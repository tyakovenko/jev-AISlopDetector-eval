"""Hand-written diffs: clean fixes plus fixes with one planted comment problem.

Each variant is a list of (old, new) replacements on the demo app. `plant` is what
was planted; it goes to data/plant_key.json (hidden from the labeler), never to the
labeling sheet. Taya's blind labels are the ground truth; the plant key only checks
that the planted problem is what a reader sees.
"""

import json
from pathlib import Path

from gen_real import BASE, ISSUES, to_diff

ROOT = Path(__file__).resolve().parent.parent

SECRET_OLD = 'app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"'
PAGE_OLD = "    offset = page * page_size\n"
SQLI_OLD = """    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
    rows = get_db().execute(query).fetchall()
"""
ASSIGN_OLD = """    try:
        db.execute(
            "UPDATE tickets SET assignee = ? WHERE id = ?",
            (data["assignee"], ticket_id),
        )
        db.commit()
    except Exception:
        pass
    return jsonify({"status": "assigned"})
"""
N1_OLD = """    comments = db.execute(
        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
    ).fetchall()

    full_comments = []
    for c in comments:
        body_row = db.execute(
            "SELECT body FROM comments WHERE id = ?", (c["id"],)
        ).fetchone()
        full_comments.append({"author": c["author"], "body": body_row["body"]})
"""
DEBUG_OLD = '    # print("DEBUG ticket:", ticket)\n\n'
IMPORT_OLD = "import sqlite3\n"

VARIANTS = [
    # ---- clean, with a comment that explains why ----
    ("secret", "clean_why", [(IMPORT_OLD, "import os\nimport sqlite3\n"),
        (SECRET_OLD, '# Set in the deploy environment; a key in source ships to every clone of the repo.\napp.config["SECRET_KEY"] = os.environ["SECRET_KEY"]')]),
    ("pagination", "clean_why", [(PAGE_OLD, "    # `page` is 1-indexed in the public API, so page 1 must start at row 0.\n    offset = (page - 1) * page_size\n")]),
    ("sqli", "clean_why", [(SQLI_OLD, """    # Build the LIKE pattern in Python so user input stays a bound parameter.
    rows = get_db().execute(
        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
    ).fetchall()
""")]),
    ("swallowed_error", "clean_why", [(ASSIGN_OLD, """    if not data or "assignee" not in data:
        return jsonify({"error": "assignee is required"}), 400
    cur = db.execute(
        "UPDATE tickets SET assignee = ? WHERE id = ?",
        (data["assignee"], ticket_id),
    )
    db.commit()
    # UPDATE on a missing id succeeds silently; rowcount is the only signal.
    if cur.rowcount == 0:
        return jsonify({"error": "ticket not found"}), 404
    return jsonify({"status": "assigned"})
""")]),
    ("n_plus_one", "clean_why", [(N1_OLD, """    # One query for all comment bodies; the per-comment lookup was N+1 on busy tickets.
    full_comments = [
        {"author": c["author"], "body": c["body"]}
        for c in db.execute(
            "SELECT author, body FROM comments WHERE ticket_id = ? ORDER BY id",
            (ticket_id,),
        ).fetchall()
    ]
""")]),
    # ---- clean, no comments needed ----
    ("pagination", "clean_nocomment", [(PAGE_OLD, "    offset = (page - 1) * page_size\n")]),
    ("sqli", "clean_nocomment", [(SQLI_OLD, """    rows = get_db().execute(
        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
    ).fetchall()
""")]),
    ("debug_print", "clean_nocomment", [(DEBUG_OLD, "")]),
    # ---- narrating comments ----
    ("pagination", "narrating", [(PAGE_OLD, "    # calculate the offset\n    offset = (page - 1) * page_size  # subtract one from page and multiply by page size\n")]),
    ("sqli", "narrating", [(SQLI_OLD, """    # execute the query with the search term
    rows = get_db().execute(
        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)  # pass the parameter
    ).fetchall()
    # rows now contains the results
""")]),
    ("n_plus_one", "narrating", [(N1_OLD, """    # get the comments
    rows = db.execute(
        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
    ).fetchall()
    # create a list of comments
    full_comments = []
    # loop over the rows
    for r in rows:
        # append the comment to the list
        full_comments.append({"author": r["author"], "body": r["body"]})
""")]),
    # ---- excessive: a comment on nearly every line ----
    ("swallowed_error", "excessive", [(ASSIGN_OLD, """    # Validate the request body before touching the database.
    if not data or "assignee" not in data:
        # Missing assignee is a client error.
        return jsonify({"error": "assignee is required"}), 400
    # Run the update statement.
    cur = db.execute(
        # SQL to set the assignee on the ticket.
        "UPDATE tickets SET assignee = ? WHERE id = ?",
        # Parameters: assignee and ticket id.
        (data["assignee"], ticket_id),
    )
    # Commit the transaction.
    db.commit()
    # If no row was updated, the ticket does not exist.
    if cur.rowcount == 0:
        # Return a 404 for missing tickets.
        return jsonify({"error": "ticket not found"}), 404
    # Otherwise report success.
    return jsonify({"status": "assigned"})
""")]),
    ("secret", "excessive", [(IMPORT_OLD, "import os  # operating system module\nimport sqlite3  # sqlite database\n"),
        (SECRET_OLD, '# Secret key configuration\n# The secret key is read from the environment\n# using os.environ\n# so it is not hardcoded\napp.config["SECRET_KEY"] = os.environ["SECRET_KEY"]  # set the secret key')]),
    # ---- inconsistent / malformed format ----
    ("swallowed_error", "format_inconsistent", [(ASSIGN_OLD, """    #validate input
    if not data or "assignee" not in data:
        return jsonify({"error": "assignee is required"}), 400
    cur = db.execute(
        "UPDATE tickets SET assignee = ? WHERE id = ?",
        (data["assignee"], ticket_id),
    )
    db.commit()
    if cur.rowcount == 0:   # NOTE: UPDATE ON A MISSING ID DOES NOT RAISE
        return jsonify({"error": "ticket not found"}), 404
    return jsonify({"status": "assigned"})  #  success
""")]),
    ("n_plus_one", "format_malformed", [(N1_OLD, """    rows = db.execute(
        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
    ).fetchall()
    \"\"\"Fetch all comment bodies in one query.

    Args:
        ticket_id: the ticket
    Returns:
    \"\"\"
    full_comments = [{"author": r["author"], "body": r["body"]} for r in rows]
""")]),
    ("pagination", "format_malformed", [("def list_tickets():\n", 'def list_tickets():\n    """\n    list tickets.\n    :param page\n    Returns: JSON\n    @page_size int\n    """\n'),
        (PAGE_OLD, "    offset = (page - 1) * page_size\n")]),
    # ---- misleading / stale ----
    ("swallowed_error", "misleading", [(ASSIGN_OLD, """    # Returns 404 if the ticket does not exist.
    db.execute(
        "UPDATE tickets SET assignee = ? WHERE id = ?",
        (data["assignee"], ticket_id),
    )
    db.commit()
    return jsonify({"status": "assigned"})
""")]),
    ("pagination", "misleading", [(PAGE_OLD, "    # Pages are 0-indexed, so no adjustment is needed here.\n    offset = (page - 1) * page_size\n")]),
    # ---- placeholder / leftover ----
    ("sqli", "placeholder", [(SQLI_OLD, """    # TODO: in a real implementation, add proper input validation and sanitization
    # For simplicity, we just use a parameterized query here.
    rows = get_db().execute(
        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
    ).fetchall()
""")]),
    ("n_plus_one", "leftover_code", [(N1_OLD, """    # comments = db.execute(
    #     "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
    # ).fetchall()
    # for c in comments:
    #     body_row = db.execute("SELECT body FROM comments WHERE id = ?", (c["id"],)).fetchone()
    rows = db.execute(
        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
    ).fetchall()
    full_comments = [{"author": r["author"], "body": r["body"]} for r in rows]
""")]),
]

ISSUE_TEXT = dict(ISSUES, debug_print="Remove the leftover debug print in GET /tickets/<id>.")


def main() -> None:
    out = ROOT / "data" / "raw_written.jsonl"
    with out.open("w") as f:
        for issue, plant, reps in VARIANTS:
            code = BASE
            for old, new in reps:
                if old not in code:
                    raise ValueError(f"{issue}/{plant}: replacement target not found")
                code = code.replace(old, new, 1)
            f.write(json.dumps({"model": "handwritten", "issue": issue, "issue_text": ISSUE_TEXT[issue],
                                "plant": plant, "diff": to_diff(code), "new_code": code}) + "\n")
    print(f"wrote {len(VARIANTS)} written diffs")


if __name__ == "__main__":
    main()
