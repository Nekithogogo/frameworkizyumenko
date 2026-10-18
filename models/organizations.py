"""Класс Organization и функции работы с организациями."""
from typing import List, Optional

from .base import Entity


class Organization(Entity):
    """Организация — владелец доменов и заказчик сертификатов."""

    def __init__(
        self,
        organization_id: int,
        name: str,
        inn: str,
        email: str,
    ) -> None:
        """Создать объект организации."""
        super().__init__(organization_id)
        self.name = name
        self.inn = inn
        self.email = email

    @property
    def inn(self) -> str:
        """ИНН организации."""
        return self._inn

    @inn.setter
    def inn(self, value: str) -> None:
        """Изменить ИНН, проверив его формат."""
        if not Organization.validate_inn(value):
            raise ValueError("ИНН должен состоять из 10 или 12 цифр")
        self._inn = value

    @staticmethod
    def validate_inn(inn: str) -> bool:
        """Проверить формат ИНН: 10 цифр (юрлицо) или 12 цифр (ИП)."""
        return inn.isdigit() and len(inn) in (10, 12)

    @classmethod
    def from_data(cls, data: dict) -> "Organization":
        """Создать организацию из словаря данных JSON."""
        return cls(data["id"], data["name"], data["inn"], data["email"])

    def to_dict(self) -> dict:
        """Вернуть данные организации для сохранения в JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "inn": self.inn,
            "email": self.email,
        }

    def __str__(self) -> str:
        """Вернуть строковое представление организации."""
        return f"{self.name} (ИНН {self.inn})"


def add_organization(
    organizations: List[Organization],
    name: str,
    inn: str,
    email: str,
) -> Organization:
    """Создать организацию, добавить ее в коллекцию и вернуть.

    ИНН должен быть уникальным, иначе ValueError.
    """
    if any(item.inn == inn for item in organizations):
        raise ValueError(f"Организация с ИНН {inn} уже учтена")
    organization_id = max((item.id for item in organizations), default=0) + 1
    organization = Organization(organization_id, name, inn, email)
    organizations.append(organization)
    return organization


def find_organization(
    organizations: List[Organization],
    query: str,
) -> List[Organization]:
    """Найти организации по подстроке названия или ИНН."""
    query = query.lower()
    return [
        item for item in organizations
        if query in item.name.lower() or query in item.inn
    ]


def find_organization_by_id(
    organizations: List[Organization],
    organization_id: int,
) -> Optional[Organization]:
    """Найти организацию по идентификатору."""
    for organization in organizations:
        if organization.id == organization_id:
            return organization
    return None


def show_organizations(organizations: List[Organization]) -> None:
    """Вывести список организаций."""
    if not organizations:
        print("Организации не найдены")
        return
    for organization in organizations:
        print(f"{organization.id:>3}  {organization}, {organization.email}")
