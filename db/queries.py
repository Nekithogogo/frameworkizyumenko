"""Именованные SQL-запросы проекта из файла sql/queries.sql.

Каждый запрос в файле начинается строкой «-- name: <имя>». Модуль
читает файл и позволяет выполнить запрос по имени, передав значения
именованными параметрами. Проверить все запросы на текущей базе:

    python -m db.queries
"""
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Mapping, Optional

from db.database import BASE_DIR, get_connection

QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"
NAME_PATTERN = re.compile(r"^-- name: (\w+)[ \t]*$", re.MULTILINE)


def load_queries(filename: Path = QUERIES_FILE) -> dict[str, str]:
    """Прочитать файл запросов и вернуть словарь «имя → текст запроса»."""
    parts = NAME_PATTERN.split(filename.read_text(encoding="utf-8"))
    # parts: [заголовок файла, имя_1, запрос_1, имя_2, запрос_2, ...]
    return {
        name: body.strip()
        for name, body in zip(parts[1::2], parts[2::2])
    }


QUERIES = load_queries()


def fetch_all(
    name: str,
    params: Optional[Mapping[str, object]] = None,
) -> list[sqlite3.Row]:
    """Выполнить запрос и вернуть все строки результата.

    sqlite3.Row позволяет обращаться к полям по именам:
    row["name"] в Python и {{ row.name }} в шаблоне Django.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(QUERIES[name], params or {}).fetchall()
    finally:
        conn.close()


def fetch_one(
    name: str,
    params: Optional[Mapping[str, object]] = None,
) -> Optional[sqlite3.Row]:
    """Выполнить запрос и вернуть первую строку или None."""
    rows = fetch_all(name, params)
    return rows[0] if rows else None


def main() -> None:
    """Выполнить все запросы файла с тестовыми параметрами и вывести итог."""
    today = date.today().isoformat()
    params = {"today": today, "date": today, "id": 3, "days": 30,
              "min_domains": 2}
    print(f"Параметры: {params}")
    for name in QUERIES:
        rows = fetch_all(name, params)
        print(f"\n== {name}: {len(rows)} строк")
        for row in rows:
            print("  ", tuple(row))


if __name__ == "__main__":
    main()
