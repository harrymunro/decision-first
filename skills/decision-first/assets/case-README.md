---
title: {title}
date: {date}
project: {project}
shape: {shape}
verdict: experiment
model:
reuse: one line on how to re-adapt this for another project
---

# {title}

## How to reuse this

Write this first, for a reader with a different project and ten minutes. What do they
change (the state fields, the option names, the thresholds) and what do they keep?

```bash
cd cases/{date}-{slug} && ./run.sh
```

## Problem

What judgment did code or a person need to make, over what items, and what was being
used before (LLM prompt, regex, manual pass, nothing)?

## Why Jev

Which shape (classify / detect / score / route / rank / filter / verify / match / select /
gate) and why it fit. If a part of the task was not a fit, say which part and what handled
it instead.

## State

The JSON shape sent per item, with an example. Say what was deliberately left out.

## Questions

Verbatim, from `questions.json`. The option and level wording is the work; keep every
variant you tried and say which won.

```json
```

## Composition in code

How the answers are combined: thresholds, weights, confidence gates, the no-match path.
Every constant in one place with the reason.

## Results

| | |
|---|---|
| items | |
| model returned | |
| agreement vs labels | (or "no labels; eyeballed the low-confidence tail") |
| input tokens / cost | |
| p50 latency | |

What the low-confidence tail looked like and what it taught about the wording.

## Verdict

adopted / declined / parked, and the one-sentence reason. If something else beat Jev,
say what and by how much.

## Sources

Docs pages, cookbooks, or community posts that shaped the design.
