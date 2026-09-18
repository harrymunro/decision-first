<div align="center">

# decision-first

**Teach your coding agent to try Jev before it writes another regex, and to write down what happened.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/harrymunro/decision-first/actions/workflows/ci.yml/badge.svg)](https://github.com/harrymunro/decision-first/actions/workflows/ci.yml)
[![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-black.svg)](https://agentskills.io)

</div>

---

decision-first is an agent skill. Once installed, your coding agent notices when a step of the
work is really a bounded judgment (classify, tag, triage, size, rank, route, filter, verify,
match, gate) and tries [TypeSafe's Jev](https://docs.typesafe.ai/introduction), a System One
model that returns typed answers with calibrated probabilities, fast and cheap, before
reaching for an LLM prompt, a keyword heuristic, or a manual pass.
Then it documents the attempt, adopted or not, in a lab directory the next project can reuse.

## Install it: paste this into your agent

Works in Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Pi, Hermes, or any agent that can
run shell commands and load skills.

```text
Install the decision-first skill from https://github.com/harrymunro/decision-first and use it from now on.

1. Get the skill: git clone --depth 1 https://github.com/harrymunro/decision-first /tmp/decision-first
   then copy /tmp/decision-first/skills/decision-first into the directory you load skills from, keeping
   SKILL.md, references/, scripts/ and assets/ together. For Claude Code that is
   ~/.claude/skills/decision-first (every project) or .claude/skills/decision-first (this repo only).
   Other agents: their own skills directory. Make scripts/*.py executable.
2. Check python3 is available and TYPESAFE_API_KEY is set. If it is not, tell me how to get a
   key from https://console.typesafe.ai. Never ask me to paste it into the chat and never write
   it to a file.
3. Read the skill, then tell me in one short paragraph what you will now do differently and
   where the log and case write-ups will go (the decision-lab: ~/Workspace/decision-lab by default, or
   the directory in $DECISION_LAB).
```

Other routes: `npx skills add harrymunro/decision-first --skill decision-first` (the
[skills.sh](https://skills.sh) installer), or in Claude Code
`claude plugin marketplace add harrymunro/decision-first && claude plugin install decision-first@decision-first`.

## Why

Jev is named after Jevons' paradox: make a resource cheap and people consume far more of it.
Decisions from Jev are cheap enough to put everywhere code needs to judge rather than compute.
The limiting factor stops being cost and becomes noticing. Agents are bad at noticing; they
reach for `if "refund" in text.lower()` or a prompt-and-parse loop because that is what the
training data does. This skill is the nudge, the procedure, and the paper trail.

### 🧑‍💻 For humans

- **It announces the candidate** in one line before doing anything, so you can say no.
- **It tries before it integrates**: 5-20 real items through a stdlib runner, with tokens, cost
  and p50 latency printed, and agreement against any labels you already have.
- **It documents every attempt.** Declines get one line in a log. Adoptions and experiments
  get a case directory with the questions verbatim, a `run.sh`, results, and a "how to reuse
  this" section written first. Read the log in three months and see where it paid off.
- **It knows what Jev cannot do** (count, do arithmetic, compare dates, generate, wide
  technical option sets) and sends those parts to code.

### 🤖 For agents

The skill body is the procedure: announce, ten-second test against ten decision shapes, design
questions by the rules the first week of builders learned, try, measure, decide, document,
report. Four reference files cover shapes and question templates, field notes from launch
week, the documented failure modes of jev-1.13, and an API cheatsheet. Three scripts do the
work:

| script | does |
|---|---|
| `scripts/ask.py` | run a questions file over one state or many items; concurrency, retries, cost and latency; `--dry-run` |
| `scripts/compare.py` | agreement per question against a labels file, with confusion tables and the confident misses |
| `scripts/lab.py` | `log` a trigger, `new` a case directory, `index` the lab |

`scripts/prompt_hook.py` is an optional `UserPromptSubmit` hook for Claude Code that nudges the
agent when a prompt contains trigger vocabulary. It never blocks and always exits 0.

## What's inside

```
skills/decision-first/
├── SKILL.md              the reflex and the procedure
├── references/           shapes.md, field-notes.md, jaggedness.md, api.md
├── scripts/              ask.py, compare.py, lab.py, prompt_hook.py
└── assets/case-README.md the case write-up template
evals/                    20 trigger prompts and a script that measures the installed skill
```

## Running the scripts by hand

`questions.json` is yours to write: copy a template out of
`skills/decision-first/references/shapes.md` for the shape you need and edit the wording.

```sh
export TYPESAFE_API_KEY=...
cd skills/decision-first
python3 scripts/ask.py --questions questions.json --state-text "My card was charged twice"
python3 scripts/ask.py --questions questions.json --items tickets.jsonl --wrap ticket --out results.jsonl
python3 scripts/compare.py results.jsonl --labels labels.json
python3 scripts/lab.py new refund-detector --project shop --title "Refund requests" --shape detect --questions questions.json
```

No dependencies beyond Python 3.11+. The runner falls back to the system certificate bundle
on Python builds that ship without one.

## Privacy

Whatever you put in `state` is sent to TypeSafe's API with your key. Do not send secrets, and
think before sending confidential text. See TypeSafe's [data handling](https://docs.typesafe.ai/models#data-handling).

## Development

```sh
git clone https://github.com/harrymunro/decision-first && cd decision-first
uvx ruff check . && uvx ruff format --check .
uvx --with pytest pytest -q
```

Tests run without a network or a key. To measure how often the skill triggers in Claude Code,
see `evals/README.md`.

## License

MIT. decision-first is an independent project and is not affiliated with TypeSafe AI.
