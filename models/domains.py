"""Класс Domain и функции работы с коллекцией доменов."""
import re
from typing import Iterator, List, Optional

from .base import Entity
from .organizations import Organization

DOMAIN_PATTERN = re.compile(r"^(\*\.)?([a-zа-я0-9-]+\.)+[a-zа-я]{2,}$")


class Domain(Entity):
    """Доменное имя, принадлежащее организации."""

    def __init__(
        self,
        domain_id: int,
        name: str,
        organization: Organization,
    ) -> None:
        """Создать объект домена."""
        super().__init__(domain_id)
        self.name = name
        self.organization = organization

    @property
    def name(self) -> str:
        """Доменное имя в нижнем регистре."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Изменить доменное имя, проверив его формат."""
        value = value.strip().lower()
        if not Domain.is_valid_name(value):
            raise ValueError(f"Некорректное доменное имя: {value}")
        self._name = value

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Проверить, что строка похожа на доменное имя (shop.example.ru)."""
        return bool(DOMAIN_PATTERN.match(name.lower()))

    @property
    def zone(self) -> str:
        """Доменная зона: ru, com и т. п."""
        return self.name.rsplit(".", 1)[-1]

    def belongs_to(self, organization: Organization) -> bool:
        """Проверить, что домен принадлежит организации."""
        return self.organization is organization

    def to_dict(self) -> dict:
        """Вернуть данные для JSON: вместо организации — ее идентификатор."""
        return {
            "id": self.id,
            "name": self.name,
            "organization_id": self.organization.id,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление домена."""
        return f"{self.name} — {self.organization.name}"


def find_domain_by_name(domains: List[Domain], name: str) -> Optional[Domain]:
    """Найти домен по точному имени."""
    name = name.strip().lower()
    for domain in domains:
        if domain.name == name:
            return domain
    return None


def add_domain(
    domains: List[Domain],
    name: str,
    organization: Organization,
) -> Domain:
    """Создать домен, добавить его в коллекцию и вернуть.

    Некорректное или уже учтенное имя приводит к ValueError.
    """
    if find_domain_by_name(domains, name) is not None:
        raise ValueError(f"Домен {name.strip().lower()} уже учтен")
    domain_id = max((domain.id for domain in domains), default=0) + 1
    domain = Domain(domain_id, name, organization)
    domains.append(domain)
    return domain


def find_domain(domains: List[Domain], query: str) -> List[Domain]:
    """Найти домены, в имени которых встречается подстрока query."""
    query = query.lower()
    return [domain for domain in domains if query in domain.name]


def find_domain_by_id(
    domains: List[Domain],
    domain_id: int,
) -> Optional[Domain]:
    """Найти домен по идентификатору."""
    for domain in domains:
        if domain.id == domain_id:
            return domain
    return None


def get_organization_domains(
    domains: List[Domain],
    organization: Organization,
) -> List[Domain]:
    """Вернуть домены организации."""
    return [domain for domain in domains if domain.belongs_to(organization)]


def filter_domains_by_zone(
    domains: List[Domain],
    zone: str,
) -> Iterator[Domain]:
    """Отобрать домены доменной зоны, например ru или com (генератор)."""
    zone = zone.strip(".").lower()
    for domain in domains:
        if domain.zone == zone:
            yield domain


def sort_domains(domains: List[Domain]) -> List[Domain]:
    """Вернуть домены, упорядоченные по имени."""
    return sorted(domains, key=lambda domain: domain.name)


def show_domains(domains: List[Domain]) -> None:
    """Вывести список доменов."""
    if not domains:
        print("Домены не найдены")
        return
    for domain in domains:
        print(f"{domain.id:>3}  {domain}")
