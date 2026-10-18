import json
from datetime import date
from pathlib import Path

from models import Organization
from storage import (
    load_certificates,
    load_data,
    load_domains,
    read_json,
    save_data,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROMASHKA = Organization(1, "ООО «Ромашка»", "7701234567", "a@a.ru")


def write(path, data) -> str:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_load_restores_links(tmp_path):
    domains = load_domains(
        write(tmp_path / "domains.json",
              [{"id": 1, "name": "example.ru", "organization_id": 1}]),
        [ROMASHKA],
    )
    certificates = load_certificates(
        write(tmp_path / "certificates.json", [{
            "id": 1, "serial_number": "CH-000001", "cert_type": "DV",
            "domain_id": 1, "organization_id": 1,
            "valid_from": "2026-01-01", "valid_to": "2027-01-01",
            "is_revoked": False,
        }]),
        domains, [ROMASHKA],
    )
    assert domains[0].organization is ROMASHKA
    assert certificates[0].domain is domains[0]
    assert certificates[0].validity.valid_to == date(2027, 1, 1)


def test_records_with_unknown_links_are_skipped(tmp_path):
    filename = write(tmp_path / "domains.json",
                     [{"id": 1, "name": "example.ru", "organization_id": 9}])
    assert load_domains(filename, [ROMASHKA]) == []


def test_save_and_load_data_roundtrip(tmp_path):
    organizations, domains, certificates = load_data(DATA_DIR)
    save_data(tmp_path, organizations, domains, certificates)
    assert read_json(str(tmp_path / "certificates.json")) == read_json(
        str(DATA_DIR / "certificates.json")
    )
    loaded = load_data(tmp_path)
    assert [len(items) for items in loaded] == [
        len(organizations), len(domains), len(certificates)
    ]


def test_missing_and_broken_files(tmp_path):
    assert read_json(str(tmp_path / "missing.json")) == []
    broken = tmp_path / "broken.json"
    broken.write_text("[{", encoding="utf-8")
    assert read_json(str(broken)) == []
