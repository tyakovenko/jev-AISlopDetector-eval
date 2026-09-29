# jev-AISlopDetector-eval

Can [Jev](https://typesafe.ai), TypeSafe's decision model, catch AI-slop *comments* in code diffs? This repo tests six comment questions as a [DeepEval JevEval](https://deepeval.com/docs/metrics-jev-eval) metric against blind human labels, and prototypes a check that tells you which questions in a JevEval metric are safe to ship.

It grew out of [jevathon](https://github.com/tyakovenko/jevathon), a hackathon project where Jev ran a 9-question AI-slop gate on every changed file. There, the lesson was that Jev works best when a large judgment ("is this code sloppy?") is broken into narrow typed questions. This repo measures how much the wording of those questions matters.

## Findings (n = 40 diffs, one labeler)

1. **Wording decides whether a question works.** One question (`explains_why`) came out backwards (AUC 0.25). Its escape clause said *"if nothing in the change is non-obvious, this is true."* On 18 diffs that added no comments, Jev followed that clause and answered true; the human labeler answered no, reading a bug fix as something that deserves a "why". Same diff, two different questions. Nothing about the model changed; the question did.
2. **Jev ranks well, but the default threshold is too lenient.** The whole JevEval score separates diffs the labeler would flag from ones she wouldn't with AUC 0.89. At JevEval's default pass mark of 0.5 it passes most of them anyway; agreement peaks around a cut-off of 0.94. The best single questions follow the same pattern: `no_narration` AUC 0.95 (best cut-off 0.89), `density` 0.85, `no_placeholder` 0.80. The threshold has to be set from labeled data, not assumed.
3. **Showing Jev the whole file didn't help.** Adding the full post-change file as context left results unchanged (AUC 0.86 vs 0.89). For comment questions, the diff is enough.
4. **Two questions couldn't be evaluated.** The labeler marked 32 of 33 diffs as consistently formatted and 39 of 40 as accurate, so there were almost no negatives for `format` or `accurate` to catch.
5. **Real models rarely write slop comments here.** Four models (GLM-5.3, DeepSeek-V4-Pro, Kimi-k2.7-code, Gemini-3.5-flash) fixing bugs and adding small features in this codebase added about four comment lines across 30 diffs; 2 of the 20 sampled were flagged. They mirror the file they're given, and the demo app has almost no comments.

Full tables: [`results/report.md`](results/report.md).

## The proposed JevEval addition: a question-set check

JevEval turns a set of user-written questions into a score with fixed math, so the score is only as good as those questions. `question_set_report()` in [`src/report.py`](src/report.py) runs before a question set ships: given Jev's probabilities and a small set of human labels, it reports per question

- agreement at the default gate (accuracy, Cohen's κ) and ranking quality (AUC),
- calibration (Brier score),
- the cut-off that best matches the labels,

and flags questions whose labels are one-sided, whose answer never changes, whose agreement or calibration is weak, or whose best cut-off is far from 0.5. On this dataset it caught both findings above: the inverted `explains_why` and the lenient default threshold.

## Setup

| Piece | What |
|---|---|
| Base code | [`data/base_app.py`](data/base_app.py), the jevathon demo Flask app (seeded bugs give models a real task) |
| Diffs | 20 real model fixes/features (5 per model) + 20 hand-written: 8 clean, 12 with one planted comment problem |
| Questions | 6 JevEval questions in [`src/questions.py`](src/questions.py), phrased so true = clean (JevEval scores P(true) as good) |
| Labels | [`data/labels.csv`](data/labels.csv), labeled blind in [`data/labeler.html`](data/labeler.html); the plant key was hidden until labeling was done |
| Conditions | Jev sees the task + diff; or task + diff + full file |
| Cost | 80 Jev calls, about $0.005 total |

## Limitations

- 40 diffs and one labeler: a pilot. No inter-annotator agreement.
- Cut-offs were chosen on the same data they're reported on, so they're optimistic.
- `format` and `accurate` had too few negatives to evaluate.
- One codebase and one programming language.
- The real-model prompts changed wording between the bug-fix and feature runs ("fixing a bug… Issue:" vs "working on… Task:").
- No comparison against an LLM judge on the same questions yet.

## Run it

```bash
python3 -m venv venv && venv/bin/pip install deepeval typesafe-sdk openai
cp .env.example .env   # TYPESAFE_API_KEY (+ GMI_* to regenerate real diffs)
cd src
../venv/bin/python gen_real.py && ../venv/bin/python gen_written.py && ../venv/bin/python build_dataset.py
../venv/bin/python run_eval.py      # Jev, both conditions
../venv/bin/python report.py        # needs data/labels.csv
```
