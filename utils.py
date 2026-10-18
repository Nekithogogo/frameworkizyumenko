"""Вспомогательные функции безопасного ввода данных."""
from datetime import date, datetime
from typing import Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)


def input_int(
    prompt: str,
    min_value: Optional[int] = None,
    default: Optional[int] = None,
) -> int:
    """Запросить у пользователя целое число.

    Пустой ввод возвращает default, если он задан.
    При некорректном вводе запрос повторяется.
    """
    while True:
        text = input(prompt).strip()
        if not text and default is not None:
            return default
        try:
            value = int(text)
        except ValueError:
            print("Введите целое число")
            continue
        if min_value is not None and value < min_value:
            print(f"Число должно быть не меньше {min_value}")
            continue
        return value


def input_text(prompt: str) -> str:
    """Запросить непустую строку."""
    while True:
        text = input(prompt).strip()
        if text:
            return text
        print("Значение не может быть пустым")


def input_date(prompt: str) -> date:
    """Запросить дату в формате ДД.ММ.ГГГГ (Enter — сегодня)."""
    while True:
        text = input(prompt).strip()
        if not text:
            return date.today()
        try:
            return datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            print("Введите дату в формате ДД.ММ.ГГГГ")


def input_choice(prompt: str, options: dict[K, str]) -> K:
    """Предложить выбрать один из вариантов и вернуть его ключ."""
    keys = list(options)
    for number, key in enumerate(keys, start=1):
        print(f"  {number}. {options[key]}")
    while True:
        number = input_int(prompt, min_value=1)
        if number <= len(keys):
            return keys[number - 1]
        print(f"Выберите номер от 1 до {len(keys)}")
