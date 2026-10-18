from datetime import date

import pytest

from certificates import (
    get_certificate_status,
    get_days_left,
    get_expiring_certificates,
    get_expiry_date,
    get_status,
    is_valid_term,
    issue_certificate,
    renew_certificate,
    revoke_certificate,
)
from domains import add_domain

START = date(2026, 1, 1)


def make_data() -> tuple[dict[int, dict], list[dict]]:
    domains: dict[int, dict] = {}
    add_domain(domains, "example.ru", "ООО «Ромашка»")
    return domains, []


def test_term_and_expiry():
    assert is_valid_term(398)
    assert not is_valid_term(399)
    assert get_expiry_date(START, 365) == date(2027, 1, 1)
    assert get_days_left(date(2026, 1, 11), START) == 10


def test_certificate_status_text():
    assert get_certificate_status(-1) == "Сертификат истек"
    assert "скоро" in get_certificate_status(30)
    assert get_certificate_status(31) == "Сертификат действителен"


def test_issue_certificate():
    domains, certificates = make_data()
    certificate = issue_certificate(domains, certificates, 1, "DV",
                                    START, 365)
    assert certificate["serial_number"] == "CH-000001"
    assert certificate["valid_to"] == "2027-01-01"
    assert get_status(certificate, date(2026, 6, 1)) == "active"
    assert get_status(certificate, date(2026, 12, 15)) == "expiring"
    assert get_status(certificate, date(2027, 2, 1)) == "expired"


def test_overlapping_certificate_forbidden():
    domains, certificates = make_data()
    issue_certificate(domains, certificates, 1, "DV", START, 365)
    with pytest.raises(ValueError):
        issue_certificate(domains, certificates, 1, "OV",
                          date(2026, 6, 1), 30)


def test_invalid_term_and_type_forbidden():
    domains, certificates = make_data()
    with pytest.raises(ValueError):
        issue_certificate(domains, certificates, 1, "DV", START, 400)
    with pytest.raises(ValueError):
        issue_certificate(domains, certificates, 1, "XX", START, 30)


def test_revoked_certificate_does_not_block_domain():
    domains, certificates = make_data()
    issue_certificate(domains, certificates, 1, "DV", START, 365)
    assert revoke_certificate(certificates, 1)
    assert not revoke_certificate(certificates, 1)
    assert get_status(certificates[0], START) == "revoked"
    issue_certificate(domains, certificates, 1, "DV", START, 365)
    assert len(certificates) == 2


def test_renew_certificate_starts_after_old_one():
    domains, certificates = make_data()
    issue_certificate(domains, certificates, 1, "DV", START, 365)
    renewed = renew_certificate(domains, certificates, 1, 90)
    assert renewed["valid_from"] == "2027-01-02"
    assert renewed["cert_type"] == "DV"


def test_expiring_certificates():
    domains, certificates = make_data()
    issue_certificate(domains, certificates, 1, "DV", START, 365)
    assert list(get_expiring_certificates(certificates,
                                          date(2026, 12, 20))) == certificates
    assert list(get_expiring_certificates(certificates, START)) == []
