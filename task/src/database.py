import sqlite3
from datetime import datetime

DB_PATH = "attendbot.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Создаёт таблицы, если их нет."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id    INTEGER UNIQUE,
                username   TEXT,
                first_name TEXT,
                created_at DATETIME
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(id),
                present    BOOLEAN,
                reason     TEXT,
                asked_at   DATETIME,
                marked_at  DATETIME
            )
        """)
        conn.commit()


def add_user(chat_id: int, username: str, first_name: str):
    """Регистрирует пользователя, если его ещё нет."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (chat_id, username, first_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, username, first_name, datetime.now()),
        )
        conn.commit()


def get_all_chat_ids() -> list[int]:
    """Возвращает chat_id всех зарегистрированных пользователей."""
    with get_connection() as conn:
        rows = conn.execute("SELECT chat_id FROM users").fetchall()
    return [row[0] for row in rows]


def get_user_id_by_chat(chat_id: int) -> int | None:
    """Возвращает внутренний id пользователя по его chat_id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
    return row[0] if row else None


def mark_present(chat_id: int, asked_at: datetime):
    """Сохраняет отметку 'присутствует'."""
    user_id = get_user_id_by_chat(chat_id)
    if user_id is None:
        return
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO attendance (user_id, present, reason, asked_at, marked_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, True, None, asked_at, datetime.now()),
        )
        conn.commit()


def mark_absent(chat_id: int, reason: str, asked_at: datetime):
    """Сохраняет отметку 'отсутствует' с причиной."""
    user_id = get_user_id_by_chat(chat_id)
    if user_id is None:
        return
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO attendance (user_id, present, reason, asked_at, marked_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, False, reason, asked_at, datetime.now()),
        )
        conn.commit()
