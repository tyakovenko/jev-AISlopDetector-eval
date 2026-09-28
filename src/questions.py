"""The comment-slop metric: six JevEval questions about comments added in a diff.

JevEval scores a Noul as P(true) and a Choice by option credit, so every question
is phrased so that "true" / credit 1.0 means clean comments. A diff that adds no
comments passes the comment-content questions: silence is not slop.
"""

from deepeval.metrics import JevEval
from deepeval.metrics.jev_eval.questions import Choice, Noul
from deepeval.test_case import SingleTurnParams

# Keys are stable ids used to join Jev's answers to Taya's labels (labels.csv columns).
QUESTIONS = {
    "no_narration": Noul(
        "Every comment added in the diff in `actual_output` explains intent, a constraint, or "
        "the reason for the code; none of them just restates what the code on the adjacent "
        "line already says (for example '# increment i' above 'i += 1'). If the diff adds no "
        "comments, this is true."
    ),
    "density": Choice(
        "How dense are the comments added in the diff in `actual_output`?",
        options={
            "no_comments_added": 1.0,
            "appropriate": 1.0,  # comments only where the code needs them
            "excessive": 0.0,  # a comment on most lines, or several on self-explanatory code
        },
    ),
    "format": Choice(
        "How are the comments and docstrings added in the diff in `actual_output` formatted, "
        "compared with each other and with the existing code? consistent: same style as the "
        "surrounding code and well-formed. inconsistent: mixed styles, such as different "
        "docstring conventions, capitalization, spacing after '#', or inline versus block "
        "comments for the same kind of note. malformed: broken or misplaced, such as a "
        "docstring that is not the first statement, a comment on the wrong line, or text "
        "that is cut off.",
        options={
            "consistent": 1.0,
            "inconsistent": 0.3,
            "malformed": 0.0,
            "no_comments_added": None,  # not applicable: nothing to format
        },
    ),
    "accurate": Noul(
        "Every comment and docstring added in the diff in `actual_output` accurately describes "
        "what the changed code actually does. If the diff adds no comments, this is true."
    ),
    "no_placeholder": Noul(
        "The diff in `actual_output` adds no placeholder or hedging comments (such as 'in a "
        "real implementation', 'for simplicity', or a TODO with no owner or reason) and leaves "
        "no commented-out code behind."
    ),
    "explains_why": Noul(
        "Wherever the change in `actual_output` does something a reader could not understand "
        "from the code alone, a comment explains why. If nothing in the change is non-obvious, "
        "this is true."
    ),
}

QUESTION_IDS = list(QUESTIONS)


def build_metric(with_file_context: bool = False) -> JevEval:
    # Condition B adds the full post-change file as `context`, testing the jevathon
    # finding that questions fail when Jev never sees what they refer to.
    params = [SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT]
    if with_file_context:
        params.append(SingleTurnParams.CONTEXT)
    return JevEval(
        name="Comment slop" + (" (+file)" if with_file_context else ""),
        evaluation_params=params,
        questions=list(QUESTIONS.values()),
        async_mode=False,
    )
