# Trigger evals

`trigger-eval.json` holds 20 realistic prompts: 10 that should make an agent load the skill
and 10 near-miss negatives (sorting by a field, counting, refactoring, prose).

`measure_trigger.py` runs each prompt through `claude -p` with the skill installed and counts
invocations of `decision-first` (a `Skill` tool call naming it, or a `Read` of its SKILL.md).

```sh
python3 evals/measure_trigger.py --model claude-fable-5-1 --workers 5 --out results.json
```

Each run is a real Claude Code session and costs real tokens; `--only 0,3` limits it. Runs
end after `--max-turns` (default 3) or on a permission prompt, so non-zero exit codes are
expected and are not failures.

Measured on 2026-09-18 with the 0.1.0 description: 9 of 10 should-trigger prompts invoked
the skill, 0 of 10 negatives did.

Do not use the skill-creator `run_eval` harness for this skill: it scores a temporary
command name that Claude ignores in favour of the installed skill, so it reads 0/20.
