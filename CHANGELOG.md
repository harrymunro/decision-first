# Changelog

All notable changes to jev-first are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- `jev_ask.py`: retry connection resets and truncated reads. urllib raises these raw
  instead of wrapping them in `URLError`, so they escaped the retry loop and were recorded
  as permanent per-item failures.
- `jev_ask.py`: the summary line now names the versioned model id the API returned
  (`jev-1.13.0`) rather than the alias that was requested (`jev-latest`), which is what the
  skill tells you to record in a case write-up.
- `jev_ask.py`: an items file with no items exits with a message instead of an IndexError
  traceback under `--dry-run`.
- `jevlab.py`: `new` no longer crashes when the lab exists but `cases/` or `lib/` does not;
  the subdirectories are ensured on every run.
- `evals/measure_trigger.py`: a run that cannot start (no `claude` on PATH) is reported as
  an error row instead of aborting the whole sweep.

### Added
- Tests for each of the above, plus a check that every JSON template in `shapes.md` loads
  as a questions file.

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
