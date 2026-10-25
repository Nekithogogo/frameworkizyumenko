"""Подключение к базе данных SQLite проекта."""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "certhub.sqlite"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Открыть соединение с базой и включить проверку внешних ключей.

    По умолчанию SQLite не проверяет, что внешний ключ ссылается
    на существующую запись, поэтому PRAGMA выполняется при каждом
    подключении.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы командами из файла sql/schema.sql."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
