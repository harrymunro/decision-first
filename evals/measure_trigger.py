#!/usr/bin/env python3
"""Measure how often the *installed* decision-first skill is invoked by `claude -p` on the eval prompts.
Counts a trigger when a Skill tool call names decision-first (or a Read touches decision-first/SKILL.md)."""

import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import time


def run(query, model, timeout, max_turns, raw=False):
    cmd = [
        "claude",
        "-p",
        query,
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-turns",
        str(max_turns),
    ]
    if model:
        cmd += ["--model", model]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~"),
            env=env,
        )
        out, err, rc = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = (
            (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "TIMEOUT",
            -1,
        )
    except OSError as e:  # claude not on PATH, etc: one bad run must not kill the sweep
        out, err, rc = "", f"{type(e).__name__}: {e}", -1
    skills = re.findall(r'"name":\s*"Skill".{0,400}?"skill":\s*"([^"]+)"', out, re.S)
    reads = re.findall(r'"file_path":\s*"([^"]*decision-first[^"]*)"', out)
    err_line = ""
    for line in out.splitlines():
        if '"is_error":true' in line or '"subtype":"error' in line:
            err_line = line[:300]
    return {
        "rc": rc,
        "secs": round(time.time() - t0, 1),
        "skills": skills,
        "reads": reads,
        "stderr": err.strip()[:300],
        "err": err_line,
        "raw": out if raw else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--eval-set", default=os.path.join(os.path.dirname(__file__), "trigger-eval.json")
    )
    ap.add_argument(
        "--model", default=None, help="claude -p --model; default: your configured model"
    )
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--max-turns", type=int, default=3)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--only", help="comma-separated indexes")
    ap.add_argument("--raw", action="store_true", help="dump raw stream for the selected runs")
    ap.add_argument("--out")
    a = ap.parse_args()
    with open(a.eval_set, encoding="utf-8") as f:
        ev = json.load(f)
    idx = [int(i) for i in a.only.split(",")] if a.only else list(range(len(ev)))
    results = {}
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {
            ex.submit(run, ev[i]["query"], a.model, a.timeout, a.max_turns, a.raw): i for i in idx
        }
        for f in cf.as_completed(futs):
            i = futs[f]
            r = f.result()
            results[i] = r
            hit = any("decision-first" in s for s in r["skills"]) or bool(r["reads"])
            err = r["err"] or r["stderr"]
            print(
                f"[{i:02d}] exp={str(ev[i]['should_trigger'])[0]} hit={'Y' if hit else 'n'} "
                f"rc={r['rc']} {r['secs']}s skills={r['skills']} reads={len(r['reads'])} "
                f"{('ERR ' + err) if err else ''}",
                flush=True,
            )
            if a.raw and r["raw"]:
                print("----- raw (first 6000 chars) -----")
                print(r["raw"][:6000])
                print("----- end raw -----")
    tp = sum(
        1
        for i in idx
        if ev[i]["should_trigger"]
        and (any("decision-first" in s for s in results[i]["skills"]) or results[i]["reads"])
    )
    fp = sum(
        1
        for i in idx
        if not ev[i]["should_trigger"]
        and (any("decision-first" in s for s in results[i]["skills"]) or results[i]["reads"])
    )
    npos = sum(1 for i in idx if ev[i]["should_trigger"])
    nneg = len(idx) - npos
    errors = sum(1 for r in results.values() if r["rc"] != 0)
    print(
        f"\nshould-trigger hit rate: {tp}/{npos}   "
        f"should-not-trigger false alarms: {fp}/{nneg}   errors: {errors}"
    )
    if a.out:
        slim = {str(i): {k: v for k, v in r.items() if k != "raw"} for i, r in results.items()}
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(slim, f, indent=1)


if __name__ == "__main__":
    main()
