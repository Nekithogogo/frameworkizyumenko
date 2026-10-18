"""Загрузка и сохранение данных проекта в JSON-файлах.

JSON хранит только данные: при загрузке они превращаются в объекты
Organization, Domain и Certificate, при сохранении — обратно в словари.
Связи хранятся в JSON идентификаторами organization_id и domain_id.
"""
import json
import os
from typing import Callable, List, Sequence, TypeVar

from models import Certificate, Domain, Entity, Organization, Validity
from models.domains import find_domain_by_id
from models.organizations import find_organization_by_id

T = TypeVar("T")


def read_json(filename: str) -> list:
    """Прочитать список записей из JSON-файла.

    Отсутствующий файл считается пустым списком. При поврежденном
    файле выводится предупреждение и также возвращается пустой список.
    """
    try:
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        print(f"Файл {filename} поврежден ({error}), данные не загружены")
        return []
    if not isinstance(data, list):
        print(f"Файл {filename} должен содержать список записей")
        return []
    return data


def write_json(filename: str, data: list) -> None:
    """Записать список записей в JSON-файл."""
    folder = os.path.dirname(filename)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_objects(filename: str, factory: Callable[[dict], T]) -> List[T]:
    """Загрузить объекты из JSON, пропуская некорректные записи."""
    objects = []
    for data in read_json(filename):
        try:
            objects.append(factory(data))
        except (KeyError, TypeError, ValueError) as error:
            print(f"{filename}: запись {data} пропущена ({error})")
    return objects


def save_objects(filename: str, objects: Sequence[Entity]) -> None:
    """Сохранить объекты любого класса-наследника Entity.

    Каждый объект сам знает, как превратиться в словарь (to_dict).
    """
    write_json(filename, [item.to_dict() for item in objects])


def load_organizations(filename: str) -> List[Organization]:
    """Загрузить организации: JSON → объекты Organization."""
    return load_objects(filename, Organization.from_data)


def save_organizations(
    filename: str,
    organizations: List[Organization],
) -> None:
    """Сохранить организации: объекты Organization → JSON."""
    save_objects(filename, organizations)


def get_organization(
    organizations: List[Organization],
    organization_id: int,
) -> Organization:
    """Найти организацию по идентификатору из JSON или сообщить об ошибке."""
    organization = find_organization_by_id(organizations, organization_id)
    if organization is None:
        raise ValueError(f"нет организации {organization_id}")
    return organization


def load_domains(
    filename: str,
    organizations: List[Organization],
) -> List[Domain]:
    """Загрузить домены и восстановить связь с Organization."""

    def make_domain(data: dict) -> Domain:
        organization = get_organization(organizations,
                                        data["organization_id"])
        return Domain(data["id"], data["name"], organization)

    return load_objects(filename, make_domain)


def save_domains(filename: str, domains: List[Domain]) -> None:
    """Сохранить домены: ссылка на организацию → идентификатор."""
    save_objects(filename, domains)


def load_certificates(
    filename: str,
    domains: List[Domain],
    organizations: List[Organization],
) -> List[Certificate]:
    """Загрузить сертификаты и восстановить связи с Domain и Organization.

    Если домен или организация с указанным идентификатором не найдены,
    запись не превращается в объект и пропускается.
    """

    def make_certificate(data: dict) -> Certificate:
        domain = find_domain_by_id(domains, data["domain_id"])
        if domain is None:
            raise ValueError(f"нет домена {data['domain_id']}")
        return Certificate(
            certificate_id=data["id"],
            serial_number=data["serial_number"],
            cert_type=data["cert_type"],
            domain=domain,
            organization=get_organization(organizations,
                                          data["organization_id"]),
            validity=Validity.from_data(data),
            is_revoked=data.get("is_revoked", False),
        )

    return load_objects(filename, make_certificate)


def save_certificates(filename: str, certificates: List[Certificate]) -> None:
    """Сохранить сертификаты: ссылки на объекты → идентификаторы."""
    save_objects(filename, certificates)


def load_data(
    data_dir: "str | os.PathLike[str]",
) -> tuple[List[Organization], List[Domain], List[Certificate]]:
    """Загрузить все данные проекта из каталога data_dir.

    Порядок важен: домены ссылаются на организации, а сертификаты —
    на домены и организации, поэтому они загружаются первыми.
    """
    organizations = load_organizations(
        os.path.join(data_dir, "organizations.json")
    )
    domains = load_domains(os.path.join(data_dir, "domains.json"),
                           organizations)
    certificates = load_certificates(
        os.path.join(data_dir, "certificates.json"), domains, organizations
    )
    return organizations, domains, certificates


def save_data(
    data_dir: "str | os.PathLike[str]",
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Сохранить все данные проекта в каталог data_dir."""
    save_organizations(os.path.join(data_dir, "organizations.json"),
                       organizations)
    save_domains(os.path.join(data_dir, "domains.json"), domains)
    save_certificates(os.path.join(data_dir, "certificates.json"),
                      certificates)
