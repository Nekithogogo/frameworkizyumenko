"""Функции для работы с доменами.

Домены хранятся в словаре: ключ — идентификатор домена, значение —
словарь с данными домена (name — доменное имя, owner — организация).
"""
import re
from typing import Iterator, Optional

DOMAIN_PATTERN = re.compile(r"^(\*\.)?([a-zа-я0-9-]+\.)+[a-zа-я]{2,}$")


def is_valid_domain_name(name: str) -> bool:
    """Проверить, что строка похожа на доменное имя (shop.example.ru)."""
    return bool(DOMAIN_PATTERN.match(name.lower()))


def add_domain(domains: dict[int, dict], name: str, owner: str) -> dict:
    """Добавить домен в словарь domains и вернуть его данные.

    Доменное имя приводится к нижнему регистру; некорректное или уже
    учтенное имя приводит к ValueError.
    """
    name = name.strip().lower()
    if not is_valid_domain_name(name):
        raise ValueError(f"Некорректное доменное имя: {name}")
    if find_domain_by_name(domains, name) is not None:
        raise ValueError(f"Домен {name} уже учтен")
    domain_id = max(domains, default=0) + 1
    domain = {"id": domain_id, "name": name, "owner": owner}
    domains[domain_id] = domain
    return domain


def find_domain(domains: dict[int, dict], query: str) -> list[dict]:
    """Найти домены, в имени которых встречается подстрока query."""
    query = query.lower()
    return [domain for domain in domains.values() if query in domain["name"]]


def find_domain_by_name(
    domains: dict[int, dict],
    name: str,
) -> Optional[dict]:
    """Найти домен по точному имени."""
    for domain in domains.values():
        if domain["name"] == name.lower():
            return domain
    return None


def get_domains_by_owner(domains: dict[int, dict], owner: str) -> list[dict]:
    """Вернуть домены организации-владельца."""
    return [
        domain for domain in domains.values()
        if domain["owner"].lower() == owner.lower()
    ]


def filter_domains_by_zone(
    domains: dict[int, dict],
    zone: str,
) -> Iterator[dict]:
    """Отобрать домены доменной зоны, например ru или com (генератор)."""
    suffix = "." + zone.strip(".").lower()
    for domain in domains.values():
        if domain["name"].endswith(suffix):
            yield domain


def sort_domains(domains: dict[int, dict]) -> list[dict]:
    """Вернуть домены, упорядоченные по имени."""
    return sorted(domains.values(), key=lambda domain: domain["name"])
