"""Merge real + written diffs, shuffle, and write the blind labeling sheet.

Outputs
- data/diffs.jsonl          id, issue_text, diff, new_code (what Jev sees)
- data/plant_key.json       id -> source/model/plant (hidden from the labeler)
- data/labeling_sheet.md    issue + diff per id, nothing about the source
- data/labels.csv           empty template Taya fills in
"""

import csv
import json
import random
from pathlib import Path

from questions import QUESTION_IDS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = 20260928  # fixed so the sheet order is reproducible

GUIDE = """# Labeling sheet (blind)

Label each diff on the 6 questions below, in `data/labels.csv` (one row per id).
Judge only comments and docstrings **added** in the diff (`+` lines). Don't judge the fix itself.
Don't open `data/plant_key.json` until you're done.

| Column | Question | Values |
|---|---|---|
| no_narration | Every added comment explains intent/constraint/reason; none just restates the adjacent code. No comments added = yes | yes / no |
| density | How dense are the added comments? | none / appropriate / excessive |
| format | Added comments/docstrings: consistent with each other and the file, inconsistent (mixed styles, casing, `#` spacing), or malformed (misplaced docstring, cut off, wrong line) | consistent / inconsistent / malformed / none |
| accurate | Every added comment accurately describes what the code does. No comments added = yes | yes / no |
| no_placeholder | No placeholder/hedging comments ("in a real implementation", "for simplicity", ownerless TODO) and no commented-out code | yes / no |
| explains_why | Wherever the change is non-obvious, a comment says why. Nothing non-obvious = yes | yes / no |
| overall_slop | Gut call: would you flag these comments in code review? | yes / no |
| notes | Optional | free text |

---
"""


REAL_PER_MODEL = 5  # 4 models x 5 = 20 real diffs, matching the 20 written ones


def adds_comment(r: dict) -> bool:
    return any(l.startswith("+") and ("#" in l or '"""' in l) for l in r["diff"].splitlines())


def sample_real(real: list[dict], rng: random.Random) -> list[dict]:
    """Up to REAL_PER_MODEL per model, keeping every diff that adds a comment:
    real models rarely comment, so those are the scarce, informative cases."""
    picked = []
    for model in sorted({r["model"] for r in real}):
        mine = [r for r in real if r["model"] == model]
        commented = [r for r in mine if adds_comment(r)]
        rest = [r for r in mine if not adds_comment(r)]
        rng.shuffle(rest)
        picked += (commented + rest)[:REAL_PER_MODEL]
    return picked


def main() -> None:
    rng = random.Random(SEED)
    real = [json.loads(line) for line in (DATA / "raw_real.jsonl").read_text().splitlines()]
    written = [json.loads(line) for line in (DATA / "raw_written.jsonl").read_text().splitlines()]
    records = sample_real(real, rng) + written
    rng.shuffle(records)

    key, sheet = {}, [GUIDE]
    with (DATA / "diffs.jsonl").open("w") as f:
        for i, r in enumerate(records, 1):
            rid = f"d{i:02d}"
            f.write(json.dumps({"id": rid, "issue_text": r["issue_text"], "diff": r["diff"],
                                "new_code": r["new_code"]}) + "\n")
            key[rid] = {k: r.get(k) for k in ("model", "requested_model", "issue", "plant")}
            sheet.append(f"## {rid}\n\n**Task:** {r['issue_text']}\n\n```diff\n{r['diff']}```\n")

    (DATA / "plant_key.json").write_text(json.dumps(key, indent=1))
    (DATA / "labeling_sheet.md").write_text("\n".join(sheet))
    with (DATA / "labels.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", *QUESTION_IDS, "overall_slop", "notes"])
        for rid in key:
            w.writerow([rid] + [""] * (len(QUESTION_IDS) + 2))
    print(f"{len(records)} diffs -> labeling_sheet.md, labels.csv")


if __name__ == "__main__":
    main()
