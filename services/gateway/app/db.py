import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gateway.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                fields TEXT,
                text TEXT,
                line_items TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_invoice(filename: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO invoices (filename, status) VALUES (?, ?)",
            (filename, "processing"),
        )
        return cursor.lastrowid


def mark_done(invoice_id: int, fields: dict, text: str, line_items: list):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE invoices
            SET status = ?, fields = ?, text = ?, line_items = ?
            WHERE id = ?
            """,
            ("done", json.dumps(fields), text, json.dumps(line_items), invoice_id),
        )


def mark_failed(invoice_id: int, error: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE invoices SET status = ?, error = ? WHERE id = ?",
            ("failed", error, invoice_id),
        )


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "status": row["status"],
        "fields": json.loads(row["fields"]) if row["fields"] else None,
        "text": row["text"],
        "line_items": json.loads(row["line_items"]) if row["line_items"] else None,
        "error": row["error"],
        "created_at": row["created_at"],
    }


def get_invoice(invoice_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        return _row_to_dict(row) if row else None


def list_invoices() -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        return [_row_to_dict(row) for row in rows]
