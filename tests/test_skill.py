"""Tests for the jev-first skill files and scripts. No network, no key."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "jev-first"
SCRIPTS = SKILL / "scripts"


def run(
    args: list[str], stdin: str | None = None, env: dict | None = None
) -> subprocess.CompletedProcess:
    full_env = {**os.environ, **(env or {})}
    full_env.pop("TYPESAFE_API_KEY", None)
    return subprocess.run(
        [sys.executable, *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=full_env,
        timeout=60,
    )


def test_frontmatter_name_and_description_length():
    text = (SKILL / "SKILL.md").read_text()
    assert text.startswith("---\nname: jev-first\n")
    desc = re.search(r'^description: "(.*)"$', text, re.M).group(1)
    assert 200 < len(desc) <= 1024, len(desc)


def test_skill_body_is_short_enough():
    assert len((SKILL / "SKILL.md").read_text().splitlines()) < 200


def test_references_exist_and_are_linked():
    body = (SKILL / "SKILL.md").read_text()
    for name in ("shapes.md", "field-notes.md", "jaggedness.md", "api.md"):
        assert (SKILL / "references" / name).exists()
        assert f"references/{name}" in body


def test_scripts_compile():
    for script in SCRIPTS.glob("*.py"):
        compile(script.read_text(), str(script), "exec")


def test_jev_ask_dry_run(tmp_path: Path):
    q = tmp_path / "q.json"
    q.write_text(json.dumps({"urgent": {"type": "noul", "instructions": "Is `item.text` urgent?"}}))
    r = run(
        [
            str(SCRIPTS / "jev_ask.py"),
            "--questions",
            str(q),
            "--state-text",
            "Help now",
            "--wrap",
            "item",
            "--dry-run",
        ]
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["state"] == {"item": "Help now"}
    assert "urgent" in payload["questions"]


def test_jev_ask_refuses_without_key(tmp_path: Path):
    q = tmp_path / "q.json"
    q.write_text(json.dumps({"x": {"type": "noul", "instructions": "?"}}))
    r = run([str(SCRIPTS / "jev_ask.py"), "--questions", str(q), "--state-text", "hi"])
    assert r.returncode != 0
    assert "TYPESAFE_API_KEY" in r.stderr


def test_jev_eval_agreement(tmp_path: Path):
    results = tmp_path / "results.jsonl"
    results.write_text(
        "\n".join(
            json.dumps(
                {
                    "id": f"i{i}",
                    "answers": {
                        "yes": {"type": "noul", "noul": 0.9 if i % 2 else 0.1},
                        "kind": {
                            "type": "choice",
                            "choice": "a",
                            "confidence": 0.8,
                            "probabilities": {"a": 0.8, "b": 0.2},
                        },
                    },
                }
            )
            for i in range(4)
        )
    )
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps({f"i{i}": {"yes": bool(i % 2), "kind": "a" if i < 3 else "b"} for i in range(4)})
    )
    r = run([str(SCRIPTS / "jev_eval.py"), str(results), "--labels", str(labels)])
    assert r.returncode == 0, r.stderr
    assert "100.0%" in r.stdout  # yes
    assert "75.0%" in r.stdout  # kind


def test_jevlab_cycle(tmp_path: Path):
    env = {"JEV_LAB": str(tmp_path / "lab")}
    r = run(
        [
            str(SCRIPTS / "jevlab.py"),
            "new",
            "demo case",
            "--project",
            "p",
            "--title",
            "Demo",
            "--shape",
            "detect",
        ],
        env=env,
    )
    assert r.returncode == 0, r.stderr
    cases = list((tmp_path / "lab" / "cases").iterdir())
    assert len(cases) == 1 and cases[0].name.endswith("-demo-case")
    for name in ("README.md", "questions.json", "sample_state.json", "run.sh"):
        assert (cases[0] / name).exists()
    assert (tmp_path / "lab" / "lib" / "jev_ask.py").exists()
    r = run(
        [
            str(SCRIPTS / "jevlab.py"),
            "log",
            "--project",
            "p",
            "--shape",
            "detect",
            "--verdict",
            "declined",
            "--task",
            "t",
            "--why",
            "w",
        ],
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "| declined |" in (tmp_path / "lab" / "LOG.md").read_text()
    r = run([str(SCRIPTS / "jevlab.py"), "index"], env=env)
    assert r.returncode == 0
    assert "Demo" in (tmp_path / "lab" / "INDEX.md").read_text()


def test_prompt_hook_fires_and_stays_quiet():
    hit = run(
        [str(SCRIPTS / "prompt_hook.py")],
        stdin=json.dumps(
            {"prompt": "go through the support inbox and tag each email as refund, bug or sales"}
        ),
    )
    assert hit.returncode == 0 and "jev-first" in hit.stdout
    quiet = run(
        [str(SCRIPTS / "prompt_hook.py")],
        stdin=json.dumps({"prompt": "rename all the .jsx files to .tsx and fix the imports"}),
    )
    assert quiet.returncode == 0 and quiet.stdout == ""
    garbage = run([str(SCRIPTS / "prompt_hook.py")], stdin="not json")
    assert garbage.returncode == 0
