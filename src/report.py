"""Compare Jev's answers with Taya's labels and write results/report.md.

`question_set_report` is the proposed DeepEval addition: given each question's
P(good) from Jev and a human label per case, it reports agreement, calibration and
threshold fit per question, and flags questions that shouldn't ship as-is.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from questions import QUESTION_IDS

ROOT = Path(__file__).resolve().parent.parent

# Human label -> good (1) / bad (0) / not applicable (None). Mirrors the credits in questions.py.
LABEL_TO_GOOD = {
    "no_narration": {"yes": 1, "no": 0},
    "density": {"none": 1, "appropriate": 1, "excessive": 0},
    "format": {"consistent": 1, "inconsistent": 0, "malformed": 0, "none": None},
    "accurate": {"yes": 1, "no": 0},
    "no_placeholder": {"yes": 1, "no": 0},
    "explains_why": {"yes": 1, "no": 0},
}

# Flag thresholds for the question-set check. Conventional cut-offs, stated so they can be argued with.
KAPPA_FLOOR = 0.4  # below "moderate" agreement (Landis & Koch)
BRIER_CEILING = 0.25  # no better than always answering 0.5
THRESHOLD_SHIFT = 0.15  # best cut-off this far from 0.5 means the default gate is miscalibrated


def p_good(qid: str, q: dict) -> float | None:
    """Jev's probability that the answer is the good one, on the same scale as the label."""
    probs = q["probabilities"]
    if qid == "density":
        return probs["no_comments_added"] + probs["appropriate"]
    if qid == "format":
        applicable_mass = 1 - probs["no_comments_added"]
        return probs["consistent"] / applicable_mass if applicable_mass > 1e-9 else None
    return probs["true"]


def kappa(y: list[int], yhat: list[int]) -> float:
    n = len(y)
    po = sum(a == b for a, b in zip(y, yhat)) / n
    p1, q1 = sum(y) / n, sum(yhat) / n
    pe = p1 * q1 + (1 - p1) * (1 - q1)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def auc(y: list[int], p: list[float]) -> float | None:
    pos = [pi for yi, pi in zip(y, p) if yi == 1]
    neg = [pi for yi, pi in zip(y, p) if yi == 0]
    if not pos or not neg:
        return None
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def best_threshold(y: list[int], p: list[float]) -> tuple[float, float]:
    """Cut-off maximising balanced accuracy; returns (threshold, balanced accuracy)."""
    best = (0.5, -1.0)
    for t in [i / 100 for i in range(5, 96)]:
        yhat = [int(pi >= t) for pi in p]
        tpr = sum(a and b for a, b in zip(y, yhat)) / max(sum(y), 1)
        tnr = sum((not a) and (not b) for a, b in zip(y, yhat)) / max(len(y) - sum(y), 1)
        bal = (tpr + tnr) / 2
        if bal > best[1] + 1e-9:
            best = (t, bal)
    return best


def calibration_bins(y: list[int], p: list[float]) -> list[tuple[str, int, float, float]]:
    bins = [(0.0, 1 / 3, "0-0.33"), (1 / 3, 2 / 3, "0.33-0.67"), (2 / 3, 1.01, "0.67-1")]
    out = []
    for lo, hi, name in bins:
        idx = [i for i, pi in enumerate(p) if lo <= pi < hi]
        if idx:
            out.append((name, len(idx), sum(p[i] for i in idx) / len(idx), sum(y[i] for i in idx) / len(idx)))
    return out


def question_set_report(pred: dict[str, list[float | None]], labels: dict[str, list[int | None]]) -> list[dict]:
    """Per question: agreement with humans at the default 0.5 gate, calibration, best cut-off, flags."""
    rows = []
    for qid in pred:
        pairs = [(y, p) for y, p in zip(labels[qid], pred[qid]) if y is not None and p is not None]
        y, p = [a for a, _ in pairs], [b for _, b in pairs]
        n = len(y)
        if n == 0:
            rows.append({"question": qid, "n": 0, "flags": ["no applicable labeled cases"]})
            continue
        yhat = [int(pi >= 0.5) for pi in p]
        acc = sum(a == b for a, b in zip(y, yhat)) / n
        k = kappa(y, yhat)
        brier = sum((pi - yi) ** 2 for yi, pi in zip(y, p)) / n
        t, bal = best_threshold(y, p)
        flags = []
        if len(set(y)) == 1:
            flags.append(f"labels are all {'good' if y[0] else 'bad'}: agreement is uninformative")
        if len(set(yhat)) == 1:
            flags.append("never changes its answer at 0.5")
        if k < KAPPA_FLOOR:
            flags.append(f"kappa {k:.2f} < {KAPPA_FLOOR}")
        if brier > BRIER_CEILING:
            flags.append(f"Brier {brier:.2f} > {BRIER_CEILING}")
        if abs(t - 0.5) >= THRESHOLD_SHIFT:
            flags.append(f"best cut-off {t:.2f}, not 0.5")
        rows.append({"question": qid, "n": n, "human_good_rate": sum(y) / n, "accuracy": acc,
                     "kappa": k, "auc": auc(y, p), "brier": brier, "best_threshold": t,
                     "balanced_acc_at_best": bal, "calibration": calibration_bins(y, p), "flags": flags})
    return rows


def load() -> tuple[dict, dict, dict]:
    labels = {}
    with (ROOT / "data" / "labels.csv").open() as f:
        for r in csv.DictReader(f):
            if not all(r[q].strip() for q in QUESTION_IDS):
                raise ValueError(f"{r['id']}: missing labels; label every question before running the report")
            labels[r["id"]] = r
    results = defaultdict(dict)
    for line in (ROOT / "results" / "jev_results.jsonl").read_text().splitlines():
        r = json.loads(line)
        results[r["condition"]][r["id"]] = r
    key = json.loads((ROOT / "data" / "plant_key.json").read_text())
    return labels, results, key


def fmt(x, nd=2):
    return "–" if x is None else f"{x:.{nd}f}"


def main() -> None:
    labels, results, key = load()
    ids = sorted(labels)
    y = {q: [LABEL_TO_GOOD[q][labels[i][q].strip().lower()] for i in ids] for q in QUESTION_IDS}
    lines = ["# Results: can Jev spot AI-slop comments?", "",
             f"n = {len(ids)} diffs, one labeler (Taya, blind). A pilot, not a benchmark.", ""]
    for cond, res in results.items():
        missing = [i for i in ids if i not in res]
        pred = {q: [None if i in missing else p_good(q, res[i]["questions"][q]) for i in ids] for q in QUESTION_IDS}
        lines += [f"## Condition: {cond}", "",
                  "| Question | n | Human 'good' rate | Accuracy @0.5 | Cohen's κ | AUC | Brier | Best cut-off | Flags |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in question_set_report(pred, y):
            lines.append(f"| {r['question']} | {r['n']} | {fmt(r.get('human_good_rate'))} | {fmt(r.get('accuracy'))} | "
                         f"{fmt(r.get('kappa'))} | {fmt(r.get('auc'))} | {fmt(r.get('brier'))} | "
                         f"{fmt(r.get('best_threshold'))} | {'; '.join(r['flags']) or 'ok'} |")
        overall_y = [int(labels[i]["overall_slop"].strip().lower() == "no") for i in ids if i in res]
        overall_p = [res[i]["score"] for i in ids if i in res]
        t, bal = best_threshold(overall_y, overall_p)
        lines += ["", f"**Whole metric (JevEval score) vs 'would you flag it?':** AUC {fmt(auc(overall_y, overall_p))}, "
                  f"best cut-off {t:.2f} (balanced accuracy {bal:.2f}).", ""]
        if missing:
            lines += [f"Missing Jev results: {', '.join(missing)}", ""]

    # Sanity check on the dataset: did Taya see the planted problem where one was planted?
    lines += ["## Plant check (hand-written diffs only)", "", "| id | planted | Taya overall_slop |", "|---|---|---|"]
    for i in ids:
        if key[i].get("plant"):
            lines.append(f"| {i} | {key[i]['plant']} | {labels[i]['overall_slop']} |")
    by_model = defaultdict(list)
    for i in ids:
        if not key[i].get("plant"):
            by_model[key[i]["model"]].append(labels[i]["overall_slop"].strip().lower() == "yes")
    lines += ["", "## Real model fixes flagged as sloppy by Taya", "", "| model | flagged / n |", "|---|---|"]
    for m, v in sorted(by_model.items()):
        lines.append(f"| {m} | {sum(v)} / {len(v)} |")
    (ROOT / "results" / "report.md").write_text("\n".join(lines) + "\n")
    print("wrote results/report.md")


if __name__ == "__main__":
    main()
