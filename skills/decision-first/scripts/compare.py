#!/usr/bin/env python3
"""Compare ask.py results against known labels, per question.

  compare.py results.jsonl --labels labels.json [--threshold 0.5] [--question q]

labels.json maps item id -> {question_id: expected}. Expected values:
  noul   -> true/false (or 1/0, "yes"/"no")
  choice -> option name
  score  -> integer level (the answer's score is rounded to the nearest level)

Prints agreement per question, a confusion table for choices, and every disagreement
with the model's confidence so you can see whether the misses are the uncertain ones.
Missing labels for an item or question are skipped, so partial labels are fine.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys

TRUTHY = {"true", "yes", "y", "1", "t"}
FALSY = {"false", "no", "n", "0", "f"}


def as_bool(v) -> bool | None:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v >= 0.5
    if isinstance(v, str):
        s = v.strip().lower()
        if s in TRUTHY:
            return True
        if s in FALSY:
            return False
    return None


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("results", help="JSONL from ask.py")
    ap.add_argument("--labels", required=True, help="JSON: {id: {question_id: expected}}")
    ap.add_argument("--threshold", type=float, default=0.5, help="noul >= threshold counts as yes")
    ap.add_argument("--question", action="append", help="only evaluate these question ids")
    ap.add_argument("--show", type=int, default=25, help="max disagreements to print per question")
    args = ap.parse_args()

    with open(args.labels, encoding="utf-8") as f:
        labels = json.load(f)
    labels = {str(k): v for k, v in labels.items()}

    results = []
    with open(args.results, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    per_q: dict[str, dict] = collections.defaultdict(
        lambda: {
            "n": 0,
            "ok": 0,
            "misses": [],
            "conf_ok": [],
            "conf_miss": [],
            "confusion": collections.Counter(),
        }
    )

    for rec in results:
        rid = str(rec.get("id"))
        if rid not in labels or "answers" not in rec:
            continue
        for qid, expected in labels[rid].items():
            if args.question and qid not in args.question:
                continue
            ans = rec["answers"].get(qid)
            if ans is None:
                continue
            t = ans.get("type")
            if t == "noul":
                exp = as_bool(expected)
                if exp is None:
                    continue
                got = ans["noul"] >= args.threshold
                conf = abs(ans["noul"] - 0.5) * 2
                got_label, exp_label = str(got).lower(), str(exp).lower()
            elif t == "choice":
                got, exp = ans["choice"], str(expected)
                conf = ans.get("confidence", 0.0)
                got_label, exp_label = got, exp
            elif t == "score":
                got, exp = round(ans["score"]), int(round(float(expected)))
                conf = ans.get("confidence", 0.0)
                got_label, exp_label = str(got), str(exp)
            else:
                continue
            slot = per_q[qid]
            slot["n"] += 1
            slot["confusion"][(exp_label, got_label)] += 1
            if got == exp:
                slot["ok"] += 1
                slot["conf_ok"].append(conf)
            else:
                slot["misses"].append((rid, exp_label, got_label, conf))
                slot["conf_miss"].append(conf)

    if not per_q:
        sys.exit("no overlapping ids/questions between results and labels")

    def mean(xs):
        return sum(xs) / len(xs) if xs else float("nan")

    print(f"{'question':<28}{'n':>5}{'agree':>8}{'conf(ok)':>10}{'conf(miss)':>12}")
    for qid, s in per_q.items():
        agree = s["ok"] / s["n"]
        print(
            f"{qid:<28}{s['n']:>5}{agree:>8.1%}"
            f"{mean(s['conf_ok']):>10.2f}{mean(s['conf_miss']):>12.2f}"
        )

    for qid, s in per_q.items():
        labels_seen = sorted({e for e, _ in s["confusion"]} | {g for _, g in s["confusion"]})
        if len(labels_seen) > 1:
            print(f"\nconfusion for {qid} (rows expected, cols got)")
            w = max(8, max(len(x) for x in labels_seen) + 2)
            print(" " * w + "".join(x.rjust(w) for x in labels_seen))
            for e in labels_seen:
                print(
                    e.ljust(w)
                    + "".join(str(s["confusion"].get((e, g), 0)).rjust(w) for g in labels_seen)
                )
        if s["misses"]:
            print(f"\ndisagreements for {qid} ({len(s['misses'])}):")
            for rid, exp, got, conf in sorted(s["misses"], key=lambda m: -m[3])[: args.show]:
                print(f"  {rid:<20} expected {exp:<16} got {got:<16} conf {conf:.2f}")

    print(
        "\nRead the conf columns: if misses cluster at low confidence, a threshold or "
        "review queue fixes most of them; if misses are confident, the question wording "
        "or the criteria are wrong."
    )


if __name__ == "__main__":
    main()
