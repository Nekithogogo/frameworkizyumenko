"""Класс Certificate и функции работы с коллекцией сертификатов."""
from datetime import date
from typing import Iterator, List, Optional

from .base import Entity
from .domains import Domain
from .organizations import Organization
from .validity import WARNING_DAYS, Validity

CERTIFICATE_TYPES = {
    "DV": "DV — проверка домена",
    "OV": "OV — проверка организации",
    "EV": "EV — расширенная проверка",
}

STATUSES = {
    "pending": "Еще не действует",
    "active": "Действует",
    "expiring": "Скоро истекает",
    "expired": "Истек",
    "revoked": "Отозван",
}


class Certificate(Entity):
    """SSL-сертификат, выпущенный для домена по заказу организации.

    Сертификат хранит ссылки на объекты Domain и Organization
    и срок действия — объект Validity.
    """

    def __init__(
        self,
        certificate_id: int,
        serial_number: str,
        cert_type: str,
        domain: Domain,
        organization: Organization,
        validity: Validity,
        is_revoked: bool = False,
    ) -> None:
        """Создать объект сертификата."""
        super().__init__(certificate_id)
        if cert_type not in CERTIFICATE_TYPES:
            raise ValueError(f"Неизвестный тип сертификата: {cert_type}")
        self.serial_number = serial_number
        self.cert_type = cert_type
        self.domain = domain
        self.organization = organization
        self.validity = validity
        self.is_revoked = is_revoked

    def revoke(self) -> bool:
        """Отозвать сертификат; False — если он уже отозван."""
        if self.is_revoked:
            return False
        self.is_revoked = True
        return True

    def is_valid_on(self, day: date) -> bool:
        """Проверить, что сертификат защищает домен в день day."""
        return not self.is_revoked and self.validity.contains(day)

    def blocks(self, validity: Validity) -> bool:
        """Проверить, мешает ли сертификат выпуску нового на срок validity."""
        return not self.is_revoked and self.validity.overlaps(validity)

    def days_left(self, today: date) -> int:
        """Количество дней до окончания действия."""
        return self.validity.days_left(today)

    def get_status(self, today: date) -> str:
        """Определить код статуса сертификата на дату today."""
        if self.is_revoked:
            return "revoked"
        if not self.validity.has_started(today):
            return "pending"
        if self.validity.is_expired(today):
            return "expired"
        if self.validity.is_expiring(today):
            return "expiring"
        return "active"

    def get_status_title(self, today: date) -> str:
        """Вернуть название статуса для отображения."""
        return STATUSES[self.get_status(today)]

    def to_dict(self) -> dict:
        """Вернуть данные для JSON: вместо объектов — их идентификаторы."""
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "cert_type": self.cert_type,
            "domain_id": self.domain.id,
            "organization_id": self.organization.id,
            **self.validity.to_dict(),
            "is_revoked": self.is_revoked,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление сертификата."""
        mark = " (отозван)" if self.is_revoked else ""
        return (f"[{self.id}] {self.serial_number} {self.cert_type} "
                f"{self.domain.name}, {self.validity}{mark}")


def get_certificate_status(days_left: int) -> str:
    """Вернуть текстовый статус по оставшимся дням (функция из ПР1)."""
    if days_left < 0:
        return "Сертификат истек"
    if days_left <= WARNING_DAYS:
        return "Сертификат скоро истечет — требуется продление"
    return "Сертификат действителен"


def find_certificate_by_id(
    certificates: List[Certificate],
    certificate_id: int,
) -> Optional[Certificate]:
    """Найти сертификат по идентификатору."""
    for certificate in certificates:
        if certificate.id == certificate_id:
            return certificate
    return None


def get_domain_certificates(
    certificates: List[Certificate],
    domain: Domain,
) -> List[Certificate]:
    """Вернуть все сертификаты домена."""
    return [c for c in certificates if c.domain is domain]


def get_current_certificate(
    certificates: List[Certificate],
    domain: Domain,
    today: date,
) -> Optional[Certificate]:
    """Вернуть последний начавшийся неотозванный сертификат домена."""
    started = [
        c for c in get_domain_certificates(certificates, domain)
        if not c.is_revoked and c.validity.has_started(today)
    ]
    if not started:
        return None
    return max(started, key=lambda c: c.validity.valid_to)


def has_active_certificate(
    certificates: List[Certificate],
    domain: Domain,
    validity: Validity,
) -> bool:
    """Проверить, есть ли у домена сертификат, пересекающийся по сроку."""
    return any(
        c.blocks(validity)
        for c in get_domain_certificates(certificates, domain)
    )


def issue_certificate(
    certificates: List[Certificate],
    domain: Domain,
    organization: Organization,
    cert_type: str,
    valid_from: date,
    days: int,
) -> Certificate:
    """Выпустить сертификат, добавить его в коллекцию и вернуть.

    При нарушении правил возбуждается ValueError с причиной.
    """
    if not domain.belongs_to(organization):
        raise ValueError(f"Домен {domain.name} не принадлежит "
                         f"организации {organization.name}")
    validity = Validity.from_days(valid_from, days)
    if has_active_certificate(certificates, domain, validity):
        raise ValueError("У домена уже есть сертификат на этот период")
    certificate_id = max((c.id for c in certificates), default=0) + 1
    certificate = Certificate(
        certificate_id, f"CH-{certificate_id:06d}", cert_type,
        domain, organization, validity,
    )
    certificates.append(certificate)
    return certificate


def renew_certificate(
    certificates: List[Certificate],
    certificate: Certificate,
    days: int,
) -> Certificate:
    """Продлить сертификат: выпустить новый с даты окончания старого."""
    if certificate.is_revoked:
        raise ValueError("Отозванный сертификат продлить нельзя")
    return issue_certificate(
        certificates, certificate.domain, certificate.organization,
        certificate.cert_type, certificate.validity.next_start(), days,
    )


def revoke_certificate(
    certificates: List[Certificate],
    certificate_id: int,
) -> bool:
    """Найти сертификат и отозвать его."""
    certificate = find_certificate_by_id(certificates, certificate_id)
    return certificate is not None and certificate.revoke()


def get_expiring_certificates(
    certificates: List[Certificate],
    today: date,
) -> Iterator[Certificate]:
    """Отобрать сертификаты, которые скоро истекут (генератор)."""
    for certificate in certificates:
        if certificate.get_status(today) == "expiring":
            yield certificate


def sort_certificates_by_expiry(
    certificates: List[Certificate],
) -> List[Certificate]:
    """Вернуть сертификаты, упорядоченные по дате окончания."""
    return sorted(certificates, key=lambda c: c.validity.valid_to)


def show_certificates(certificates: List[Certificate], today: date) -> None:
    """Вывести список сертификатов со статусом."""
    if not certificates:
        print("Сертификаты не найдены")
        return
    for certificate in certificates:
        print(f"{certificate}  — {certificate.get_status_title(today)}")
