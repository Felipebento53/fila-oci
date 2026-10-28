import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"

def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connection() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                event_type TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
        """)

def log_event(order_id, event_type, detail=""):
    init_db()
    with connection() as con:
        con.execute(
            "INSERT INTO events(order_id,event_type,detail,created_at) VALUES(?,?,?,?)",
            (order_id, event_type, detail, datetime.now(timezone.utc).isoformat())
        )

def recent_events(limit=30):
    init_db()
    with connection() as con:
        rows = con.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def metrics():
    init_db()
    with connection() as con:
        sent = con.execute("SELECT COUNT(*) FROM events WHERE event_type='ENVIADO'").fetchone()[0]
        processed = con.execute("SELECT COUNT(*) FROM events WHERE event_type='PROCESSADO'").fetchone()[0]
        failed = con.execute("SELECT COUNT(*) FROM events WHERE event_type='ERRO'").fetchone()[0]
        received = con.execute("SELECT COUNT(*) FROM events WHERE event_type='RECEBIDO'").fetchone()[0]
    return {"sent": sent, "processed": processed, "failed": failed, "received": received}
