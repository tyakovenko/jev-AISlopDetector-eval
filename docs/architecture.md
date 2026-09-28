# Architecture — jev-AISlopDetector-eval
*Last updated: 2026-09-28*

## Overview
Offline eval. Code diffs → JevEval metric (6 comment questions, answered by Jev) → per-question probabilities → compared to Taya's blind labels.

## Components
| Component | Responsibility | Tech |
|---|---|---|
| `src/questions.py` | The 6 comment questions as JevEval Noul/Choice | deepeval JevEval |
| `src/make_dataset.py` | Real model fixes (GMI) + written/planted diffs → `data/diffs.jsonl` | openai-compatible client |
| `data/labeling_sheet.md` / `labels.csv` | Blind human labels | markdown/CSV |
| `src/run_eval.py` | JevEval over all diffs, two context conditions | deepeval + typesafe-sdk |
| `src/report.py` | Agreement, calibration, threshold sweep; the proposed question-set report | pandas/numpy |

## Data Flow
demo `app.py` → diffs.jsonl → (labels.csv, jev_results.jsonl) → report.md

## Key Decisions
- Questions phrased so Noul true = good — JevEval maps P(true) straight to score.
- Base code = jevathon demo repo (seeded bugs give models a real task to comment on).
