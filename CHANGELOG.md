# Changelog

All notable changes to jev-first are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-09-18

### Added
- `skills/jev-first/SKILL.md`: the Jev-first reflex. Announce the candidate, ten-second
  test against ten decision shapes, question-design rules, try / measure / decide /
  document / report.
- References: `shapes.md` (trigger vocabulary and per-shape templates), `field-notes.md`
  (what shipped in Jev's first 72 hours and what did not work), `jaggedness.md`,
  `api.md`.
- Scripts: `jev_ask.py` (stdlib runner with batch, retries, cost and latency),
  `jev_eval.py` (agreement against labels), `jevlab.py` (trigger log, case scaffolding,
  index), `prompt_hook.py` (optional Claude Code prompt nudge).
- `evals/`: 20 trigger prompts and `measure_trigger.py`, which counts invocations of the
  installed skill through `claude -p`.
- Claude Code plugin manifest so `claude plugin marketplace add harrymunro/jev-first` works.
