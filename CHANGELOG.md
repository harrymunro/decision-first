# Changelog

All notable changes to decision-first are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.1] - 2026-09-18

### Changed
- Renamed from jev-first to decision-first, and the scripts to `ask.py`, `compare.py` and
  `lab.py`, so TypeSafe's product name stays out of ours. The lab moved to
  `~/Workspace/decision-lab` (`DECISION_LAB`). Cost and latency figures removed from the
  public copies.

### Fixed
- `ask.py`: retry connection resets and truncated reads. urllib raises these raw
  instead of wrapping them in `URLError`, so they escaped the retry loop and were recorded
  as permanent per-item failures.
- `ask.py`: the summary line now names the versioned model id the API returned
  (`jev-1.13.0`) rather than the alias that was requested (`jev-latest`), which is what the
  skill tells you to record in a case write-up.
- `ask.py`: an items file with no items exits with a message instead of an IndexError
  traceback under `--dry-run`.
- `lab.py`: `new` no longer crashes when the lab exists but `cases/` or `lib/` does not;
  the subdirectories are ensured on every run.
- `evals/measure_trigger.py`: a run that cannot start (no `claude` on PATH) is reported as
  an error row instead of aborting the whole sweep.

### Added
- Tests for each of the above, plus a check that every JSON template in `shapes.md` loads
  as a questions file.

## [0.1.0] - 2026-09-18

### Added
- `skills/decision-first/SKILL.md`: the Decision-first reflex. Announce the candidate, ten-second
  test against ten decision shapes, question-design rules, try / measure / decide /
  document / report.
- References: `shapes.md` (trigger vocabulary and per-shape templates), `field-notes.md`
  (what shipped in Jev's first 72 hours and what did not work), `jaggedness.md`,
  `api.md`.
- Scripts: `ask.py` (stdlib runner with batch, retries, cost and latency),
  `compare.py` (agreement against labels), `lab.py` (trigger log, case scaffolding,
  index), `prompt_hook.py` (optional Claude Code prompt nudge).
- `evals/`: 20 trigger prompts and `measure_trigger.py`, which counts invocations of the
  installed skill through `claude -p`.
- Claude Code plugin manifest so `claude plugin marketplace add harrymunro/decision-first` works.
