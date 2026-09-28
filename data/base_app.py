"""Ticket API — tracks on-call tickets in sqlite."""

import sqlite3

from flask import Flask, g, jsonify, request

app = Flask(__name__)
app.config["SECRET_KEY"] = "sk_live_49fa8b2c1e0d4477"

DB_PATH = "tickets.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            assignee TEXT,
            status TEXT NOT NULL DEFAULT 'open'
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL
        )
        """
    )
    db.commit()
    db.close()


@app.route("/tickets", methods=["GET"])
def list_tickets():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    offset = page * page_size
    rows = get_db().execute(
        "SELECT * FROM tickets ORDER BY id LIMIT ? OFFSET ?",
        (page_size, offset),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/tickets/search", methods=["GET"])
def search_tickets():
    q = request.args.get("q", "")
    query = f"SELECT * FROM tickets WHERE title LIKE '%{q}%'"
    rows = get_db().execute(query).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()
    db = get_db()
    cur = db.execute(
        "INSERT INTO tickets (title, severity, status) VALUES (?, ?, 'open')",
        (data["title"], data.get("severity", "medium")),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid}), 201


@app.route("/tickets/<int:ticket_id>/assign", methods=["PUT"])
def assign_ticket(ticket_id):
    data = request.get_json()
    db = get_db()
    try:
        db.execute(
            "UPDATE tickets SET assignee = ? WHERE id = ?",
            (data["assignee"], ticket_id),
        )
        db.commit()
    except Exception:
        pass
    return jsonify({"status": "assigned"})


@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    db = get_db()
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    comments = db.execute(
        "SELECT id, author FROM comments WHERE ticket_id = ?", (ticket_id,)
    ).fetchall()

    full_comments = []
    for c in comments:
        body_row = db.execute(
            "SELECT body FROM comments WHERE id = ?", (c["id"],)
        ).fetchone()
        full_comments.append({"author": c["author"], "body": body_row["body"]})

    # print("DEBUG ticket:", ticket)

    return jsonify({"ticket": dict(ticket), "comments": full_comments})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
