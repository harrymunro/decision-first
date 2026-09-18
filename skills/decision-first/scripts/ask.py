#!/usr/bin/env python3
"""Run a set of Jev (TypeSafe System One) questions over one state or many items.

Stdlib only. Reads TYPESAFE_API_KEY from the environment.

Examples
--------
  # one state, questions in a file
  ask.py --questions q.json --state state.json

  # a state inline
  ask.py --questions q.json --state-text "My card was charged twice"

  # many items (JSONL or a JSON array), each wrapped under a key, 8 at a time
  ask.py --questions q.json --items beads.jsonl --wrap bead --workers 8 --out results.jsonl

  # see the request without sending it
  ask.py --questions q.json --state state.json --dry-run

questions file: either {"questions": {...}, "state": {...}?} or a bare map of question ids
to question objects ({"type": "noul"|"choice"|"score", "instructions": ..., "criteria": ...}).

Output: one JSON object per item on stdout (or --out), shaped
  {"id": ..., "model": ..., "answers": {...}, "usage": {...}, "ms": ...}
plus a per-question summary table and totals on stderr.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextlib
import http.client
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("TYPESAFE_API_BASE", "https://api.typesafe.ai") + "/v1/systemone"
PRICE_PER_MTOK = 0.042  # USD per million input tokens; output is free (Sept 2026)


def ssl_context() -> ssl.SSLContext:
    """Default TLS context, with fallbacks for Python builds that ship without CA certs
    (python.org macOS installs before 'Install Certificates.command' has been run)."""
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0) > 0:
        return ctx
    candidates = [os.environ.get("SSL_CERT_FILE")]
    try:
        import certifi  # type: ignore

        candidates.append(certifi.where())
    except Exception:  # noqa: BLE001
        pass
    candidates += [
        "/etc/ssl/cert.pem",
        "/opt/homebrew/etc/openssl@3/cert.pem",
        "/usr/local/etc/openssl@3/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    ]
    for cafile in candidates:
        if cafile and os.path.exists(cafile):
            ctx.load_verify_locations(cafile)
            return ctx
    return ctx


CTX = ssl_context()


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return json.loads(text)


def load_questions(path: str) -> tuple[dict, object | None]:
    data = load_json(path)
    if isinstance(data, dict) and "questions" in data and isinstance(data["questions"], dict):
        return data["questions"], data.get("state")
    if isinstance(data, dict) and all(isinstance(v, dict) and "type" in v for v in data.values()):
        return data, None
    sys.exit(f"{path}: expected a questions map or an object with a 'questions' key")


def load_items(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    stripped = text.lstrip()
    if stripped.startswith("["):
        return json.loads(text)
    items = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"{path}:{n}: bad JSON ({e})")
    return items


def call(
    model: str, state, questions: dict, key: str, timeout: float, retries: int = 5
) -> tuple[dict, float]:
    body = json.dumps({"model": model, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    delay = 1.0
    for attempt in range(1, retries + 1):
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                payload = json.loads(resp.read().decode())
                return payload, (time.perf_counter() - t0) * 1000
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")
            retryable = e.code == 429 or e.code >= 500
            if not retryable or attempt == retries:
                raise RuntimeError(f"HTTP {e.code}: {text[:500]}") from None
            ra = e.headers.get("retry-after")
            wait = float(ra) if ra and ra.replace(".", "", 1).isdigit() else delay
            time.sleep(wait)
            delay = min(delay * 2, 30)
        except (OSError, http.client.HTTPException) as e:  # URLError, resets, truncated reads
            if attempt == retries:
                raise RuntimeError(f"connection failed: {e}") from None
            time.sleep(delay)
            delay = min(delay * 2, 30)
    raise RuntimeError("unreachable")


def brief(answer: dict) -> str:
    t = answer.get("type")
    if t == "noul":
        return f"{answer['noul']:.2f}"
    if t == "choice":
        return f"{answer['choice']} ({answer.get('confidence', 0):.2f})"
    if t == "score":
        return f"{answer['score']:.2f} ({answer.get('confidence', 0):.2f})"
    return json.dumps(answer)[:40]


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--questions", required=True, help="questions JSON file")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--state", help="state JSON file")
    src.add_argument("--state-text", help="state as a plain string")
    src.add_argument("--items", help="JSONL file or JSON array; one request per item")
    ap.add_argument(
        "--wrap", help="wrap each item under this key, e.g. --wrap bead -> state={'bead': item}"
    )
    ap.add_argument(
        "--id-field", default="id", help="item field to use as id (default: id, else index)"
    )
    ap.add_argument("--limit", type=int, help="only the first N items")
    ap.add_argument("--model", default=os.environ.get("JEV_MODEL", "jev-latest"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--out", help="write JSONL results here instead of stdout")
    ap.add_argument("--dry-run", action="store_true", help="print the first request and exit")
    ap.add_argument("--quiet", action="store_true", help="no per-item table on stderr")
    args = ap.parse_args()

    questions, embedded_state = load_questions(args.questions)

    if args.items:
        items = load_items(args.items)
        if args.limit:
            items = items[: args.limit]
        jobs = []
        for i, item in enumerate(items):
            item_id = item.get(args.id_field, i) if isinstance(item, dict) else i
            state = {args.wrap: item} if args.wrap else item
            jobs.append((item_id, state))
        if not jobs:
            sys.exit(f"{args.items}: no items")
    else:
        if args.state:
            state = load_json(args.state)
        elif args.state_text is not None:
            state = args.state_text
        elif embedded_state is not None:
            state = embedded_state
        else:
            sys.exit("need --state, --state-text, --items, or a 'state' key in the questions file")
        if args.wrap:
            state = {args.wrap: state}
        jobs = [(0, state)]

    if args.dry_run:
        print(
            json.dumps({"model": args.model, "state": jobs[0][1], "questions": questions}, indent=2)
        )
        print(f"\n{len(jobs)} request(s) would be sent to {ENDPOINT}", file=sys.stderr)
        return

    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        sys.exit("TYPESAFE_API_KEY is not set")

    with contextlib.ExitStack() as stack:
        out = sys.stdout
        if args.out:
            out = stack.enter_context(open(args.out, "w", encoding="utf-8"))
        qids = list(questions)
        widths = {q: max(len(q), 14) for q in qids}
        if not args.quiet:
            print(
                "id".ljust(12) + "  " + "  ".join(q.ljust(widths[q]) for q in qids), file=sys.stderr
            )

        tokens = 0
        latencies: list[float] = []
        models: set[str] = set()
        failures = 0
        t_start = time.perf_counter()

        def run(job):
            item_id, state = job
            payload, ms = call(args.model, state, questions, key, args.timeout)
            return item_id, payload, ms

        with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futures = {ex.submit(run, job): job for job in jobs}
            for fut in cf.as_completed(futures):
                item_id = futures[fut][0]
                try:
                    item_id, payload, ms = fut.result()
                except Exception as e:  # noqa: BLE001
                    failures += 1
                    print(f"{str(item_id).ljust(12)}  ERROR {e}", file=sys.stderr)
                    out.write(json.dumps({"id": item_id, "error": str(e)}) + "\n")
                    continue
                answers = payload.get("answers", {})
                usage = payload.get("usage", {})
                tokens += usage.get("input_tokens", 0)
                latencies.append(ms)
                models.add(payload.get("model") or args.model)
                rec = {
                    "id": item_id,
                    "model": payload.get("model"),
                    "answers": answers,
                    "usage": usage,
                    "ms": round(ms),
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                if not args.quiet:
                    cells = "  ".join(
                        brief(answers[q]).ljust(widths[q]) if q in answers else "-".ljust(widths[q])
                        for q in qids
                    )
                    print(f"{str(item_id)[:12].ljust(12)}  {cells}", file=sys.stderr)

    wall = time.perf_counter() - t_start
    n = len(latencies)
    p50 = sorted(latencies)[n // 2] if n else 0
    cost = tokens / 1e6 * PRICE_PER_MTOK
    answered = "/".join(sorted(models)) if models else args.model  # the versioned id: log it
    print(
        f"\n{n} ok, {failures} failed | model {answered} | {tokens} input tokens ≈ ${cost:.5f} | "
        f"p50 {p50:.0f} ms | wall {wall:.1f} s" + (f" | wrote {args.out}" if args.out else ""),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
