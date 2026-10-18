"""CertHub — начальный сценарий проекта (ПР1).

Проверка срока действия SSL-сертификата домена: дата окончания,
количество оставшихся дней и текстовый статус сертификата.
"""
from datetime import date, timedelta

domain_name = "shop.example.ru"
organization_name = "ООО «Ромашка»"
certificate_type = "DV"
valid_from = date(2026, 3, 1)
validity_days = "365"  # срок из заявки приходит строкой

MAX_VALIDITY_DAYS = 398
WARNING_DAYS = 30


def is_valid_term(days: int) -> bool:
    """Проверить, что срок действия допустим (от 1 до 398 дней)."""
    return 0 < days <= MAX_VALIDITY_DAYS


def get_expiry_date(start: date, days: int) -> date:
    """Вернуть дату окончания действия сертификата."""
    return start + timedelta(days=days)


def get_days_left(expiry: date, today: date) -> int:
    """Вернуть количество дней до окончания действия."""
    return (expiry - today).days


def get_certificate_status(days_left: int) -> str:
    """Вернуть текстовый статус сертификата по оставшимся дням."""
    if days_left < 0:
        return "Сертификат истек"
    elif days_left <= WARNING_DAYS:
        return "Сертификат скоро истечет — требуется продление"
    else:
        return "Сертификат действителен"


def main() -> None:
    """Выполнить сценарий проверки срока действия сертификата."""
    days = int(validity_days)
    answer = input(f"Срок действия в днях (Enter — {days}): ")
    if answer.isdigit():
        days = int(answer)
    elif answer:
        print("Введено не число, используется срок из заявки")

    if not is_valid_term(days):
        print(f"Срок {days} дн. недопустим: максимум {MAX_VALIDITY_DAYS} дн.")
        days = MAX_VALIDITY_DAYS

    today = date.today()
    expiry = get_expiry_date(valid_from, days)
    days_left = get_days_left(expiry, today)

    print()
    print(f"Домен: {domain_name}")
    print(f"Организация: {organization_name}")
    print(f"Тип сертификата: {certificate_type}")
    print(f"Действует: {valid_from.strftime('%d.%m.%Y')} — "
          f"{expiry.strftime('%d.%m.%Y')} ({days} дн.)")
    print(f"Дата проверки: {today.strftime('%d.%m.%Y')}, "
          f"осталось дней: {days_left}")
    print(get_certificate_status(days_left))


if __name__ == "__main__":
    main()
