from datetime import date

import pytest

from models import Certificate, Domain, Entity, Organization, Validity
from models.certificates import (
    get_certificate_status,
    get_current_certificate,
    get_expiring_certificates,
    issue_certificate,
    renew_certificate,
    revoke_certificate,
    sort_certificates_by_expiry,
)

START = date(2026, 1, 1)
ROMASHKA = Organization(1, "ООО «Ромашка»", "7701234567", "a@a.ru")
TECHNO = Organization(2, "АО «Техно»", "7812345678", "b@b.ru")


def make_domain() -> Domain:
    return Domain(1, "example.ru", ROMASHKA)


def test_certificate_creation_links_objects():
    domain = make_domain()
    validity = Validity.from_days(START, 365)
    certificate = Certificate(1, "CH-000001", "DV", domain, ROMASHKA,
                              validity)
    assert certificate.domain is domain
    assert certificate.organization is ROMASHKA
    assert certificate.validity is validity
    assert not certificate.is_revoked
    assert str(certificate) == ("[1] CH-000001 DV example.ru, "
                                "01.01.2026 – 01.01.2027")


def test_unknown_type_forbidden():
    with pytest.raises(ValueError):
        Certificate(1, "CH-1", "XX", make_domain(), ROMASHKA,
                    Validity.from_days(START, 10))


def test_status_depends_on_date():
    certificates: list[Certificate] = []
    certificate = issue_certificate(certificates, make_domain(), ROMASHKA,
                                    "DV", START, 365)
    assert certificate.get_status(date(2025, 12, 1)) == "pending"
    assert certificate.get_status(date(2026, 6, 1)) == "active"
    assert certificate.get_status(date(2026, 12, 15)) == "expiring"
    assert certificate.get_status_title(date(2027, 2, 1)) == "Истек"
    assert certificate.revoke()
    assert certificate.get_status(date(2026, 6, 1)) == "revoked"


def test_status_text_from_pr1():
    assert get_certificate_status(-1) == "Сертификат истек"
    assert "скоро" in get_certificate_status(30)
    assert get_certificate_status(31) == "Сертификат действителен"


def test_issue_for_foreign_domain_forbidden():
    with pytest.raises(ValueError):
        issue_certificate([], make_domain(), TECHNO, "DV", START, 365)


def test_overlapping_certificate_forbidden():
    domain = make_domain()
    certificates: list[Certificate] = []
    issue_certificate(certificates, domain, ROMASHKA, "DV", START, 365)
    with pytest.raises(ValueError):
        issue_certificate(certificates, domain, ROMASHKA, "OV",
                          date(2026, 6, 1), 30)


def test_revoked_certificate_does_not_block_domain():
    domain = make_domain()
    certificates: list[Certificate] = []
    issue_certificate(certificates, domain, ROMASHKA, "DV", START, 365)
    assert revoke_certificate(certificates, 1)
    assert not revoke_certificate(certificates, 1)
    issue_certificate(certificates, domain, ROMASHKA, "DV", START, 365)
    assert len(certificates) == 2
    assert certificates[0].is_revoked


def test_renew_and_current_certificate():
    domain = make_domain()
    certificates: list[Certificate] = []
    old = issue_certificate(certificates, domain, ROMASHKA, "OV", START, 365)
    new = renew_certificate(certificates, old, 90)
    assert new.validity.valid_from == date(2027, 1, 2)
    assert new.cert_type == "OV" and new.domain is domain
    assert get_current_certificate(certificates, domain, START) is old
    assert get_current_certificate(certificates, domain,
                                   date(2027, 2, 1)) is new
    assert sort_certificates_by_expiry([new, old]) == [old, new]


def test_expiring_certificates():
    certificates: list[Certificate] = []
    issue_certificate(certificates, make_domain(), ROMASHKA, "DV", START, 365)
    assert list(get_expiring_certificates(certificates,
                                          date(2026, 12, 20))) == certificates
    assert list(get_expiring_certificates(certificates, START)) == []


def test_to_dict_and_polymorphism():
    certificates: list[Certificate] = []
    domain = make_domain()
    certificate = issue_certificate(certificates, domain, ROMASHKA, "DV",
                                    START, 30)
    assert certificate.to_dict() == {
        "id": 1, "serial_number": "CH-000001", "cert_type": "DV",
        "domain_id": 1, "organization_id": 1,
        "valid_from": "2026-01-01", "valid_to": "2026-01-31",
        "is_revoked": False,
    }
    objects: list[Entity] = [ROMASHKA, domain, certificate]
    assert [item.to_dict()["id"] for item in objects] == [1, 1, 1]
    with pytest.raises(NotImplementedError):
        Entity(1).to_dict()
