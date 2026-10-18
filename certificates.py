"""Функции для работы с SSL-сертификатами и сроками их действия.

Сертификаты хранятся в списке словарей: идентификатор, серийный номер,
тип, идентификатор домена, срок действия (valid_from, valid_to — строки
ГГГГ-ММ-ДД) и признак отзыва is_revoked.
"""
from datetime import date, timedelta
from typing import Iterator, Optional

MAX_VALIDITY_DAYS = 398
WARNING_DAYS = 30

CERTIFICATE_TYPES = {
    "DV": "DV — проверка домена",
    "OV": "OV — проверка организации",
    "EV": "EV — расширенная проверка",
}

STATUSES = {
    "pending": "еще не действует",
    "active": "действует",
    "expiring": "скоро истекает",
    "expired": "истек",
    "revoked": "отозван",
}


def is_valid_term(days: int) -> bool:
    """Проверить допустимость срока действия (функция из ПР1)."""
    return 0 < days <= MAX_VALIDITY_DAYS


def get_expiry_date(start: date, days: int) -> date:
    """Вернуть дату окончания действия (функция из ПР1)."""
    return start + timedelta(days=days)


def get_days_left(expiry: date, today: date) -> int:
    """Вернуть количество дней до окончания (функция из ПР1)."""
    return (expiry - today).days


def get_certificate_status(days_left: int) -> str:
    """Вернуть текстовый статус по оставшимся дням (функция из ПР1)."""
    if days_left < 0:
        return "Сертификат истек"
    if days_left <= WARNING_DAYS:
        return "Сертификат скоро истечет — требуется продление"
    return "Сертификат действителен"


def get_period(certificate: dict) -> tuple[date, date]:
    """Вернуть срок действия сертификата как пару дат."""
    return (
        date.fromisoformat(certificate["valid_from"]),
        date.fromisoformat(certificate["valid_to"]),
    )


def get_status(certificate: dict, today: date) -> str:
    """Определить код статуса сертификата на дату today."""
    if certificate["is_revoked"]:
        return "revoked"
    valid_from, valid_to = get_period(certificate)
    if today < valid_from:
        return "pending"
    days_left = get_days_left(valid_to, today)
    if days_left < 0:
        return "expired"
    if days_left <= WARNING_DAYS:
        return "expiring"
    return "active"


def periods_overlap(certificate: dict, start: date, end: date) -> bool:
    """Проверить, пересекается ли срок сертификата с периодом start–end."""
    valid_from, valid_to = get_period(certificate)
    return valid_from <= end and start <= valid_to


def has_active_certificate(
    certificates: list[dict],
    domain_id: int,
    start: date,
    end: date,
) -> bool:
    """Проверить, есть ли у домена неотозванный сертификат на этот период."""
    return any(
        certificate["domain_id"] == domain_id
        and not certificate["is_revoked"]
        and periods_overlap(certificate, start, end)
        for certificate in certificates
    )


def find_certificate_by_id(
    certificates: list[dict],
    certificate_id: int,
) -> Optional[dict]:
    """Найти сертификат по идентификатору."""
    for certificate in certificates:
        if certificate["id"] == certificate_id:
            return certificate
    return None


def get_domain_certificates(
    certificates: list[dict],
    domain_id: int,
) -> list[dict]:
    """Вернуть все сертификаты домена."""
    return [c for c in certificates if c["domain_id"] == domain_id]


def issue_certificate(
    domains: dict[int, dict],
    certificates: list[dict],
    domain_id: int,
    cert_type: str,
    valid_from: date,
    days: int,
) -> dict:
    """Выпустить сертификат для домена и вернуть его данные.

    При нарушении правил возбуждается ValueError с причиной.
    """
    if domain_id not in domains:
        raise ValueError("Домен не найден")
    if cert_type not in CERTIFICATE_TYPES:
        raise ValueError(f"Неизвестный тип сертификата: {cert_type}")
    if not is_valid_term(days):
        raise ValueError(f"Срок должен быть от 1 до {MAX_VALIDITY_DAYS} дней")
    valid_to = get_expiry_date(valid_from, days)
    if has_active_certificate(certificates, domain_id, valid_from, valid_to):
        raise ValueError("У домена уже есть сертификат на этот период")
    certificate_id = max((c["id"] for c in certificates), default=0) + 1
    certificate = {
        "id": certificate_id,
        "serial_number": f"CH-{certificate_id:06d}",
        "cert_type": cert_type,
        "domain_id": domain_id,
        "valid_from": valid_from.isoformat(),
        "valid_to": valid_to.isoformat(),
        "is_revoked": False,
    }
    certificates.append(certificate)
    return certificate


def renew_certificate(
    domains: dict[int, dict],
    certificates: list[dict],
    certificate_id: int,
    days: int,
) -> dict:
    """Продлить сертификат: выпустить новый с даты окончания старого."""
    old = find_certificate_by_id(certificates, certificate_id)
    if old is None:
        raise ValueError("Сертификат не найден")
    if old["is_revoked"]:
        raise ValueError("Отозванный сертификат продлить нельзя")
    _, valid_to = get_period(old)
    return issue_certificate(
        domains, certificates, old["domain_id"], old["cert_type"],
        valid_to + timedelta(days=1), days,
    )


def revoke_certificate(certificates: list[dict], certificate_id: int) -> bool:
    """Отозвать сертификат; False — если не найден или уже отозван."""
    certificate = find_certificate_by_id(certificates, certificate_id)
    if certificate is None or certificate["is_revoked"]:
        return False
    certificate["is_revoked"] = True
    return True


def get_expiring_certificates(
    certificates: list[dict],
    today: date,
) -> Iterator[dict]:
    """Отобрать сертификаты, которые скоро истекут (генератор)."""
    for certificate in certificates:
        if get_status(certificate, today) == "expiring":
            yield certificate


def sort_certificates_by_expiry(certificates: list[dict]) -> list[dict]:
    """Вернуть сертификаты, упорядоченные по дате окончания."""
    return sorted(certificates, key=lambda c: c["valid_to"])
