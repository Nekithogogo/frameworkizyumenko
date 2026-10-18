import pytest

from domains import (
    add_domain,
    filter_domains_by_zone,
    find_domain,
    find_domain_by_name,
    get_domains_by_owner,
    is_valid_domain_name,
    sort_domains,
)


def make_domains() -> dict[int, dict]:
    domains: dict[int, dict] = {}
    add_domain(domains, "Shop.Example.ru", "ООО «Ромашка»")
    add_domain(domains, "api.techno.com", "АО «Техно»")
    return domains


def test_add_domain_normalizes_name():
    domains = make_domains()
    assert len(domains) == 2
    assert domains[1]["name"] == "shop.example.ru"


@pytest.mark.parametrize("name", ["localhost", "bad name.ru", "a..ru"])
def test_invalid_domain_name_forbidden(name):
    assert not is_valid_domain_name(name)
    with pytest.raises(ValueError):
        add_domain({}, name, "ООО")


def test_duplicate_domain_forbidden():
    with pytest.raises(ValueError):
        add_domain(make_domains(), "SHOP.example.ru", "ООО")


def test_find_domains():
    domains = make_domains()
    assert find_domain(domains, "techno")[0]["id"] == 2
    assert find_domain_by_name(domains, "API.techno.com")["id"] == 2
    assert get_domains_by_owner(domains, "ооо «ромашка»")[0]["id"] == 1


def test_filter_and_sort_domains():
    domains = make_domains()
    assert [d["id"] for d in filter_domains_by_zone(domains, "ru")] == [1]
    assert [d["id"] for d in sort_domains(domains)] == [2, 1]
