"""Tests for the jev-first skill files and scripts. No network, no key."""

from __future__ import annotations

import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "jev-first"
SCRIPTS = SKILL / "scripts"


def run(
    args: list[str], stdin: str | None = None, env: dict | None = None
) -> subprocess.CompletedProcess:
    full_env = {**os.environ}
    full_env.pop("TYPESAFE_API_KEY", None)
    full_env.update(env or {})
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


def test_jev_ask_rejects_an_empty_items_file(tmp_path: Path):
    q = tmp_path / "q.json"
    q.write_text(json.dumps({"x": {"type": "noul", "instructions": "?"}}))
    items = tmp_path / "items.jsonl"
    items.write_text("\n")
    r = run(
        [str(SCRIPTS / "jev_ask.py"), "--questions", str(q), "--items", str(items), "--dry-run"]
    )
    assert r.returncode != 0
    assert "no items" in r.stderr


def test_shapes_templates_are_runnable_questions(tmp_path: Path):
    """Every JSON template in shapes.md has to load as a questions file (CONTRIBUTING)."""
    blocks = re.findall(
        r"```json\n(.*?)```", (SKILL / "references" / "shapes.md").read_text(), re.S
    )
    assert len(blocks) >= 10
    for i, block in enumerate(blocks):
        q = tmp_path / f"q{i}.json"
        q.write_text(block)
        r = run(
            [str(SCRIPTS / "jev_ask.py"), "--questions", str(q), "--state-text", "x", "--dry-run"]
        )
        assert r.returncode == 0, f"shapes.md block {i}: {r.stderr}"


def test_jev_ask_reports_the_model_that_answered(tmp_path: Path):
    """The summary has to name the versioned id the API returned, not the alias asked for."""
    import http.server
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            out = json.dumps(
                {
                    "model": "jev-1.13.0",
                    "answers": {q: {"type": "noul", "noul": 0.9} for q in body["questions"]},
                    "usage": {"input_tokens": 312, "output_tokens": 48},
                }
            ).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        q = tmp_path / "q.json"
        q.write_text(json.dumps({"x": {"type": "noul", "instructions": "?"}}))
        r = run(
            [
                str(SCRIPTS / "jev_ask.py"),
                "--questions",
                str(q),
                "--state-text",
                "hi",
                "--timeout",
                "5",
            ],
            env={
                "TYPESAFE_API_KEY": "test-key",
                "TYPESAFE_API_BASE": f"http://127.0.0.1:{srv.server_port}",
            },
        )
    finally:
        srv.shutdown()
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["model"] == "jev-1.13.0"
    assert "model jev-1.13.0" in r.stderr, r.stderr


def test_jevlab_repairs_a_lab_missing_its_subdirectories(tmp_path: Path):
    lab = tmp_path / "lab"
    lab.mkdir()
    (lab / "LOG.md").write_text("# Trigger log\n\n| date |\n|---|\n")
    r = run(
        [
            str(SCRIPTS / "jevlab.py"),
            "new",
            "demo",
            "--project",
            "p",
            "--title",
            "Demo",
            "--shape",
            "detect",
        ],
        env={"JEV_LAB": str(lab)},
    )
    assert r.returncode == 0, r.stderr
    assert (lab / "lib" / "jev_ask.py").exists()


def test_jev_ask_retries_a_dropped_connection(tmp_path: Path):
    """A reset mid-response is transient: urllib raises it raw, and it must still be retried."""
    import socket
    import threading

    def serve(sock: socket.socket, drops: int) -> None:
        body = json.dumps(
            {
                "model": "jev-1.13.0",
                "answers": {"x": {"type": "noul", "noul": 0.9}},
                "usage": {"input_tokens": 12, "output_tokens": 4},
            }
        ).encode()
        for i in range(drops + 1):
            conn, _ = sock.accept()
            with conn:
                conn.recv(65536)
                if i < drops:  # hang up without a status line
                    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                    continue
                conn.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                    + str(len(body)).encode()
                    + b"\r\n\r\n"
                    + body
                )

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(2)
    threading.Thread(target=serve, args=(sock, 1), daemon=True).start()
    try:
        q = tmp_path / "q.json"
        q.write_text(json.dumps({"x": {"type": "noul", "instructions": "?"}}))
        r = run(
            [
                str(SCRIPTS / "jev_ask.py"),
                "--questions",
                str(q),
                "--state-text",
                "hi",
                "--timeout",
                "5",
            ],
            env={
                "TYPESAFE_API_KEY": "test-key",
                "TYPESAFE_API_BASE": f"http://127.0.0.1:{sock.getsockname()[1]}",
            },
        )
    finally:
        sock.close()
    assert r.returncode == 0, r.stderr
    assert "1 ok, 0 failed" in r.stderr, r.stderr
