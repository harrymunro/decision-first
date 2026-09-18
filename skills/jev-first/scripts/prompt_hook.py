#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge the agent to load the jev-first skill when a prompt smells
like a bounded-judgment task. Reads the hook JSON on stdin, prints a one-line reminder on
stdout when the vocabulary matches, always exits 0 so it can never block a prompt.

Register in settings.json under hooks.UserPromptSubmit. Tune WORDS below if it fires too
often or too rarely; the skill description does the real work, this is a safety net.
"""

import json
import re
import sys

WORDS = [
    r"classif\w*",
    r"categori[sz]\w*",
    r"\btag(s|ged|ging)?\b",
    r"label\w*",
    r"triag\w*",
    r"prioriti[sz]\w*",
    r"\bsiz(e|ing)\b",
    r"estimat\w*",
    r"\bscor(e|es|ing)\b",
    r"\brat(e|ing)\b",
    r"\brank\w*",
    r"\bsort (these|them|into|out)",
    r"\brout(e|ing)\b",
    r"dispatch\w*",
    r"\bfilter\w*",
    r"dedup\w*",
    r"duplicate",
    r"\bmatch(es|ing)?\b",
    r"reconcil\w*",
    r"verif\w*",
    r"\bflag\w*",
    r"moderat\w*",
    r"\breview\w*",
    r"\bgrad(e|ing)\b",
    r"screen\w*",
    r"detect\w*",
    r"\bjudge\b",
    r"llm.as.a.judge",
    r"go through (all|each|every|the)",
    r"for each (of|ticket|issue|bead|email|row|record)",
    r"sort (these|them) into",
    r"which of these",
    r"is this an?\b",
    r"does this (need|look|count|comply|match)",
    r"should this (go|be|get)",
    r"how (bad|big|urgent|severe|risky) is",
    r"needs? a human",
    r"waiting on",
    r"backlog",
    r"\bbeads?\b",
    r"\binbox\b",
    r"tickets?\b",
    r"transcripts?\b",
    r"tool calls?\b",
    r"structured output",
    r"respond only with",
    r"json mode",
    r"regex",
    r"keyword",
    r"heuristic",
    r"\bjev\b",
    r"typesafe",
    r"system one",
]
PATTERN = re.compile("|".join(WORDS), re.I)


def main() -> None:
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "") if isinstance(data, dict) else ""
    except Exception:  # noqa: BLE001
        return
    if not prompt or len(prompt) < 25:
        return
    hits = sorted({m.group(0).lower() for m in PATTERN.finditer(prompt)})
    if not hits:
        return
    shown = ", ".join(hits[:5])
    print(
        f"jev-first: this looks like it contains a bounded-judgment step (matched: {shown}). "
        "Load the jev-first skill before planning, name the candidate in one line, "
        "and log the trigger."
    )


if __name__ == "__main__":
    main()
