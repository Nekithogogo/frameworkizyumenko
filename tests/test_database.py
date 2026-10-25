"""Проверка базы данных SQLite, импорта из JSON и SQL-запросов."""
import sqlite3
from datetime import date

import pytest

from db import import_json
from db.database import get_connection
from db.queries import QUERIES, fetch_all, fetch_one, load_queries
from storage import load_data

pytestmark = pytest.mark.usefixtures("sqlite_db")

TODAY = "2026-10-25"
ALL_PARAMS = {"today": TODAY, "date": TODAY, "id": 1, "days": 30,
              "min_domains": 2}


def test_tables_created():
    conn = get_connection()
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    conn.close()
    assert tables == {"organizations", "domains", "certificates"}


def test_foreign_keys_declared_and_enforced():
    conn = get_connection()
    links = {
        row[2] for row in conn.execute("PRAGMA foreign_key_list(certificates)")
    }
    assert links == {"domains", "organizations"}
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO domains (id, name, organization_id) "
            "VALUES (?, ?, ?)",
            (100, "orphan.ru", 999),
        )
    conn.close()


def test_import_copies_all_json_records():
    organizations, domains, certificates = load_data(import_json.DATA_DIR)
    conn = get_connection()
    assert import_json.count_rows(conn) == {
        "organizations": len(organizations),
        "domains": len(domains),
        "certificates": len(certificates),
    }
    conn.close()


def test_import_can_be_repeated():
    import_json.main()
    assert fetch_one("summary")["certificates_count"] == 6


def test_queries_file_has_enough_queries():
    def queries_with(keyword: str) -> int:
        return sum(keyword in query.upper() for query in QUERIES.values())

    assert len(QUERIES) >= 10
    for keyword in ("WHERE", "JOIN", "COUNT(", "GROUP BY"):
        assert queries_with(keyword) >= 2, keyword
    assert queries_with("HAVING") >= 1
    assert load_queries() == QUERIES


@pytest.mark.parametrize("name", list(QUERIES))
def test_every_query_runs(name):
    fetch_all(name, ALL_PARAMS)


@pytest.mark.parametrize("today", [
    date(2025, 12, 1), date(2026, 6, 1), date(2026, 10, 25),
    date(2026, 12, 1), date(2027, 7, 1),
])
def test_sql_status_matches_python_model(today):
    _, _, certificates = load_data(import_json.DATA_DIR)
    expected = {c.id: c.get_status(today) for c in certificates}
    rows = fetch_all("certificate_list", {"today": today.isoformat()})
    assert {row["id"]: row["status"] for row in rows} == expected


def test_unprotected_domains_on_date():
    rows = fetch_all("unprotected_domains", {"date": TODAY})
    assert [row["name"] for row in rows] == [
        "ivanov-blog.ru", "mail.techno.com"
    ]


def test_expiring_certificates_within_days():
    rows = fetch_all("expiring_certificates", {"today": TODAY, "days": 30})
    assert [row["serial_number"] for row in rows] == ["CH-000002"]
    assert rows[0]["days_left"] == 11
    assert fetch_all("expiring_certificates",
                     {"today": TODAY, "days": 5}) == []


def test_domain_list_group_by():
    rows = {row["name"]: row for row in
            fetch_all("domain_list", {"today": TODAY})}
    assert rows["api.techno.com"]["certificates_count"] == 2
    assert rows["api.techno.com"]["protected_until"] == "2027-06-02"
    assert rows["mail.techno.com"]["protected_until"] is None


def test_statistics_queries():
    statuses = {row["status"]: row["certificates_count"] for row in
                fetch_all("status_counts", {"today": TODAY})}
    assert statuses == {"active": 2, "expired": 2, "expiring": 1,
                        "revoked": 1}
    types = {row["cert_type"]: row["certificates_count"]
             for row in fetch_all("type_statistics")}
    assert types == {"DV": 3, "EV": 2, "OV": 1}
    large = fetch_all("large_organizations", {"min_domains": 2})
    assert {row["name"] for row in large} == {"ООО «Ромашка»", "АО «Техно»"}
    assert fetch_all("large_organizations", {"min_domains": 3}) == []


def test_parameters_are_not_part_of_sql_text():
    # Значение с кавычкой не ломает запрос: оно передается параметром.
    rows = fetch_all("unprotected_domains", {"date": "x' OR 1=1 --"})
    assert len(rows) == 5
    assert fetch_one("domain_detail", {"id": "1 OR 1=1",
                                       "today": TODAY}) is None
