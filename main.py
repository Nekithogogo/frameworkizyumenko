"""CertHub — консольное приложение управления SSL-сертификатами.

Точка запуска программы: меню и пользовательские сценарии.
Каждый пункт меню — функция с общей сигнатурой (organizations, domains,
certificates). Текст пункта меню берется из документации функции.
"""
import os
from datetime import date
from typing import Callable, List, Optional

from models import Certificate, Domain, Organization
from models.certificates import (
    CERTIFICATE_TYPES,
    find_certificate_by_id,
    get_certificate_status,
    get_current_certificate,
    get_domain_certificates,
    get_expiring_certificates,
    issue_certificate,
    renew_certificate,
    revoke_certificate,
    show_certificates,
    sort_certificates_by_expiry,
)
from models.domains import (
    add_domain,
    filter_domains_by_zone,
    find_domain,
    find_domain_by_name,
    show_domains,
    sort_domains,
)
from models.organizations import (
    add_organization,
    find_organization_by_id,
    show_organizations,
)
from models.validity import MAX_VALIDITY_DAYS
from storage import load_data, save_data
from utils import input_choice, input_date, input_int, input_text

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

Action = Callable[[List[Organization], List[Domain], List[Certificate]],
                  None]


def select_organization(
    organizations: List[Organization],
) -> Organization:
    """Предложить выбрать организацию из списка."""
    options = {item.id: item.name for item in organizations}
    organization = find_organization_by_id(
        organizations, input_choice("Организация: ", options)
    )
    assert organization is not None
    return organization


def select_domain(domains: List[Domain]) -> Optional[Domain]:
    """Запросить доменное имя и найти домен; сообщить, если его нет."""
    domain = find_domain_by_name(domains, input_text("Доменное имя: "))
    if domain is None:
        print("Домен не найден")
    return domain


def print_organizations(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Показать организации"""
    show_organizations(organizations)


def create_organization(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Добавить организацию"""
    name = input_text("Название: ")
    inn = input_text("ИНН (10 или 12 цифр): ")
    email = input_text("E-mail для уведомлений: ")
    try:
        organization = add_organization(organizations, name, inn, email)
    except ValueError as error:
        print(error)
        return
    save_data(DATA_DIR, organizations, domains, certificates)
    print(f"Организация добавлена: {organization}")


def print_domains(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Показать домены"""
    show_domains(sort_domains(domains))


def search_domains(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Найти домен по имени"""
    show_domains(find_domain(domains, input_text("Часть имени домена: ")))


def select_domains(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Отобрать домены по зоне"""
    zone = input_text("Доменная зона (ru, com, ...): ")
    show_domains(list(filter_domains_by_zone(domains, zone)))


def create_domain(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Добавить домен"""
    name = input_text("Доменное имя: ")
    organization = select_organization(organizations)
    try:
        domain = add_domain(domains, name, organization)
    except ValueError as error:
        print(error)
        return
    save_data(DATA_DIR, organizations, domains, certificates)
    print(f"Домен добавлен: {domain}")


def print_certificates(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Показать сертификаты"""
    show_certificates(sort_certificates_by_expiry(certificates), date.today())


def check_domain(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Проверить сертификаты домена"""
    domain = select_domain(domains)
    if domain is None:
        return
    today = date.today()
    print(domain)
    show_certificates(get_domain_certificates(certificates, domain), today)
    current = get_current_certificate(certificates, domain, today)
    if current is None:
        print("У домена нет действующих сертификатов")
        return
    days_left = current.days_left(today)
    print(f"Текущий сертификат {current.serial_number}, "
          f"осталось дней: {days_left}")
    print(get_certificate_status(days_left))


def issue(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Выпустить сертификат"""
    domain = select_domain(domains)
    if domain is None:
        return
    organization = select_organization(organizations)
    cert_type = input_choice("Тип сертификата: ", CERTIFICATE_TYPES)
    valid_from = input_date("Начало действия ДД.ММ.ГГГГ (Enter — сегодня): ")
    days = input_int(f"Срок в днях (до {MAX_VALIDITY_DAYS}, Enter — 365): ",
                     min_value=1, default=365)
    try:
        certificate = issue_certificate(certificates, domain, organization,
                                        cert_type, valid_from, days)
    except ValueError as error:
        print(f"Сертификат не выпущен: {error}")
        return
    save_data(DATA_DIR, organizations, domains, certificates)
    print(f"Выпущен сертификат: {certificate}")


def renew(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Продлить сертификат"""
    old = find_certificate_by_id(certificates, input_int("ID сертификата: "))
    if old is None:
        print("Сертификат не найден")
        return
    days = input_int("Срок в днях (Enter — 365): ", min_value=1, default=365)
    try:
        certificate = renew_certificate(certificates, old, days)
    except ValueError as error:
        print(f"Сертификат не продлен: {error}")
        return
    save_data(DATA_DIR, organizations, domains, certificates)
    print(f"Выпущен новый сертификат: {certificate}")


def revoke(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Отозвать сертификат"""
    if revoke_certificate(certificates, input_int("ID сертификата: ")):
        save_data(DATA_DIR, organizations, domains, certificates)
        print("Сертификат отозван")
    else:
        print("Сертификат не найден или уже отозван")


def print_expiring(
    organizations: List[Organization],
    domains: List[Domain],
    certificates: List[Certificate],
) -> None:
    """Показать сертификаты, требующие продления"""
    today = date.today()
    show_certificates(list(get_expiring_certificates(certificates, today)),
                      today)


ACTIONS: dict[str, Action] = {
    "1": print_organizations,
    "2": create_organization,
    "3": print_domains,
    "4": search_domains,
    "5": select_domains,
    "6": create_domain,
    "7": print_certificates,
    "8": check_domain,
    "9": issue,
    "10": renew,
    "11": revoke,
    "12": print_expiring,
}


def print_menu() -> None:
    """Вывести меню, используя документацию функций-действий."""
    print("\n=== CertHub: управление SSL-сертификатами ===")
    for key, action in ACTIONS.items():
        print(f"{key}. {action.__doc__}")
    print("0. Выход")


def main() -> None:
    """Точка запуска: загрузка объектов, цикл меню, сохранение."""
    organizations, domains, certificates = load_data(DATA_DIR)
    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Такого пункта нет")
            continue
        print()
        action(organizations, domains, certificates)
    save_data(DATA_DIR, organizations, domains, certificates)


if __name__ == "__main__":
    main()
