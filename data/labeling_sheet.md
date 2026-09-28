# Labeling sheet (blind)

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

## d01

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -88,13 +88,15 @@
     data = request.get_json()
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
-    return jsonify({"status": "assigned"})
+    #validate input
+    if not data or "assignee" not in data:
+        return jsonify({"error": "assignee is required"}), 400
+    cur = db.execute(
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        (data["assignee"], ticket_id),
+    )
+    db.commit()
+    if cur.rowcount == 0:   # NOTE: UPDATE ON A MISSING ID DOES NOT RAISE
+        return jsonify({"error": "ticket not found"}), 404
+    return jsonify({"status": "assigned"})  #  success
 
 
```

## d02

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -104,15 +104,8 @@
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
     comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
 
-    full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
-
-    # print("DEBUG ticket:", ticket)
+    full_comments = [{"author": c["author"], "body": c["body"]} for c in comments]
 
     return jsonify({"ticket": dict(ticket), "comments": full_comments})
```

## d03

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -88,12 +88,10 @@
     data = request.get_json()
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
+    # Returns 404 if the ticket does not exist.
+    db.execute(
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        (data["assignee"], ticket_id),
+    )
+    db.commit()
     return jsonify({"status": "assigned"})
 
```

## d04

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,5 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d05

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -88,12 +88,14 @@
     data = request.get_json()
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
+    if not data or "assignee" not in data:
+        return jsonify({"error": "assignee is required"}), 400
+    cur = db.execute(
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        (data["assignee"], ticket_id),
+    )
+    db.commit()
+    # UPDATE on a missing id succeeds silently; rowcount is the only signal.
+    if cur.rowcount == 0:
+        return jsonify({"error": "ticket not found"}), 404
     return jsonify({"status": "assigned"})
 
```

## d06

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,12 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+
+    # Ensure sane values so the OFFSET doesn't go negative.
+    if page < 1:
+        page = 1
+    if page_size < 1:
+        page_size = 10
+
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d07

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -103,14 +103,13 @@
     db = get_db()
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
-    comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+    # comments = db.execute(
+    #     "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+    # ).fetchall()
+    # for c in comments:
+    #     body_row = db.execute("SELECT body FROM comments WHERE id = ?", (c["id"],)).fetchone()
+    rows = db.execute(
+        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
-
-    full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+    full_comments = [{"author": r["author"], "body": r["body"]} for r in rows]
 
     # print("DEBUG ticket:", ticket)
```

## d08

**Task:** Add a PUT /tickets/<id>/close endpoint that marks a ticket as closed.

```diff
--- a/app.py
+++ b/app.py
@@ -99,4 +99,15 @@
 
 
+@app.route("/tickets/<int:ticket_id>/close", methods=["PUT"])
+def close_ticket(ticket_id):
+    db = get_db()
+    db.execute(
+        "UPDATE tickets SET status = 'closed' WHERE id = ?",
+        (ticket_id,),
+    )
+    db.commit()
+    return jsonify({"status": "closed"})
+
+
 @app.route("/tickets/<int:ticket_id>", methods=["GET"])
 def get_ticket(ticket_id):
```

## d09

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -103,14 +103,12 @@
     db = get_db()
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
-    comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
-    ).fetchall()
-
-    full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+    # One query for all comment bodies; the per-comment lookup was N+1 on busy tickets.
+    full_comments = [
+        {"author": c["author"], "body": c["body"]}
+        for c in db.execute(
+            "SELECT author, body FROM comments WHERE ticket_id = ? ORDER BY id",
+            (ticket_id,),
+        ).fetchall()
+    ]
 
     # print("DEBUG ticket:", ticket)
```

## d10

**Task:** The Flask SECRET_KEY is hardcoded in source. Load it from the environment instead.

```diff
--- a/app.py
+++ b/app.py
@@ -1,4 +1,5 @@
 """Ticket API — tracks on-call tickets in sqlite."""
 
+import os
 import sqlite3
 
@@ -6,5 +7,6 @@
 
 app = Flask(__name__)
-app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"
+# Set in the deploy environment; a key in source ships to every clone of the repo.
+app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
 
 DB_PATH = "tickets.db"
```

## d11

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -103,14 +103,14 @@
     db = get_db()
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
-    comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+    rows = db.execute(
+        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
+    """Fetch all comment bodies in one query.
 
-    full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+    Args:
+        ticket_id: the ticket
+    Returns:
+    """
+    full_comments = [{"author": r["author"], "body": r["body"]} for r in rows]
 
     # print("DEBUG ticket:", ticket)
```

## d12

**Task:** Add a POST /tickets/<id>/comments endpoint that adds a comment (author, body) to a ticket.

```diff
--- a/app.py
+++ b/app.py
@@ -99,4 +99,22 @@
 
 
+@app.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
+def add_comment(ticket_id):
+    data = request.get_json()
+    author = data.get("author")
+    body = data.get("body")
+
+    if not author or not body:
+        return jsonify({"error": "author and body are required"}), 400
+
+    db = get_db()
+    cur = db.execute(
+        "INSERT INTO comments (ticket_id, author, body) VALUES (?, ?, ?)",
+        (ticket_id, author, body),
+    )
+    db.commit()
+    return jsonify({"id": cur.lastrowid}), 201
+
+
 @app.route("/tickets/<int:ticket_id>", methods=["GET"])
 def get_ticket(ticket_id):
```

## d13

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -86,14 +86,27 @@
 @app.route("/tickets/<int:ticket_id>/assign", methods=["PUT"])
 def assign_ticket(ticket_id):
-    data = request.get_json()
+    data = request.get_json(silent=True)
+
+    if data is None or "assignee" not in data:
+        return jsonify({"error": "Missing required field 'assignee'"}), 400
+
+    assignee = data["assignee"]
+    if not isinstance(assignee, str):
+        return jsonify({"error": "'assignee' must be a string"}), 400
+
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
+
+    ticket = db.execute(
+        "SELECT id FROM tickets WHERE id = ?", (ticket_id,)
+    ).fetchone()
+    if ticket is None:
+        return jsonify({"error": f"Ticket {ticket_id} not found"}), 404
+
+    db.execute(
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        (assignee, ticket_id),
+    )
+    db.commit()
+
     return jsonify({"status": "assigned"})
 
```

## d14

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,6 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    query = "SELECT * FROM tickets WHERE title LIKE ?"
+    rows = get_db().execute(query, (f"%{q}%",)).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d15

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,5 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d16

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,6 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    # Pages are 0-indexed, so no adjustment is needed here.
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d17

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,8 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?",
+        (f"%{q}%",),
+    ).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d18

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,8 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    # Build the LIKE pattern in Python so user input stays a bound parameter.
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
+    ).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d19

**Task:** Add a POST /tickets/<id>/comments endpoint that adds a comment (author, body) to a ticket.

```diff
--- a/app.py
+++ b/app.py
@@ -99,4 +99,25 @@
 
 
+@app.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
+def add_comment(ticket_id):
+    data = request.get_json(silent=True)
+    if not data or "author" not in data or "body" not in data:
+        return jsonify({"error": "author and body are required"}), 400
+
+    db = get_db()
+    ticket = db.execute(
+        "SELECT id FROM tickets WHERE id = ?", (ticket_id,)
+    ).fetchone()
+    if ticket is None:
+        return jsonify({"error": "ticket not found"}), 404
+
+    cur = db.execute(
+        "INSERT INTO comments (ticket_id, author, body) VALUES (?, ?, ?)",
+        (ticket_id, data["author"], data["body"]),
+    )
+    db.commit()
+    return jsonify({"id": cur.lastrowid, "ticket_id": ticket_id}), 201
+
+
 @app.route("/tickets/<int:ticket_id>", methods=["GET"])
 def get_ticket(ticket_id):
```

## d20

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -86,15 +86,27 @@
 @app.route("/tickets/<int:ticket_id>/assign", methods=["PUT"])
 def assign_ticket(ticket_id):
-    data = request.get_json()
+    data = request.get_json(silent=True)  # returns None if body is not valid JSON
+    if data is None:
+        return jsonify({"error": "Request body must be valid JSON"}), 400
+
+    assignee = data.get("assignee")
+    if not assignee or not isinstance(assignee, str) or not assignee.strip():
+        return jsonify({"error": "Assignee is required and must be a non-empty string"}), 400
+
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
-    return jsonify({"status": "assigned"})
+    cur = db.execute(
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        (assignee, ticket_id),
+    )
+    db.commit()
+
+    if cur.rowcount == 0:
+        return jsonify({"error": "Ticket not found"}), 404
+
+    return jsonify({
+        "status": "assigned",
+        "ticket_id": ticket_id,
+        "assignee": assignee
+    })
 
 
```

## d21

**Task:** PUT /tickets/<id>/assign always returns 'assigned', even when the request body is missing 'assignee' or the ticket does not exist. Make it report errors properly.

```diff
--- a/app.py
+++ b/app.py
@@ -88,12 +88,22 @@
     data = request.get_json()
     db = get_db()
-    try:
-        db.execute(
-            "UPDATE tickets SET assignee = ? WHERE id = ?",
-            (data["assignee"], ticket_id),
-        )
-        db.commit()
-    except Exception:
-        pass
+    # Validate the request body before touching the database.
+    if not data or "assignee" not in data:
+        # Missing assignee is a client error.
+        return jsonify({"error": "assignee is required"}), 400
+    # Run the update statement.
+    cur = db.execute(
+        # SQL to set the assignee on the ticket.
+        "UPDATE tickets SET assignee = ? WHERE id = ?",
+        # Parameters: assignee and ticket id.
+        (data["assignee"], ticket_id),
+    )
+    # Commit the transaction.
+    db.commit()
+    # If no row was updated, the ticket does not exist.
+    if cur.rowcount == 0:
+        # Return a 404 for missing tickets.
+        return jsonify({"error": "ticket not found"}), 404
+    # Otherwise report success.
     return jsonify({"status": "assigned"})
 
```

## d22

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,5 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d23

**Task:** The Flask SECRET_KEY is hardcoded in source. Load it from the environment instead.

```diff
--- a/app.py
+++ b/app.py
@@ -1,10 +1,15 @@
 """Ticket API — tracks on-call tickets in sqlite."""
 
-import sqlite3
+import os  # operating system module
+import sqlite3  # sqlite database
 
 from flask import Flask, g, jsonify, request
 
 app = Flask(__name__)
-app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"
+# Secret key configuration
+# The secret key is read from the environment
+# using os.environ
+# so it is not hardcoded
+app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]  # set the secret key
 
 DB_PATH = "tickets.db"
```

## d24

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,6 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    # calculate the offset
+    offset = (page - 1) * page_size  # subtract one from page and multiply by page size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d25

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,9 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    # TODO: in a real implementation, add proper input validation and sanitization
+    # For simplicity, we just use a parameterized query here.
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
+    ).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d26

**Task:** The Flask SECRET_KEY is hardcoded in source. Load it from the environment instead.

```diff
--- a/app.py
+++ b/app.py
@@ -1,4 +1,5 @@
 """Ticket API — tracks on-call tickets in sqlite."""
 
+import os
 import sqlite3
 
@@ -6,5 +7,5 @@
 
 app = Flask(__name__)
-app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"
+app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24))
 
 DB_PATH = "tickets.db"
```

## d27

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,7 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)
+    ).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d28

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -104,13 +104,10 @@
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
     comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
 
     full_comments = []
     for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+        full_comments.append({"author": c["author"], "body": c["body"]})
 
     # print("DEBUG ticket:", ticket)
```

## d29

**Task:** Add a POST /tickets/<id>/comments endpoint that adds a comment (author, body) to a ticket.

```diff
--- a/app.py
+++ b/app.py
@@ -119,4 +119,16 @@
 
 
+@app.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
+def add_comment(ticket_id):
+    data = request.get_json()
+    db = get_db()
+    cur = db.execute(
+        "INSERT INTO comments (ticket_id, author, body) VALUES (?, ?, ?)",
+        (ticket_id, data["author"], data["body"]),
+    )
+    db.commit()
+    return jsonify({"id": cur.lastrowid}), 201
+
+
 if __name__ == "__main__":
     init_db()
```

## d30

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,9 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    # execute the query with the search term
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?", (f"%{q}%",)  # pass the parameter
+    ).fetchall()
+    # rows now contains the results
     return jsonify([dict(r) for r in rows])
 
```

## d31

**Task:** Remove the leftover debug print in GET /tickets/<id>.

```diff
--- a/app.py
+++ b/app.py
@@ -114,6 +114,4 @@
         full_comments.append({"author": c["author"], "body": body_row["body"]})
 
-    # print("DEBUG ticket:", ticket)
-
     return jsonify({"ticket": dict(ticket), "comments": full_comments})
 
```

## d32

**Task:** GET /tickets/search builds SQL with an f-string from user input (SQL injection). Fix it.

```diff
--- a/app.py
+++ b/app.py
@@ -67,6 +67,8 @@
 def search_tickets():
     q = request.args.get("q", "")
-    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
-    rows = get_db().execute(query).fetchall()
+    rows = get_db().execute(
+        "SELECT * FROM tickets WHERE title LIKE ?",
+        (f"%{q}%",),
+    ).fetchall()
     return jsonify([dict(r) for r in rows])
 
@@ -114,6 +116,4 @@
         full_comments.append({"author": c["author"], "body": body_row["body"]})
 
-    # print("DEBUG ticket:", ticket)
-
     return jsonify({"ticket": dict(ticket), "comments": full_comments})
 
```

## d33

**Task:** Let GET /tickets filter by severity and status via optional query parameters.

```diff
--- a/app.py
+++ b/app.py
@@ -57,8 +57,23 @@
     page_size = int(request.args.get("page_size", 10))
     offset = page * page_size
-    rows = get_db().execute(
-        "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
-        (page_size, offset),
-    ).fetchall()
+
+    severity = request.args.get("severity")
+    status = request.args.get("status")
+
+    query = "SELECT * FROM tickets WHERE 1=1"
+    params = []
+
+    if severity:
+        query += " AND severity = ?"
+        params.append(severity)
+
+    if status:
+        query += " AND status = ?"
+        params.append(status)
+
+    query += " ORDER BY id LIMIT ? OFFSET ?"
+    params.extend([page_size, offset])
+
+    rows = get_db().execute(query, tuple(params)).fetchall()
     return jsonify([dict(r) for r in rows])
 
```

## d34

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,6 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    # `page` is 1-indexed in the public API, so page 1 must start at row 0.
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d35

**Task:** The Flask SECRET_KEY is hardcoded in source. Load it from the environment instead.

```diff
--- a/app.py
+++ b/app.py
@@ -1,4 +1,5 @@
 """Ticket API — tracks on-call tickets in sqlite."""
 
+import os
 import sqlite3
 
@@ -6,5 +7,5 @@
 
 app = Flask(__name__)
-app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"
+app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
 
 DB_PATH = "tickets.db"
```

## d36

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -103,14 +103,14 @@
     db = get_db()
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
-    comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+    # get the comments
+    rows = db.execute(
+        "SELECT author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
-
+    # create a list of comments
     full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+    # loop over the rows
+    for r in rows:
+        # append the comment to the list
+        full_comments.append({"author": r["author"], "body": r["body"]})
 
     # print("DEBUG ticket:", ticket)
```

## d37

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -56,5 +56,5 @@
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d38

**Task:** Add a POST /tickets/<id>/comments endpoint that adds a comment (author, body) to a ticket.

```diff
--- a/app.py
+++ b/app.py
@@ -119,4 +119,36 @@
 
 
+@app.route("/tickets/<int:ticket_id>/comments", methods=["POST"])
+def add_comment(ticket_id):
+    data = request.get_json()
+    if not data:
+        return jsonify({"error": "Invalid JSON"}), 400
+
+    author = data.get("author")
+    body = data.get("body")
+    if not author or not body:
+        return jsonify({"error": "author and body are required"}), 400
+
+    db = get_db()
+    # Optionally verify ticket exists
+    ticket = db.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
+    if not ticket:
+        return jsonify({"error": "Ticket not found"}), 404
+
+    cur = db.execute(
+        "INSERT INTO comments (ticket_id, author, body) VALUES (?, ?, ?)",
+        (ticket_id, author, body),
+    )
+    db.commit()
+    comment_id = cur.lastrowid
+
+    return jsonify({
+        "id": comment_id,
+        "ticket_id": ticket_id,
+        "author": author,
+        "body": body
+    }), 201
+
+
 if __name__ == "__main__":
     init_db()
```

## d39

**Task:** GET /tickets skips the first page of results: page 1 returns rows 11-20 instead of 1-10. Fix the pagination.

```diff
--- a/app.py
+++ b/app.py
@@ -54,7 +54,13 @@
 @app.route("/tickets", methods=["GET"])
 def list_tickets():
+    """
+    list tickets.
+    :param page
+    Returns: JSON
+    @page_size int
+    """
     page = int(request.args.get("page", 1))
     page_size = int(request.args.get("page_size", 10))
-    offset = page * page_size
+    offset = (page - 1) * page_size
     rows = get_db().execute(
         "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
```

## d40

**Task:** GET /tickets/<id> runs one query per comment to fetch comment bodies. Fetch them in a single query.

```diff
--- a/app.py
+++ b/app.py
@@ -104,13 +104,10 @@
     ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
     comments = db.execute(
-        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
+        "SELECT id, author, body FROM comments WHERE ticket_id = ?", (ticket_id,)
     ).fetchall()
 
-    full_comments = []
-    for c in comments:
-        body_row = db.execute(
-            "SELECT body FROM comments WHERE id = ?", (c["id"],)
-        ).fetchone()
-        full_comments.append({"author": c["author"], "body": body_row["body"]})
+    full_comments = [
+        {"author": c["author"], "body": c["body"]} for c in comments
+    ]
 
     # print("DEBUG ticket:", ticket)
```
