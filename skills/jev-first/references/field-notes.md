# Field notes: what people built with Jev in the first 72 hours

Jev launched in early access on 15 September 2026. These notes were gathered on
18 September from X, GitHub, Hacker News, Reddit, YouTube, and vendor blogs. They are here
for two reasons: to seed ideas when you are looking at a task, and to calibrate
expectations, because the community write-ups are more measured than the launch banner.
Sources are named so you can go and read the numbers yourself; this file deliberately does
not reproduce speed or accuracy comparisons against other models.

## The one-line framing that stuck

"AI executes, code decides." LLMs generate answers; Jev makes decisions. Think AI
multiple choice, not AI essay writing. Keep the big model for hard thinking and writing,
use Jev for the rapid-fire judgments in between.

## Shipped workflows, ranked by how much they were copied

1. **Browser agent where Jev picks the next click** (Browser Use, repo
   `browser-use/jev-ultrafast`). DOM as state, candidate elements as Choice options, a
   small LLM wakes only to type. Pattern: new action space every step, Jev chooses among
   candidates, generation only as a fallback. Browserbase reported the same approach.
2. **Context compaction by scoring tool calls** (`fast-jev-compaction` Claude Code plugin,
   `save-token-jev`, `winnow`). Instead of summarising at the context ceiling, score every
   tool result for relevance and drop the dead weight.
3. **Safety reviewer for agent commands** (Vercel `fx` auto mode, in production; LangChain
   `AutoModeMiddleware`; community: `pi-jev-auto-mode`, `jev-guard`, `jev-shield`,
   `omp-jevens-classifier`, `typesafe-migration-guard`). "Should this command run" as a
   Noul with a threshold, failing closed.
4. **Model routing as middleware** (LangChain `ModelRouterMiddleware`; `jev-router`,
   `jcm-router`, `jev-codex-router`, `frost`, `ailerix`, `pi-jev-router`). Jev picks which
   model and how much reasoning each turn gets; probabilities kept in state for audit. The
   most-cited job in the corpus.
5. **RAG precision filter.** Keep the retriever, run one Noul over every chunk, drop the
   failures. Free output tokens make a per-chunk verdict affordable at retrieval time.
6. **Real-time loops**: Doom at several decisions per second; Minecraft with Jev on
   reactions and a frontier model planning; a keystroke launcher that reranks files on
   every keystroke; chess by Choice over legal moves with zero illegal moves.
7. **Email and ticket triage at batch scale.** TypeSafe's own quickstart is already a
   triage pipeline; several people ran thousands of exported emails through it.
8. **Map-reduce over documents.** Mike Taylor (Every) ran 21 questions over 37 articles in
   one request; the whole experiment series cost under a cent.
9. **Local clones of the interface** (Reflex on WebGPU, `open-jev`, `mini-jev`). An offline
   escape hatch for data that cannot leave the machine.

## Coding-agent tooling

The largest single cluster on GitHub is Jev inside coding-agent harnesses:

- Tool-call gates and auto-approve: `pi-jev`, `pi-jev-auto-mode`, `pi-warden` (judges
  irreversible and off-task calls, detects stuck loops, checks unverified "done" claims),
  `omp-typesafe` adversarial reviewer.
- Stop hooks: `limpet` (stops the agent stopping early against plain-language rules),
  `pi-agent-foreman`, `foreman` (software-factory supervisor keeping agents on task).
- Code review: `jev-review` (several variants, one with a local dashboard, one as an MCP
  plugin), `diffjury` (PR risk router), `check-risk` (GitHub Action recommending checks
  and reviewers), `agent-gate-loop`, `JevLint` (semantic linting, file-level Nouls).
- Skill and capability routing: `typesafe-skill-router`, `jev-skillful`, `typesafe-mod`
  (ranks installed skills per prompt), `jev-predict-skill`. TypeSafe's cookbook ranks 182
  skills in one request.
- Context hygiene: `winnow` (every tool result judged before entering context),
  `fast-jev-compaction`, `save-token-jev`.
- Judging sessions: `ask-jev`, Vercel AI SDK `experimental_evaluate` with Jev as the
  evaluation model, Cribl replacing a committee of LLM judges for grading agent responses.
- Issue triage: `jev-triage`.
- MCP servers exposing classify / score / check / match / screen tools: at least six.
- CLI: `jev-axi` (pick, rate, check, rank, triage, guard from the shell), `typesafe-cli`.

## Other applications worth remembering

- `pg-jev` and `pg_typesafe`: ask Postgres tables questions, categorical classification
  in SQL.
- `HA-Jev` and `typesafe-assist`: Home Assistant entities and conversation agent.
- `neo4jev`: navigating a Neo4j graph by classifying over neighbouring relationships.
- `zod-jev`: Zod validates shape, Jev validates meaning of request bodies.
- `n8n-nodes-typesafe-ai`: n8n node.
- `youtube-sponsor-detection`: skip sponsor segments.
- Legal corpus testing, sponsor-inquiry triage on a newsletter form (Flavio Copes),
  telemetry log-type routing (Cribl), idea scoring across ~10 dimensions (Reddit).
- Playbook reference designs (`awesome-jev-by-typesafe`): security incident response,
  agent-trace observability, invoice matching and payment controls, multi-action
  customer service, abstention for claims and moderation, verified extraction cascades,
  autoresearch for semantic features.

## What did not work, or worked less well than the hype

- **Wide technical option sets.** Cribl's engineering blog reports Jev misclassifying
  noticeably more often than their purpose-built classifier on a 28-way log-type Choice,
  mostly by dumping known types into `other`, while still being much faster and cheaper.
  Lesson: keep option sets narrow or walk a hierarchy.
- **Generation of any kind.** Spelling words letter by letter via Choice produced `bue`
  and `helhoh`. Finishing a partial worked better than starting from nothing.
- **Defect detection against a frontier reasoning model.** Mike Taylor's planted-defect
  test: Jev caught most of them at a fraction of the latency, the reasoning model caught
  all of them. His verdict: an early-warning system, because the alternative is not
  checking.
- **The headline multipliers** are from TypeSafe's own workflow evals against a mid-tier
  model, with reference labels generated by other models rather than humans. Independent
  side-by-sides report smaller but still large gains. Read the evals page and decide.
- **Grading is the work.** The builder who spent the week trying to break it: "if you
  don't get the grading right, it doesn't work." The option set and question wording are
  where the effort goes; the call itself is trivial.
- **"Can't hallucinate" is wrong as stated.** It cannot emit an invalid type; it can emit
  a confidently wrong valid value. The founder accepted "a very good zero-shot classifier
  with calibrated probabilities" as the honest framing.

## Four rules from the docs and the founder's replies

1. Ask many questions per call; they evaluate in parallel.
2. Threshold on confidence; below roughly 0.3-0.5, ask a human rather than act.
3. Give it candidates, do not ask it to invent. Add an `other` for the edge cases.
4. Get the grading right or nothing else matters.

## Where Jev is available

Direct: `POST https://api.typesafe.ai/v1/systemone` with a Bearer key. Also via Vercel AI
Gateway, Cloudflare Workers AI and AI Gateway, Netlify AI Gateway, OpenRouter (beta),
LiteLLM pass-through, LangChain (`langchain-typesafe`, `TypeSafeClassifier`), Vercel AI
SDK (`@ai-sdk/typesafe-ai`), and community SDKs in Go, Rust, Ruby, .NET, PHP, Elixir,
Swift, Scala, Zig. Community catalogues: awesomejev.com, `Anil-matcha/awesome-jev-by-typesafe`
(with a use-case playbook), `AnotiaWang/awesome-jev`, `AbdelStark/awesome-typesafe`.
