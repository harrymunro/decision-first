#!/usr/bin/env python3
"""Keep the decision-lab: the log of every Jev trigger and the reusable case write-ups.

Lab root: $DECISION_LAB, else ~/Workspace/decision-lab. Created (with git init) on first use.

  lab.py log  --project fls --shape detect --verdict adopted \
                 --task "tag beads waiting on a person" \
                 --why "existing 'human' label gives 73 test cases" [--case slug]

  lab.py new  blocked-by-human --project fls --title "Beads blocked by a human" \
                 --shape detect [--questions q.json] [--sample state.json]

  lab.py index          # rebuild INDEX.md from case READMEs
  lab.py path           # print the lab root

`log` appends one row to LOG.md. `new` scaffolds cases/<date>-<slug>/ with README.md,
questions.json, sample_state.json, run.sh, and vendored copies of ask.py and
compare.py under lib/ so every case runs on its own. Both print what they did.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / "assets" / "case-README.md"
SHAPES = [
    "classify",
    "detect",
    "score",
    "route",
    "rank",
    "filter",
    "verify",
    "match",
    "select",
    "gate",
    "other",
]
VERDICTS = ["adopted", "declined", "parked", "experiment"]


def lab_root() -> Path:
    return Path(
        os.environ.get("DECISION_LAB", Path.home() / "Workspace" / "decision-lab")
    ).expanduser()


def ensure_lab(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cases").mkdir(exist_ok=True)
    (root / "lib").mkdir(exist_ok=True)
    if (root / "LOG.md").exists():
        return
    (root / "README.md").write_text(
        "# decision-lab\n\n"
        "Every time an agent spots a step that could be a Jev (TypeSafe System One)\n"
        "judgment, it logs the trigger in `LOG.md`. Every real attempt gets a case directory\n"
        "under `cases/` with the questions verbatim, a runnable `run.sh`, results, and a reuse\n"
        "recipe. `INDEX.md` is the table of cases. Maintained by the `decision-first` skill.\n\n"
        "Run any case:\n\n"
        "```bash\n"
        "export TYPESAFE_API_KEY=...\n"
        "cd cases/<case> && ./run.sh\n"
        "```\n"
    )
    (root / "LOG.md").write_text(
        "# Trigger log\n\n"
        "One row per time the decision-first reflex fired, adopted or not.\n\n"
        "| date | project | shape | verdict | task | why | case |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    (root / "INDEX.md").write_text("# Cases\n\n(no cases yet; run `lab.py index`)\n")
    (root / ".gitignore").write_text("results*.jsonl\n*.tmp\n__pycache__/\n.venv/\n")
    if shutil.which("git") and not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=False)
    print(f"created lab at {root}")


def vendor_lib(root: Path) -> None:
    for name in ("ask.py", "compare.py"):
        src, dst = HERE / name, root / "lib" / name
        if src.exists() and (not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime):
            shutil.copy2(src, dst)
            dst.chmod(0o755)


def cell(s: str) -> str:
    return " ".join(str(s).split()).replace("|", "\\|")


def cmd_log(args) -> None:
    root = lab_root()
    ensure_lab(root)
    today = dt.date.today().isoformat()
    cells = [
        today,
        cell(args.project),
        args.shape,
        args.verdict,
        cell(args.task),
        cell(args.why),
        cell(args.case or ""),
    ]
    row = "| " + " | ".join(cells) + " |\n"
    with open(root / "LOG.md", "a", encoding="utf-8") as f:
        f.write(row)
    print(f"logged to {root / 'LOG.md'}:\n{row.strip()}")


def cmd_new(args) -> None:
    root = lab_root()
    ensure_lab(root)
    vendor_lib(root)
    today = dt.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", args.slug.lower()).strip("-")
    case = root / "cases" / f"{today}-{slug}"
    if case.exists():
        sys.exit(f"{case} already exists")
    case.mkdir(parents=True)

    if args.questions:
        shutil.copy(args.questions, case / "questions.json")
    else:
        (case / "questions.json").write_text(
            json.dumps(
                {
                    "example_noul": {"type": "noul", "instructions": "Does `item.text` ...?"},
                    "example_choice": {
                        "type": "choice",
                        "instructions": "Which ... best describes `item.text`?",
                        "criteria": {"a": "...", "b": "...", "other": "None of the above"},
                    },
                },
                indent=2,
            )
            + "\n"
        )
    if args.sample:
        shutil.copy(args.sample, case / "sample_state.json")
    else:
        (case / "sample_state.json").write_text(
            json.dumps({"item": {"text": "replace me"}}, indent=2) + "\n"
        )

    wrap = f"--wrap {args.wrap} " if args.wrap else ""
    (case / "run.sh").write_text(
        "#!/usr/bin/env bash\n"
        "# Re-run this case. Needs TYPESAFE_API_KEY. Edit questions.json or sample_state.json.\n"
        "set -euo pipefail\n"
        'cd "$(dirname "$0")"\n'
        "if [ -f items.jsonl ]; then\n"
        "  python3 ../../lib/ask.py --questions questions.json --items items.jsonl "
        f'{wrap}--out results.jsonl "$@"\n'
        "else\n"
        '  python3 ../../lib/ask.py --questions questions.json --state sample_state.json "$@"\n'
        "fi\n"
        "# with labels: python3 ../../lib/compare.py results.jsonl --labels labels.json\n"
    )
    (case / "run.sh").chmod(0o755)

    template = TEMPLATE.read_text() if TEMPLATE.exists() else "---\ntitle: {title}\n---\n"
    readme = (
        template.replace("{title}", args.title)
        .replace("{date}", today)
        .replace("{project}", args.project)
        .replace("{shape}", args.shape)
        .replace("{slug}", slug)
    )
    (case / "README.md").write_text(readme)

    cmd_index(None)
    print(f"created {case}")
    print("  edit README.md, questions.json, sample_state.json (or add items.jsonl), then ./run.sh")
    print(f"  don't forget: lab.py log --case {case.name} ...")


FRONT = re.compile(r"^---\n(.*?)\n---", re.S)


def front_matter(text: str) -> dict:
    m = FRONT.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def cmd_index(_args) -> None:
    root = lab_root()
    ensure_lab(root)
    rows = []
    for case in sorted((root / "cases").glob("*/README.md"), reverse=True):
        fm = front_matter(case.read_text())
        link = f"[{cell(fm.get('title', case.parent.name))}](cases/{case.parent.name}/README.md)"
        rows.append(
            f"| {fm.get('date', '')} | {link} | {cell(fm.get('project', ''))} "
            f"| {fm.get('shape', '')} | {fm.get('verdict', '')} | {cell(fm.get('reuse', ''))} |"
        )
    body = (
        "# Cases\n\nOne row per documented Jev attempt. "
        "Each links to a README with the questions verbatim and a `run.sh`.\n\n"
    )
    body += (
        "| date | case | project | shape | verdict | reuse |\n|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n"
    )
    (root / "INDEX.md").write_text(body)
    if _args is not None:
        print(f"indexed {len(rows)} case(s) into {root / 'INDEX.md'}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("log", help="append a trigger row to LOG.md")
    p.add_argument("--project", required=True)
    p.add_argument("--shape", required=True, choices=SHAPES)
    p.add_argument("--verdict", required=True, choices=VERDICTS)
    p.add_argument("--task", required=True, help="one line: what the judgment step was")
    p.add_argument("--why", required=True, help="one line: why adopted / declined / parked")
    p.add_argument("--case", help="case directory name if one was created")
    p.set_defaults(fn=cmd_log)

    p = sub.add_parser("new", help="scaffold a case directory")
    p.add_argument("slug")
    p.add_argument("--project", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--shape", required=True, choices=SHAPES)
    p.add_argument("--questions", help="questions.json to copy in")
    p.add_argument("--sample", help="sample_state.json to copy in")
    p.add_argument("--wrap", help="wrap key for items.jsonl runs, e.g. bead")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("index", help="rebuild INDEX.md")
    p.set_defaults(fn=cmd_index)

    p = sub.add_parser("path", help="print the lab root")
    p.set_defaults(fn=lambda a: print(lab_root()))

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
