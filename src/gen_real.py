"""Real AI-written fixes: several models each fix the demo repo's seeded bugs.

The prompt never mentions comments, so whatever commenting style shows up is the
model's own habit. That is the behaviour the eval is about.
Writes data/raw_real.jsonl: one record per (model, issue) with the unified diff.
"""

import difflib
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
BASE = (ROOT / "data" / "base_app.py").read_text()

ISSUES = {
    "secret": "The Flask SECRET_KEY is hardcoded in source. Load it from the environment instead.",
    "pagination": "GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.",
    "sqli": "GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.",
    "swallowed_error": "PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.",
    "n_plus_one": "GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.",
}

# New code attracts comments/docstrings far more than one-line fixes (bug fixes above
# came back almost comment-free), so the real half also includes small features.
FEATURES = {
    "feat_close": "Add a PUT /tickets/<id>/close endpoint that marks a ticket as closed.",
    "feat_comment": "Add a POST /tickets/<id>/comments endpoint that adds a comment (author, body) to a ticket.",
    "feat_filter": "Let GET /tickets filter by severity and status via optional query parameters.",
}

GMI_MODELS = [
    "zai-org/GLM-5.3",
    "deepseek-ai/DeepSeek-V4-Pro",
    "moonshotai/kimi-k2.7-code",
    "google/gemini-3.5-flash",
]
HAIKU = "claude-haiku-4-5-20251001"

PROMPT = """You are working on this Flask app.

Task: {issue}

app.py:
```python
{code}
```

Return the complete updated app.py in a single ```python code block."""


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    if not m:
        raise ValueError("no code block in model output")
    return m.group(1)


def to_diff(new: str) -> str:
    return "".join(
        difflib.unified_diff(
            BASE.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile="a/app.py", tofile="b/app.py", n=2,
        )
    )


def gmi_generate(model: str, prompt: str) -> str:
    client = OpenAI(api_key=os.environ["GMI_API_KEY"], base_url=os.environ["GMI_BASE_URL"])
    r = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=4000
    )
    return r.choices[0].message.content


def haiku_generate(prompt: str) -> str:
    import anthropic

    r = anthropic.Anthropic().messages.create(
        model=HAIKU, max_tokens=4000, messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text


def main() -> None:
    out = ROOT / "data" / "raw_real.jsonl"
    done = set()
    if out.exists():
        done = {(r["model"], r["issue"]) for r in map(json.loads, out.read_text().splitlines())}
    with out.open("a") as f:
        for model in GMI_MODELS:
            for issue, text in {**ISSUES, **FEATURES}.items():
                if (model, issue) in done:
                    continue
                prompt = PROMPT.format(issue=text, code=BASE)
                source = model
                try:
                    reply = gmi_generate(model, prompt)
                except Exception as e:  # noqa: BLE001 - fallback is logged, never silent
                    print(f"ERROR GMI {model}/{issue}: {e} -> falling back to {HAIKU}", file=sys.stderr)
                    reply, source = haiku_generate(prompt), HAIKU
                try:
                    diff = to_diff(extract_code(reply))
                except ValueError as e:
                    print(f"ERROR {source}/{issue}: {e}; skipped", file=sys.stderr)
                    continue
                if not diff:
                    print(f"ERROR {source}/{issue}: empty diff; skipped", file=sys.stderr)
                    continue
                f.write(json.dumps({"model": source, "requested_model": model, "issue": issue,
                                    "issue_text": text, "diff": diff, "new_code": extract_code(reply)}) + "\n")
                f.flush()
                print(f"ok {source} {issue} ({diff.count(chr(10))} diff lines)")


if __name__ == "__main__":
    main()
