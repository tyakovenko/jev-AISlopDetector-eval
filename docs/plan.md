# Plan — jev-AISlopDetector-eval
*Last updated: 2026-09-28*

## Goal
Measure whether Jev (via DeepEval's JevEval) can detect AI-slop *comments* in code diffs, per question, against blind human labels; propose a question-set check for JevEval.

## Milestones
- [ ] M1: Scaffolding, keys, JevEval smoke test
- [ ] M2: Dataset: 40 diffs on jevathon-demo-repo `app.py` (~20 real model fixes via GMI, ~20 written: clean + one planted comment issue each)
- [ ] M3: Blind labeling sheet → Taya labels 6 questions × 40 diffs (~1h)
- [ ] M4: Run JevEval (diff only, and diff + full file context)
- [ ] M5: Analysis: per-question agreement (accuracy, Cohen's kappa), calibration (Brier, reliability bins), threshold sweep, context A/B
- [ ] M6: `question_set_report()` prototype = proposed DeepEval addition; README write-up

## Out of Scope (v1)
- Non-comment slop (the other jevathon rubric questions)
- Multiple labelers / inter-annotator agreement

## Open Questions
- Does Jev need the whole file to judge format consistency? (tested in M4)
