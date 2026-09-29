# Results: can Jev spot AI-slop comments?

n = 40 diffs, one labeler (Taya, blind). A pilot, not a benchmark.

## Condition: diff_only

| Question | n | Human 'good' rate | Accuracy @0.5 | Cohen's κ | AUC | Brier | Best cut-off | Flags |
|---|---|---|---|---|---|---|---|---|
| no_narration | 40 | 0.60 | 0.72 | 0.37 | 0.95 | 0.15 | 0.89 | kappa 0.37 < 0.4; best cut-off 0.89, not 0.5 |
| density | 40 | 0.70 | 0.75 | 0.22 | 0.85 | 0.18 | 0.89 | kappa 0.22 < 0.4; best cut-off 0.89, not 0.5 |
| format | 33 | 0.97 | 0.88 | -0.05 | 0.91 | 0.08 | 0.62 | kappa -0.05 < 0.4 |
| accurate | 40 | 0.97 | 0.88 | -0.04 | 0.21 | 0.08 | 0.05 | kappa -0.04 < 0.4; best cut-off 0.05, not 0.5 |
| no_placeholder | 40 | 0.88 | 0.85 | 0.17 | 0.80 | 0.11 | 0.94 | kappa 0.17 < 0.4; best cut-off 0.94, not 0.5 |
| explains_why | 40 | 0.42 | 0.40 | -0.05 | 0.25 | 0.42 | 0.57 | kappa -0.05 < 0.4; Brier 0.42 > 0.25 |

**Whole metric (JevEval score) vs 'would you flag it?':** AUC 0.89, best cut-off 0.94 (balanced accuracy 0.83).

## Condition: with_file

| Question | n | Human 'good' rate | Accuracy @0.5 | Cohen's κ | AUC | Brier | Best cut-off | Flags |
|---|---|---|---|---|---|---|---|---|
| no_narration | 40 | 0.60 | 0.72 | 0.37 | 0.95 | 0.14 | 0.85 | kappa 0.37 < 0.4; best cut-off 0.85, not 0.5 |
| density | 40 | 0.70 | 0.78 | 0.32 | 0.85 | 0.17 | 0.94 | kappa 0.32 < 0.4; best cut-off 0.94, not 0.5 |
| format | 34 | 0.97 | 0.88 | -0.05 | 0.88 | 0.09 | 0.73 | kappa -0.05 < 0.4; best cut-off 0.73, not 0.5 |
| accurate | 40 | 0.97 | 0.88 | -0.04 | 0.18 | 0.10 | 0.05 | kappa -0.04 < 0.4; best cut-off 0.05, not 0.5 |
| no_placeholder | 40 | 0.88 | 0.85 | 0.17 | 0.79 | 0.12 | 0.91 | kappa 0.17 < 0.4; best cut-off 0.91, not 0.5 |
| explains_why | 40 | 0.42 | 0.40 | -0.05 | 0.29 | 0.42 | 0.68 | kappa -0.05 < 0.4; Brier 0.42 > 0.25; best cut-off 0.68, not 0.5 |

**Whole metric (JevEval score) vs 'would you flag it?':** AUC 0.86, best cut-off 0.90 (balanced accuracy 0.81).

## Plant check (hand-written diffs only)

| id | planted | Taya overall_slop |
|---|---|---|
| d01 | format_inconsistent | no |
| d03 | misleading | no |
| d05 | clean_why | no |
| d07 | leftover_code | yes |
| d09 | clean_why | no |
| d10 | clean_why | yes |
| d11 | format_malformed | yes |
| d15 | clean_nocomment | no |
| d16 | misleading | yes |
| d18 | clean_why | yes |
| d21 | excessive | yes |
| d23 | excessive | yes |
| d24 | narrating | yes |
| d25 | placeholder | yes |
| d27 | clean_nocomment | no |
| d30 | narrating | yes |
| d31 | clean_nocomment | no |
| d34 | clean_why | no |
| d36 | narrating | yes |
| d39 | format_malformed | no |

## Real model fixes flagged as sloppy by Taya

| model | flagged / n |
|---|---|
| deepseek-ai/DeepSeek-V4-Pro | 0 / 5 |
| google/gemini-3.5-flash | 1 / 5 |
| moonshotai/kimi-k2.7-code | 1 / 5 |
| zai-org/GLM-5.3 | 0 / 5 |
