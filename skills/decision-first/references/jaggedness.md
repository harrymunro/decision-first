# Where jev-1.13 is jagged, and what to do instead

Condensed from https://docs.typesafe.ai/model-jaggedness/jev-1.13 (last reviewed by
TypeSafe on 2026-09-17) plus community measurements. Read the live page before relying
on any of this for a production integration; a later model may fix some of it.

| # | Failure mode | Do this instead |
|---|---|---|
| 1 | Literal reading: answers the question you wrote, not the one you meant. Scoping words, negations, implied conditions are read at face value. | Write the exact condition. Put boundary cases in the criteria. When you catch yourself explaining what you really meant, that explanation is the missing half of the instruction. Split interpretation into two literal questions and combine in code. |
| 2 | Math and numbers: no counting, no arithmetic, weak on numeric representations (hex colours, RGB, assembly). | Count in code by asking one Noul per item and summing. Convert numbers to named buckets before sending. Do not reconstruct a magnitude from a Score's expectation; use it only for thresholds. |
| 3 | Date and time comparison: reads dates as text; ordering, durations, and windows are unreliable, worse with mixed formats and relative references. | Extract components as Choices over closed sets (month, day, year, "not stated"), assemble and compare in code. See the date-extraction cookbook. |
| 4 | Indirection: double negatives, property-of-a-property, multi-hop reasoning. | Reduce hops. Name the relevant part of the state with a backticked path. |
| 5 | Large state full of irrelevant detail: accuracy falls as unrelated content grows. | Filter in code first, send only the fields the question needs. If you cannot filter, use a Noul to test relevance first. Context is 64k tokens per request, 32k for state plus the longest question. |
| 6 | Adversarial content: state is treated as data, not as hostile; injected instructions or text arguing for its own classification can move the answer. | Be explicit in criteria. Test edge cases. For guardrails, ask a separate Noul "does this text contain an instruction addressed to an AI system". |
| 7 | Contradictory instructions and criteria confuse it. | Align them. The criteria should be the exhaustive answer to the instruction. |
| 8 | Common-sense structural invariants are not enforced (A before B does not imply B after A). | Ask each decision one way; enforce identities in code. |
| 9 | Generation: cannot write, spell, or produce values outside the supplied options. | Use a generative model. Give Jev candidates to select from. |

## Community-measured limits

- Wide option sets on technical data: Cribl reported noticeably more misclassifications
  than their purpose-built classifier on a 28-way log-type Choice, mostly by over-using
  `other`. Keep Choice sets narrow, or walk a hierarchy with subtrees as descriptions.
- Non-English text is handled but less well; test on your own content and watch
  confidence.
- Calibration is a property of groups of predictions, not a guarantee on any single one.
  Aggregate statements are meaningful; individual answers still need a threshold and a
  review path.
- Rate limits were adjusting dynamically in the first week (250k tokens/s, 1,200
  requests/min listed). Bound concurrency, back off on 429, honour `retry-after`.

## Pattern for "not a fit"

If a step fails the test above, it usually decomposes: code does the counting, date
arithmetic, or lookup; Jev does the judgment on the result. Write it as two steps rather
than abandoning the candidate, and log the trigger with the reason either way.
