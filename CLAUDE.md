# jev-AISlopDetector-eval: project rules

## Project-Specific Constraints
- **Human labels are ground truth.** Taya labels every diff blind. Never score Jev against labels Claude wrote (the plant key is a sanity check on the dataset, not ground truth).
- **Keep the plant key hidden until labeling is done.** `data/plant_key.json` is gitignored until Taya's labels are in; don't paste its contents in chat before then. Un-ignore and commit it after.
- **JevEval Noul = P(true) is scored as good.** Phrase every Noul so "true" means clean comments. Choice credits: 1.0 = best.
- **Never print or log API keys.** `.env` holds TYPESAFE_API_KEY and GMI_* copied from jevathon/backend/.env (hackathon credits, Taya approved 2026-09-28).
- **Real-model diffs:** GMI first; if GMI fails, Claude Haiku (`claude-haiku-4-5-20251001`) on Taya's ANTHROPIC_API_KEY.
- Report numbers with n and one-labeler caveat; 40 diffs is a pilot, not a benchmark.
