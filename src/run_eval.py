"""Run the comment-slop JevEval metric over every diff, in two conditions.

- diff_only: Jev sees the task and the diff (what the jevathon gate saw).
- with_file: Jev also gets the full post-change file as `context`.
Writes results/jev_results.jsonl: one row per (id, condition) with each question's
probabilities, so the report can score any threshold without re-calling Jev.
"""

import json
import sys
from pathlib import Path

from deepeval.test_case import LLMTestCase

from questions import QUESTION_IDS, build_metric

ROOT = Path(__file__).resolve().parent.parent
CONDITIONS = {"diff_only": False, "with_file": True}


def main() -> None:
    diffs = [json.loads(line) for line in (ROOT / "data" / "diffs.jsonl").read_text().splitlines()]
    out = ROOT / "results" / "jev_results.jsonl"
    done = set()
    if out.exists():
        done = {(r["id"], r["condition"]) for r in map(json.loads, out.read_text().splitlines())}

    total_cost = 0.0
    with out.open("a") as f:
        for cond, with_file in CONDITIONS.items():
            metric = build_metric(with_file_context=with_file)
            for d in diffs:
                if (d["id"], cond) in done:
                    continue
                tc = LLMTestCase(
                    input=d["issue_text"],
                    actual_output=d["diff"],
                    context=[d["new_code"]] if with_file else None,
                )
                try:
                    metric.measure(tc, _show_indicator=False)
                except Exception as e:  # noqa: BLE001 - one failed call must not lose the run
                    print(f"ERROR {d['id']}/{cond}: {e}", file=sys.stderr)
                    continue
                total_cost += metric.evaluation_cost or 0
                f.write(json.dumps({
                    "id": d["id"], "condition": cond, "score": metric.score,
                    "questions": {qid: {"value": o["value"], "applicable": o["applicable"],
                                        "probabilities": o["probabilities"]}
                                  for qid, o in zip(QUESTION_IDS, metric.score_breakdown)},
                }) + "\n")
                f.flush()
    print(f"done; Jev cost this run ${total_cost:.5f}")


if __name__ == "__main__":
    main()
