# Contributing

Thanks for looking. jev-first is small on purpose; the best contributions keep it that way.

## Setup

```sh
git clone https://github.com/harrymunro/jev-first && cd jev-first
uvx ruff check . && uvx ruff format --check .
uvx --with pytest pytest -q
```

The scripts are stdlib-only. Tests run without a network or a key; anything that would call
the API is exercised through `--dry-run` or a fixture.

## Ground rules

- **The description stays under 1,024 characters.** Claude Code truncates longer ones.
  `tests/test_skill.py` checks it. If you change it, re-run `evals/measure_trigger.py`
  and put the before/after numbers in the PR.
- **Arithmetic, dates and counting live in code**, never in a question to the model.
- **No key ever touches disk, output or logs.**
- **No benchmark tables** comparing the model provider to other models in the repo. Link
  to the source instead. Your own case numbers belong in your own lab.
- **Hyphens, not em dashes**, in prose.
- Keep `SKILL.md` under 200 lines. Depth goes in `references/`.

## Adding a shape or a template

Shapes live in `references/shapes.md`. A new shape needs: the words that announce it, the
primitive to reach for, a JSON template that runs through `jev_ask.py --dry-run`, and a
sentence on when *not* to use it.

## Sharing a case

Case write-ups from your own jev-lab are welcome as examples under `examples/` if they
contain no confidential text. Keep the questions verbatim and the reuse section first.

## Pull requests

- One change per PR, with a test where a test makes sense.
- Run ruff and pytest locally; CI runs the same on Python 3.11 to 3.13.
- Update `CHANGELOG.md` under Unreleased.
