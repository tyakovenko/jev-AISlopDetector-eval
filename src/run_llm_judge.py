"""LLM-judge baseline: Claude Haiku answers the same six questions as Jev.

Same question text, same options, same diff-only input. Haiku is asked for a
probability per answer so its output maps onto the same scale as Jev's and the
same report scores both. Runs through the `claude` CLI on the subscription login;
ANTHROPIC_API_KEY is stripped so it never bills API credit (same rule as the job scout).
Writes results/llm_results.jsonl in the jev_results.jsonl schema.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from deepeval.metrics.jev_eval.questions import Choice, Noul

from questions import QUESTIONS

ROOT = Path(__file__).resolve().parent.parent
MODEL = "claude-haiku-4-5-20251001"
CONDITION = "haiku_diff_only"

PROMPT = """You are judging the comments in a code change. Answer each question about the diff below.

Task the change was made for: {task}

Diff (actual_output):
```diff
{diff}
```

Questions:
{questions}

For every question give probabilities that sum to 1. For yes/no questions give the probability that the statement is true.
Reply with only a JSON object, no prose, in this shape:
{shape}"""


def question_block() -> tuple[str, str]:
    lines, shape = [], {}
    for qid, q in QUESTIONS.items():
        if isinstance(q, Noul):
            lines.append(f'- {qid} (true/false): {q.statement}')
            shape[qid] = {"true": 0.0}
        else:
            opts = list(q.options)
            lines.append(f'- {qid} (pick one of {", ".join(opts)}): {q.question}')
            shape[qid] = {o: 0.0 for o in opts}
    return "\n".join(lines), json.dumps(shape)


def ask(prompt: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    out = subprocess.run(["claude", "-p", "--model", MODEL, prompt], capture_output=True, text=True,
                         env=env, timeout=180, cwd="/tmp")
    m = re.search(r"\{.*\}", out.stdout, re.S)
    if out.returncode != 0 or not m:
        raise RuntimeError(f"claude exit {out.returncode}: {out.stdout[:200]} {out.stderr[:200]}")
    return json.loads(m.group(0))


def normalise(qid: str, raw: dict) -> dict:
    """Coerce Haiku's answer onto the same probability keys Jev returns."""
    q = QUESTIONS[qid]
    if isinstance(q, Noul):
        p = min(max(float(raw.get("true", 0.0)), 0.0), 1.0)
        return {"true": p, "false": 1 - p}
    probs = {o: max(float(raw.get(o, 0.0)), 0.0) for o in q.options}
    total = sum(probs.values())
    if total <= 0:
        raise ValueError(f"{qid}: no probability mass")
    return {o: v / total for o, v in probs.items()}


def score(answers: dict) -> float:
    """JevEval's aggregation: Noul value = P(true); Choice = credit-weighted mean over applicable options."""
    vals = []
    for qid, q in QUESTIONS.items():
        probs = answers[qid]
        if isinstance(q, Noul):
            vals.append((q.weight, probs["true"]))
            continue
        credits = q.applicable_options
        na = sum(probs[o] for o in q.not_applicable_options)
        mass = sum(probs[o] for o in credits)
        if na < 0.5 and mass > 0:  # JevEval's not-applicable threshold
            vals.append((q.weight, sum(probs[o] * c for o, c in credits.items()) / mass))
    return sum(w * v for w, v in vals) / sum(w for w, _ in vals) if vals else 1.0


def main() -> None:
    diffs = [json.loads(l) for l in (ROOT / "data" / "diffs.jsonl").read_text().splitlines()]
    out = ROOT / "results" / "llm_results.jsonl"
    done = {json.loads(l)["id"] for l in out.read_text().splitlines()} if out.exists() else set()
    qtext, shape = question_block()
    with out.open("a") as f:
        for d in diffs:
            if d["id"] in done:
                continue
            try:
                raw = ask(PROMPT.format(task=d["issue_text"], diff=d["diff"], questions=qtext, shape=shape))
                answers = {qid: normalise(qid, raw.get(qid, {})) for qid in QUESTIONS}
            except Exception as e:  # noqa: BLE001 - log and continue; report lists missing ids
                print(f"ERROR {d['id']}: {e}", file=sys.stderr)
                continue
            f.write(json.dumps({"id": d["id"], "condition": CONDITION, "score": score(answers),
                                "questions": {qid: {"probabilities": p} for qid, p in answers.items()}}) + "\n")
            f.flush()
            print(f"ok {d['id']}")


if __name__ == "__main__":
    main()
