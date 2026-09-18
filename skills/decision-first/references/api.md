# API cheatsheet (verified 2026-09-18 against the live endpoint)

## Endpoint

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

`GET https://api.typesafe.ai/v1/models` lists aliases. `jev-latest` and `jev-preview`
both resolved to `jev-1.13.0` on 18 Sept 2026. Pin `jev-1.13.0` when thresholds must be
stable; the response's `model` field reports the versioned id that answered, so log it.

## Request

```json
{
  "model": "jev-latest",
  "state": {"bead": {"title": "...", "description": "...", "notes": "..."}},
  "questions": {
    "waiting_on_person": {"type": "noul", "instructions": "Does `bead.description` say progress is waiting on a person?"},
    "stakeholder": {"type": "choice", "instructions": "If waiting on a person, who?", "criteria": {"mike": "...", "james": "...", "unspecified": "Waiting but no name given", "nobody": "Not waiting on anyone"}},
    "size": {"type": "score", "instructions": "How many independent changes does `bead.description` describe?", "criteria": ["One change", "One main change plus a small related tweak", "Several independent changes"]}
  }
}
```

- `state`: string, JSON object, or array of text. Text only. Prefer a named object.
- `questions`: map of your ids to question objects. Ids are not sent to the model.
- `instructions` and every `criteria` entry may be a string, object, or array. Field
  names inside objects (`what`, `not_for`, `examples`, `focus`) are yours; the model sees
  them.
- Choice `criteria`: map option -> description (or `null`). Up to 255 options.
- Score `criteria`: ordered array, low to high, 2-10 levels.
- Noul `criteria`: optional `{"true": ..., "false": ...}`.

## Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "waiting_on_person": {"type": "noul", "noul": 0.93},
    "stakeholder": {"type": "choice", "choice": "mike", "confidence": 0.71, "probabilities": {"mike": 0.8, "james": 0.1, "unspecified": 0.1, "nobody": 0.0}},
    "size": {"type": "score", "score": 1.3, "confidence": 0.54, "legend": {"0": "...", "1": "...", "2": "..."}, "probabilities": {"0": 0.0, "1": 0.7, "2": 0.3}}
  },
  "usage": {"input_tokens": 418, "output_tokens": 74}
}
```

- `score` is the probability-weighted mean of level numbers; normalise by
  `len(criteria) - 1` before combining. Different distributions can give the same score,
  so read `probabilities` and `confidence` alongside it.
- `confidence` (Choice and Score only) is derived from how peaked `probabilities` is.
  Noul has no separate confidence; near 0.5 means uncertain, not "medium".
- Errors: 429 with `retry-after` on rate limit, 5xx transient. Retry with backoff.

## Limits and price

| | |
|---|---|
| Context | 64k tokens per request; 32k for state plus the longest question |
| Rate limits (listed) | 250,000 tokens/s, 1,200 requests/min, adjusting dynamically |
| Price | $0.042 per million input tokens; output tokens free |
| Latency | typically 70-500 ms, ~100 ms common |
| Input | text only |

A 1,000-token state with ten questions costs about $0.00005. A backlog of 600 items at
~250 tokens each is roughly $0.01.

## Python SDK

```bash
uv add typesafe-sdk        # or: pip install typesafe-sdk   (Python >= 3.10)
```

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

with TypeSafeClient() as client:  # reads TYPESAFE_API_KEY, default jev-latest
    r = client.system_one(
        state={"bead": bead},
        questions={
            "waiting_on_person": Noul(
                instructions="Does `bead.description` say progress is waiting on a person?"
            ),
            "stakeholder": Choice(
                instructions="If waiting on a person, who?",
                criteria={
                    "mike": None,
                    "james": None,
                    "unspecified": "No name given",
                    "nobody": "Not waiting",
                },
            ),
            "size": Score(
                instructions="How many independent changes does `bead.description` describe?",
                criteria=["One", "One plus a tweak", "Several"],
            ),
        },
    )
r.nouls["waiting_on_person"].noul
(
    r.choices["stakeholder"].choice,
    r.choices["stakeholder"].confidence,
    r.choices["stakeholder"].probabilities,
)
r.scores["size"].score, r.scores["size"].probabilities  # SDK keys probabilities by int level
```

`AsyncTypeSafeClient` has the same surface. The SDK retries 429/529 with backoff by
default.

## JavaScript SDK

```bash
npm install @typesafe-ai/sdk
```

```ts
import { TypeSafeClient, choice, noul, score } from "@typesafe-ai/sdk";
const client = new TypeSafeClient();
const r = await client.systemOne({ state, questions: { urgent: noul("Does this need attention now?") } });
```

## curl

```bash
curl -sS -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" -H "Content-Type: application/json" \
  -d @request.json | python3 -m json.tool
```

## Other routes to the same model

Vercel AI Gateway, Cloudflare Workers AI (`typesafe/jev`), Netlify AI Gateway, OpenRouter
(`typesafe/jev-1.13`), LiteLLM pass-through, LangChain `langchain-typesafe`.

## Docs

Index: https://docs.typesafe.ai/llms.txt. Append `.md` to any docs page for Markdown.
Cookbooks worth reading before building a shape you have not built: parallel questions,
re-ranking, classifying RAG passages, citation check, LLM guardrails, hierarchical
classification, entity alignment, date extraction, pre-parsed value extraction, skill
suggestion, self-consistency (noul and choice), classification using confidence,
autoresearch feature discovery.
