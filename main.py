"""CertHub — консольное приложение управления SSL-сертификатами.

Точка запуска программы: меню и вызов функций проекта.
Каждый пункт меню — функция с общей сигнатурой (domains, certificates).
Текст пункта меню берется из документации функции (интроспекция).
"""
import os
from datetime import date
from typing import Callable

from certificates import (
    CERTIFICATE_TYPES,
    MAX_VALIDITY_DAYS,
    STATUSES,
    get_certificate_status,
    get_days_left,
    get_domain_certificates,
    get_expiring_certificates,
    get_period,
    get_status,
    issue_certificate,
    renew_certificate,
    revoke_certificate,
    sort_certificates_by_expiry,
)
from domains import (
    add_domain,
    filter_domains_by_zone,
    find_domain,
    find_domain_by_name,
    get_domains_by_owner,
    sort_domains,
)
from storage import (
    load_certificates,
    load_domains,
    save_certificates,
    save_domains,
)
from utils import format_date, input_choice, input_date, input_int, input_text

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DOMAINS_FILE = os.path.join(DATA_DIR, "domains.json")
CERTIFICATES_FILE = os.path.join(DATA_DIR, "certificates.json")

Action = Callable[[dict[int, dict], list[dict]], None]


def save_all(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Сохранить все данные проекта в JSON-файлы."""
    save_domains(DOMAINS_FILE, domains)
    save_certificates(CERTIFICATES_FILE, certificates)


def print_domains(domains: list[dict]) -> None:
    """Вывести таблицу доменов."""
    if not domains:
        print("Домены не найдены")
        return
    for domain in domains:
        print(f"{domain['id']:>3}  {domain['name']:<22}{domain['owner']}")


def print_certificates(
    certificates: list[dict],
    domains: dict[int, dict],
) -> None:
    """Вывести список сертификатов со сроком и статусом."""
    if not certificates:
        print("Сертификаты не найдены")
        return
    today = date.today()
    for certificate in certificates:
        domain = domains.get(certificate["domain_id"])
        name = domain["name"] if domain else "?"
        print(f"[{certificate['id']}] {certificate['serial_number']} "
              f"{certificate['cert_type']} {name:<20} "
              f"{format_date(certificate['valid_from'])} – "
              f"{format_date(certificate['valid_to'])}  "
              f"{STATUSES[get_status(certificate, today)]}")


def show_domains(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Показать домены"""
    print_domains(sort_domains(domains))


def search_domains(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Найти домен по имени"""
    print_domains(find_domain(domains, input_text("Часть имени домена: ")))


def select_domains(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Отобрать домены по зоне или организации"""
    query = input_text("Зона (ru, com) или название организации: ")
    found = list(filter_domains_by_zone(domains, query))
    print_domains(found or get_domains_by_owner(domains, query))


def create_domain(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Добавить домен"""
    name = input_text("Доменное имя: ")
    owner = input_text("Организация-владелец: ")
    try:
        domain = add_domain(domains, name, owner)
    except ValueError as error:
        print(error)
        return
    save_all(domains, certificates)
    print(f"Домен добавлен, ID {domain['id']}")


def show_certificates(
    domains: dict[int, dict],
    certificates: list[dict],
) -> None:
    """Показать сертификаты"""
    print_certificates(sort_certificates_by_expiry(certificates), domains)


def check_domain(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Проверить срок действия сертификата домена"""
    domain = find_domain_by_name(domains, input_text("Доменное имя: "))
    if domain is None:
        print("Домен не найден")
        return
    today = date.today()
    current = [
        c for c in get_domain_certificates(certificates, domain["id"])
        if get_status(c, today) in ("active", "expiring", "expired")
    ]
    if not current:
        print("У домена нет действующих сертификатов")
        return
    latest = max(current, key=lambda c: c["valid_to"])
    _, valid_to = get_period(latest)
    days_left = get_days_left(valid_to, today)
    print(f"Сертификат {latest['serial_number']} до "
          f"{valid_to.strftime('%d.%m.%Y')}, осталось дней: {days_left}")
    print(get_certificate_status(days_left))


def issue(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Выпустить сертификат"""
    domain = find_domain_by_name(domains, input_text("Доменное имя: "))
    if domain is None:
        print("Домен не найден")
        return
    cert_type = input_choice("Тип сертификата: ", CERTIFICATE_TYPES)
    valid_from = input_date("Начало действия ДД.ММ.ГГГГ (Enter — сегодня): ")
    days = input_int(f"Срок в днях (до {MAX_VALIDITY_DAYS}, Enter — 365): ",
                     min_value=1, default=365)
    try:
        certificate = issue_certificate(domains, certificates, domain["id"],
                                        cert_type, valid_from, days)
    except ValueError as error:
        print(f"Сертификат не выпущен: {error}")
        return
    save_all(domains, certificates)
    print(f"Выпущен сертификат {certificate['serial_number']}")


def renew(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Продлить сертификат"""
    certificate_id = input_int("ID сертификата: ")
    days = input_int("Срок в днях (Enter — 365): ", min_value=1, default=365)
    try:
        certificate = renew_certificate(domains, certificates,
                                        certificate_id, days)
    except ValueError as error:
        print(f"Сертификат не продлен: {error}")
        return
    save_all(domains, certificates)
    print(f"Выпущен новый сертификат {certificate['serial_number']} "
          f"с {format_date(certificate['valid_from'])}")


def revoke(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Отозвать сертификат"""
    if revoke_certificate(certificates, input_int("ID сертификата: ")):
        save_all(domains, certificates)
        print("Сертификат отозван")
    else:
        print("Сертификат не найден или уже отозван")


def show_expiring(domains: dict[int, dict], certificates: list[dict]) -> None:
    """Показать сертификаты, требующие продления"""
    expiring = list(get_expiring_certificates(certificates, date.today()))
    print_certificates(expiring, domains)


ACTIONS: dict[str, Action] = {
    "1": show_domains,
    "2": search_domains,
    "3": select_domains,
    "4": create_domain,
    "5": show_certificates,
    "6": check_domain,
    "7": issue,
    "8": renew,
    "9": revoke,
    "10": show_expiring,
}


def print_menu() -> None:
    """Вывести меню, используя документацию функций-действий."""
    print("\n=== CertHub: управление SSL-сертификатами ===")
    for key, action in ACTIONS.items():
        print(f"{key}. {action.__doc__}")
    print("0. Выход")


def main() -> None:
    """Точка запуска приложения: загрузка данных и цикл меню."""
    domains = load_domains(DOMAINS_FILE)
    certificates = load_certificates(CERTIFICATES_FILE)
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
        action(domains, certificates)


if __name__ == "__main__":
    main()
