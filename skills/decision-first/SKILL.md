---
name: decision-first
description: "Decision-first reflex: spot any step where code or an agent must make a bounded judgment about text or records, and try TypeSafe's Jev (System One model: typed Choice/Score/Noul answers with calibrated probabilities, fast, cheap) before an LLM prompt, a regex heuristic, or a manual pass. Use whenever work involves classifying, tagging, labelling, triaging, prioritising, sizing, scoring, rating, ranking, routing, filtering, deduplicating, matching, verifying, flagging, moderating, reviewing, or detecting anything about tickets, issues, beads, emails, documents, logs, records, tool calls, or PRs; whenever a loop over items needs a judgment per item; whenever an LLM is asked for JSON, a label, a yes/no, or to act as a judge; whenever an if/else depends on meaning; whenever the user says go through, sort into, which of these, is this a, should this, how bad, flag the, or needs a human; and whenever Jev, TypeSafe, or System One is mentioned. Every trigger and use is logged in ~/Workspace/decision-lab."
---

# Decision first

Jev is named after Jevons' paradox: make a resource cheap and people use far more of it.
A typed decision from Jev is cheap and fast enough that the right instinct is to put one
everywhere a program needs to *judge* rather than *compute*. The person you work for wants to learn where that instinct pays off, fast,
across all of their projects. That only works if two things happen every time: the
candidate step gets spotted while the work is happening, and the attempt gets written down
in a form the next project can pick up and run. This skill exists to make both automatic.

Paths below are relative to this skill's directory. The lab (where logs and case write-ups
go) defaults to `~/Workspace/decision-lab`; set `DECISION_LAB` to put it elsewhere.

## Say it when you see it

The moment you notice a judgment step, say so to the user in one line before doing
anything else, for example:

> Jev candidate: tagging each ticket as waiting-on-a-person or not. Shape: detection (Noul)
> plus a Choice over the people it could be waiting on.

Do this even when you go on to decline it. Naming the candidate is what builds the habit,
and the decline reasons are as valuable a record as the adoptions.

## The ten-second test

Look at each step in the task and ask: *does code need to decide something about text
or a record here, where the answer is not a lookup, not arithmetic, and not a regex?*
If yes, it is a Jev candidate. The shapes that fit, with the primitive to reach for:

| Shape | Reach for it when | Primitive |
|---|---|---|
| Classify | one known category should win | Choice, with an `other` option |
| Detect | you need the probability that a property is present | Noul |
| Score | the answer sits on an ordered rubric you can describe in situations | Score, 2-10 levels |
| Route | a category picks the next code path, model, handler, or person | Choice + confidence gate |
| Rank / rerank | items need ordering by relevance or quality | one Score or Noul per item, sort in code |
| Filter | keep or drop each item against a natural-language criterion | Noul per item |
| Verify | an artifact must be checked for named failure modes | one Noul per failure mode |
| Match / dedupe | do two records describe the same thing | Score with levels merge / unsure / distinct |
| Select / extract | pick the right span or value from candidates code found | Choice over candidates |
| Gate | is this action safe, done, on-task, or does it need a human | Noul + threshold in code |

Smells that mean you are already looking at one:

- A loop over items with an LLM call, a prompt template, or "ask the model" inside it.
- A prompt that asks for JSON, a label, a number, true/false, or "respond only with".
- An LLM-as-judge, grader, reviewer, or safety check.
- `if "refund" in text`, keyword lists, hand-tuned regexes that keep growing.
- Words in the request: label, tag, categorise, triage, prioritise, size, score, rank,
  route, flag, dedupe, match, verify, moderate, review, screen, "go through all",
  "sort these into", "which of these", "is this a", "should this go to".
- A backlog, inbox, corpus, export, or dataset that someone wants a view over.
- A manual pass the user is doing themselves because it was "not worth automating".

The full trigger vocabulary and per-shape question templates are in
`references/shapes.md`. Read it when designing questions for a shape you have not done
before.

## Not a fit, still log it

Jev 1.13 is literal, cannot count or do arithmetic, does not compare dates, weakens on
multi-hop indirection, degrades on large states full of irrelevant detail, and cannot
generate anything. It also does measurably worse than purpose-built classifiers on wide,
technical option sets (one team reported this on a 28-way log-type Choice). Send those
parts to code or to a generative model, keep the judgment part for Jev, and log the
trigger either way with the reason. Details and workarounds are in
`references/jaggedness.md`.

## Procedure

Work through these in order. Each one is short.

1. **Announce** the candidate in one line (above).
2. **Design** the questions. Rules that matter most, all learned the hard way by the
   first week of builders:
   - One judgment per question. Split "rate this ticket" into severity, frustration,
     and report quality, then weight them in code.
   - Ask every question you might need in the *same* request, including speculative
     ones. They run in parallel and extra questions are nearly free.
   - Describe situations, not degrees. "Broken but a workaround exists" works;
     "moderately severe" does not. Score levels are judged one at a time, so the
     numbers and neighbours mean nothing to the model.
   - Always include a no-match option (`other`, `none`, `unspecified`) and, when the
     boundary is subtle, give options `what` / `not_for` / `examples` fields.
   - Put the state in a named JSON object and point questions at fields with backticked
     paths like `` `ticket.description` ``. Send only the fields the question needs.
   - Give Jev candidates to pick from; never ask it to invent. Build the option set in
     code from the DOM, the retriever, the tool list, the label set, the legal moves.
   - Code owns control flow, thresholds, arithmetic, and side effects. Jev supplies the
     judgment and a probability. Confidence below roughly 0.5 means "ask, do not act".
3. **Try it** on 5-20 real items before writing any integration. Use the runner:

   ```bash
   python3 scripts/ask.py --questions questions.json --items items.jsonl --wrap item --out results.jsonl
   ```

   It is stdlib-only, reads `TYPESAFE_API_KEY`, runs items concurrently, retries on 429,
   and prints a per-question table plus tokens, cost, and latency. `--dry-run` shows the
   request without sending it. Read `references/api.md` for the request shape if you are
   writing the call yourself.
4. **Measure**. If any labels exist (an existing tag, a closed-reason, a human's earlier
   pass), run `python3 scripts/compare.py results.jsonl --labels labels.json` and report
   agreement per question. With no labels, eyeball the low-confidence tail: it is where
   the question wording is wrong or the state is missing something.
5. **Decide**: adopt, decline, or park. Say which and why in one sentence.
6. **Document**. This is not optional, and it is the whole point of the exercise:

   ```bash
   # every trigger, adopted or not
   python3 scripts/lab.py log --project <repo> --shape <shape> \
     --verdict adopted|declined|parked --task "<one line>" --why "<one line>"

   # every adoption or real experiment: scaffolds a reusable case directory
   python3 scripts/lab.py new <slug> --project <repo> --title "<title>" \
     --shape <shape> --questions questions.json
   ```

   `new` creates `<lab>/cases/<date>-<slug>/` with a README from the template, the
   questions file, a sample state, `run.sh`, and vendored copies of the runner so the
   case runs standalone. Fill the README sections in: problem, why Jev, state shape, the
   questions verbatim, how code composes the answers, results with numbers, verdict, and
   *how to re-adapt this for another project*. That last section is what the next agent
   reads first.
7. **Report** to the user: the verdict, the numbers, and the case path.

## Documenting well

The lab is a corpus for learning, so write the README for a reader who has a different
project and ten minutes. Lead with the reuse recipe. Keep the questions verbatim as JSON,
because the option wording *is* the work. Record the versioned model id the API returned,
the item count, agreement against any labels, tokens, cost, and p50 latency. If you tried
two wordings, keep both and say which won and why. If Jev lost to something else, say what
beat it. Put every threshold you chose in one place with the reason.

`python3 scripts/lab.py index` rebuilds `<lab>/INDEX.md` from the case READMEs, and
`<lab>/LOG.md` holds the one-line trigger log. Commit the lab after each case.

## References

- `references/shapes.md`: trigger vocabulary, ten shapes, question templates per shape.
- `references/field-notes.md`: what people shipped in the first 72 hours, and what did
  not work. Read for ideas and for calibration on what to expect.
- `references/jaggedness.md`: the documented failure modes of jev-1.13 and workarounds.
- `references/api.md`: request and response shapes, limits, pricing, SDK snippet, curl.
- Live docs are the source of truth: https://docs.typesafe.ai/llms.txt lists every page;
  append `.md` to a docs URL for Markdown. TypeSafe's own agent skill
  (`claude plugin install typesafe@typesafe-ai`) is worth loading for integration code.
