import pytest

from models import Organization
from models.organizations import (
    add_organization,
    find_organization,
    find_organization_by_id,
)


def test_organization_creation():
    organization = Organization(1, "ООО «Ромашка»", "7701234567",
                                "admin@example.ru")
    assert organization.id == 1
    assert organization.name == "ООО «Ромашка»"
    assert organization.email == "admin@example.ru"
    assert str(organization) == "ООО «Ромашка» (ИНН 7701234567)"


@pytest.mark.parametrize("inn", ["123", "77012345AB", "77012345678"])
def test_invalid_inn_forbidden(inn):
    assert not Organization.validate_inn(inn)
    with pytest.raises(ValueError):
        Organization(1, "ООО", inn, "a@b.ru")


def test_from_data_and_to_dict():
    data = {"id": 3, "name": "ИП Иванов", "inn": "500100732259",
            "email": "ivanov@mail.ru"}
    assert Organization.from_data(data).to_dict() == data


def test_add_and_find_organizations():
    organizations: list[Organization] = []
    add_organization(organizations, "ООО «Ромашка»", "7701234567", "a@a.ru")
    add_organization(organizations, "АО «Техно»", "7812345678", "b@b.ru")
    assert organizations[1].id == 2
    assert find_organization(organizations, "техно") == [organizations[1]]
    assert find_organization(organizations, "7701") == [organizations[0]]
    assert find_organization_by_id(organizations, 9) is None
    with pytest.raises(ValueError):
        add_organization(organizations, "Дубль", "7701234567", "c@c.ru")
