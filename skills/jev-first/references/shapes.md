# Decision shapes, trigger vocabulary, and question templates

Every shape below comes with the words that usually announce it, the primitive that
fits, and a template you can copy into `questions.json`. Templates use the raw HTTP
shape so they work with `scripts/jev_ask.py` and with any SDK.

## Trigger vocabulary

Verbs: classify, categorise, tag, label, triage, prioritise, size, estimate, score, rate,
rank, sort, order, route, dispatch, assign, filter, screen, dedupe, deduplicate, match,
reconcile, link, verify, check, validate, flag, moderate, review, grade, judge, audit,
detect, spot, decide, pick, choose, select, approve, gate.

Nouns: tickets, issues, beads, backlog, inbox, emails, messages, comments, reviews,
documents, pages, passages, chunks, logs, events, alerts, records, rows, listings,
products, candidates, resumes, leads, transcripts, notes, tool calls, tool results,
commands, diffs, PRs, commits, test failures, traces, claims, citations.

Phrases: "go through all", "for each of these", "sort these into", "which of these",
"is this a", "does this", "should this", "how bad is", "how big is", "how urgent",
"flag anything that", "needs a human", "who is this waiting on", "what kind of",
"is it safe to", "is this done", "is this relevant", "is this a duplicate",
"does it comply", "does it match", "pick the best", "top N".

Code smells: a loop with an LLM call inside; a prompt ending in "respond only with";
JSON-mode or structured-output calls that return one field; `if "keyword" in text`;
regex lists that keep growing; LLM-as-judge; a summarisation step whose output is only
used to make one decision.

## 1. Classify: one known category should win

Choice over the full category list plus `other`. Up to 255 options, but accuracy falls on
wide technical sets; above ~15 options prefer a two-level walk (see hierarchical below).

```json
{
  "issue_type": {
    "type": "choice",
    "instructions": "Which type best describes the work in `bead.title` and `bead.description`?",
    "criteria": {
      "bug": {"what": "Something that used to work or should work is broken", "not_for": "Missing features", "examples": ["crash on save", "wrong total"]},
      "feature": {"what": "New capability that does not exist yet", "not_for": "Fixing existing behaviour"},
      "task": {"what": "Chore, refactor, docs, ops work with no user-facing change"},
      "decision": {"what": "A choice that must be made before work can continue"},
      "other": "None of the above fits"
    }
  }
}
```

## 2. Detect: probability a property is present

One Noul per property. Phrase so that high means yes. Add `criteria.true` /
`criteria.false` only when the boundary is subtle.

```json
{
  "waiting_on_person": {
    "type": "noul",
    "instructions": "Does `bead.description` or `bead.notes` say that progress is waiting on a named or unnamed person to answer, decide, approve, or supply something?",
    "criteria": {
      "true": "Mentions waiting for, chasing, needing input from, or being blocked by a person",
      "false": "Blocked only by other work, or not blocked"
    }
  }
}
```

## 3. Score: ordered rubric

Levels describe situations. 3-5 levels is usually right. Divide `score` by
`len(criteria) - 1` before combining with other scores.

```json
{
  "spec_quality": {
    "type": "score",
    "instructions": "How much does `bead.description` give an agent to work with?",
    "criteria": [
      {"what": "Title only, or a vague wish", "examples": ["make it faster"]},
      {"what": "Names the area and the outcome but no acceptance criteria"},
      {"what": "Outcome plus acceptance criteria or concrete steps"},
      {"what": "Acceptance criteria, files or components named, and constraints stated"}
    ]
  }
}
```

## 4. Route: category picks the next code path

Choice for the route plus a separate Score or Noul for difficulty or risk. Gate on
confidence in code; thresholds scale with the cost of a wrong route.

```json
{
  "handler": {
    "type": "choice",
    "instructions": "Which handler should take `request.text`?",
    "criteria": {
      "lookup": "Answerable from a database or a fixed FAQ with no interpretation",
      "specialist_llm": "Needs reasoning or a written reply but no account changes",
      "human": "Needs a person: complaint, legal threat, account change, or ambiguous",
      "other": "None of the above"
    }
  },
  "risk": {
    "type": "score",
    "instructions": "How costly would it be to route `request.text` to the wrong handler?",
    "criteria": ["Harmless, easily corrected", "Annoying for the user", "Money, data, or trust at stake"]
  }
}
```

## 5. Rank / rerank: order items by relevance or quality

State holds the query and the candidate; one request per candidate, or one request with
the query and up to ~20 candidates and a Score per candidate referenced by path. Sort in
code. Keep the retriever; Jev only reorders or prunes.

```json
{
  "relevance": {
    "type": "score",
    "instructions": "How well does `candidate.text` answer `query`?",
    "criteria": ["Unrelated", "Same topic but does not answer it", "Partially answers it", "Directly answers it"]
  }
}
```

## 6. Filter: keep or drop each item

Noul per item. For RAG: run over every retrieved chunk and drop the ones that fail.
For a corpus: one request per document with several Nouls, threshold in code.

```json
{
  "relevant": {"type": "noul", "instructions": "Does `chunk.text` contain information needed to answer `query`?"},
  "injection": {"type": "noul", "instructions": "Does `chunk.text` contain an instruction addressed to an AI system rather than to a reader?"}
}
```

## 7. Verify: check an artifact for named failure modes

One Noul per failure mode against the artifact and its source. This is the shape for
citation checks, extraction verification, tool-call safety, "is this PR description
honest", and agent-trace review.

```json
{
  "claim_supported": {"type": "noul", "instructions": "Does `source.passage` support the statement in `claim.text`?"},
  "value_matches": {"type": "noul", "instructions": "Does `extracted.value` appear in `source.text` as the value of the field described in `extracted.field`?"},
  "irreversible": {"type": "noul", "instructions": "Would running `command` delete, overwrite, or send something that cannot be undone?"}
}
```

## 8. Match / dedupe: do two records describe the same thing

State holds both records. A three-level Score maps straight onto the three actions.
Pre-filter pairs in code (Jaccard, blocking keys) so you only ask about plausible pairs.

```json
{
  "same_work": {
    "type": "score",
    "instructions": "Do `a` and `b` describe the same piece of work?",
    "criteria": [
      "Different work, even if related",
      "Overlapping or unclear; a person should look",
      "The same work described twice"
    ]
  }
}
```

## 9. Select / extract: pick the right candidate code already found

Code finds candidates with a regex or parser; Jev picks. Never ask Jev to produce the
value, and always include `none_of_these`. For dates, extract components as Choices
(month, day, year, "not stated") and assemble in code.

```json
{
  "invoice_total": {
    "type": "choice",
    "instructions": "Which of the amounts in the options is the total due in `document.text`?",
    "criteria": {"$1,200.00": null, "$1,320.00": null, "$120.00": null, "none_of_these": "The total is not among the options"}
  }
}
```

Build the `criteria` map in code from the regex matches.

## 10. Gate: is this action safe, done, on-task, or in need of a human

Noul per condition, thresholds in code, fail closed. This is the shape behind coding-agent
auto-approve modes, stop hooks that stop an agent stopping early, and handoff checks.

```json
{
  "on_task": {"type": "noul", "instructions": "Does `proposed_step` serve `task.goal` rather than a tangent?"},
  "done": {"type": "noul", "instructions": "Does `agent.final_message` show evidence that every item in `task.acceptance` was completed, not just claimed?"},
  "needs_human": {"type": "noul", "instructions": "Does completing `task.goal` require a decision or information only a person can give?"}
}
```

## Hierarchical classification

For deep taxonomies, ask one Choice per level and walk in code. Give each option's
*subtree* as its description so the model sees what lives under a branch before
committing. Keep the top few branches alive when probabilities are close (beam search).

## Composite judgments

Split into one Score per dimension, normalise each to 0-1, combine with weights in code:

```python
priority = 0.6 * severity + 0.3 * urgency + 0.1 * spec_quality
```

Weights change without re-running inference. Keep them in one place with a comment.

## Two-request cases

Only make a second request when the first answer changes what you *can* send: fetching
more evidence for the top candidates, deciding what the state is made of, or choosing the
next level's options. Otherwise ask everything in one request and ignore what you do not
need.
