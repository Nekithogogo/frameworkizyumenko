"""Перенос данных проекта из JSON-файлов в базу данных SQLite.

Запуск из корня проекта:

    python -m db.import_json

Скрипт создает таблицы (если их еще нет), очищает их и заново
заполняет данными из data/*.json, поэтому его можно запускать повторно.
"""
import json
import sqlite3

from db.database import BASE_DIR, create_schema, get_connection

DATA_DIR = BASE_DIR / "data"
ORGANIZATIONS_FILE = DATA_DIR / "organizations.json"
DOMAINS_FILE = DATA_DIR / "domains.json"
CERTIFICATES_FILE = DATA_DIR / "certificates.json"


def load_json(filename) -> list:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Удалить старые записи: сначала зависимые таблицы, потом главные."""
    for table in ("certificates", "domains", "organizations"):
        conn.execute(f"DELETE FROM {table}")  # имя таблицы — из кода


def import_organizations(conn: sqlite3.Connection) -> None:
    """Перенести организации."""
    conn.executemany(
        """
        INSERT INTO organizations (id, name, inn, email)
        VALUES (?, ?, ?, ?)
        """,
        [
            (item["id"], item["name"], item["inn"], item["email"])
            for item in load_json(ORGANIZATIONS_FILE)
        ],
    )


def import_domains(conn: sqlite3.Connection) -> None:
    """Перенести домены."""
    conn.executemany(
        """
        INSERT INTO domains (id, name, organization_id)
        VALUES (?, ?, ?)
        """,
        [
            (item["id"], item["name"], item["organization_id"])
            for item in load_json(DOMAINS_FILE)
        ],
    )


def import_certificates(conn: sqlite3.Connection) -> None:
    """Перенести сертификаты; логическое is_revoked хранится как 0/1."""
    conn.executemany(
        """
        INSERT INTO certificates (
            id, serial_number, cert_type, domain_id, organization_id,
            valid_from, valid_to, is_revoked
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item["serial_number"],
                item["cert_type"],
                item["domain_id"],
                item["organization_id"],
                item["valid_from"],
                item["valid_to"],
                int(item["is_revoked"]),
            )
            for item in load_json(CERTIFICATES_FILE)
        ],
    )


def count_rows(conn: sqlite3.Connection) -> dict[str, int]:
    """Посчитать записи в каждой таблице."""
    return {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("organizations", "domains", "certificates")
    }


def main() -> None:
    """Создать таблицы и перенести в них данные одной транзакцией."""
    conn = get_connection()
    try:
        create_schema(conn)
        clear_tables(conn)
        import_organizations(conn)
        import_domains(conn)
        import_certificates(conn)
        conn.commit()
        print("Импорт завершен:", count_rows(conn))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
