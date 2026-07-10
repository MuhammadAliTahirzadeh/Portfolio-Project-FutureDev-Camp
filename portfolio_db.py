import sqlite3
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "portfolio.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_connection()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def seed_projects():
    with closing(get_connection()) as conn, conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM projects").fetchone()["count"]
        if count == 0:
            default_projects = [
                (
                    "Portfolio Website",
                    "A polished personal portfolio built with Flask and Jinja2.",
                    "This project shows how a personal brand can be presented through a clean and responsive Flask experience.",
                ),
                (
                    "Basic Backend App",
                    "A simple Flask application for routes, responses, and render logic.",
                    "The app demonstrates the core structure of a lightweight backend experience.",
                ),
            ]
            conn.executemany(
                "INSERT INTO projects (title, summary, description) VALUES (?, ?, ?)",
                default_projects,
            )
            conn.commit()


def get_projects():
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT id, title, summary, description, created_at FROM projects ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_project(project_id):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT id, title, summary, description, created_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None


def create_project(title, summary, description):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO projects (title, summary, description) VALUES (?, ?, ?)",
            (title, summary, description),
        )
        conn.commit()
        return cursor.lastrowid


def update_project(project_id, title, summary, description):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "UPDATE projects SET title = ?, summary = ?, description = ? WHERE id = ?",
            (title, summary, description, project_id),
        )
        return cursor.rowcount


def delete_project(project_id):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount


def get_messages():
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT id, name, email, message, status, created_at FROM messages ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def create_message(name, email, message):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message),
        )
        conn.commit()
        return cursor.lastrowid


def update_message(message_id, message_text, status):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "UPDATE messages SET message = ?, status = ? WHERE id = ?",
            (message_text, status, message_id),
        )
        return cursor.rowcount


def delete_message(message_id):
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        return cursor.rowcount
