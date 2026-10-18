import pytest

from models import Domain, Organization
from models.domains import (
    add_domain,
    filter_domains_by_zone,
    find_domain,
    find_domain_by_name,
    get_organization_domains,
    sort_domains,
)

ROMASHKA = Organization(1, "ООО «Ромашка»", "7701234567", "a@a.ru")
TECHNO = Organization(2, "АО «Техно»", "7812345678", "b@b.ru")


def make_domains() -> list[Domain]:
    domains: list[Domain] = []
    add_domain(domains, "Shop.Example.ru", ROMASHKA)
    add_domain(domains, "api.techno.com", TECHNO)
    return domains


def test_domain_creation():
    domain = Domain(1, " Example.RU ", ROMASHKA)
    assert domain.name == "example.ru"
    assert domain.zone == "ru"
    assert domain.organization is ROMASHKA
    assert domain.belongs_to(ROMASHKA)
    assert not domain.belongs_to(TECHNO)
    assert str(domain) == "example.ru — ООО «Ромашка»"
    assert domain.to_dict() == {"id": 1, "name": "example.ru",
                                "organization_id": 1}


@pytest.mark.parametrize("name", ["localhost", "bad name.ru", "a..ru"])
def test_invalid_domain_name_forbidden(name):
    assert not Domain.is_valid_name(name)
    with pytest.raises(ValueError):
        Domain(1, name, ROMASHKA)


def test_duplicate_domain_forbidden():
    with pytest.raises(ValueError):
        add_domain(make_domains(), "SHOP.example.ru", ROMASHKA)


def test_find_domains():
    domains = make_domains()
    assert find_domain(domains, "techno") == [domains[1]]
    assert find_domain_by_name(domains, "API.techno.com") is domains[1]
    assert get_organization_domains(domains, ROMASHKA) == [domains[0]]


def test_filter_and_sort_domains():
    domains = make_domains()
    assert list(filter_domains_by_zone(domains, ".RU")) == [domains[0]]
    assert sort_domains(domains) == [domains[1], domains[0]]
