"""Класс Validity — срок действия сертификата."""
from datetime import date, timedelta

MAX_VALIDITY_DAYS = 398
WARNING_DAYS = 30


class Validity:
    """Период действия сертификата: с valid_from по valid_to включительно.

    Срок не имеет собственного идентификатора: он существует только
    в составе сертификата и хранится вместе с ним.
    """

    def __init__(self, valid_from: date, valid_to: date) -> None:
        """Создать срок действия, проверив порядок дат."""
        if valid_to <= valid_from:
            raise ValueError("Дата окончания должна быть позже даты начала")
        self.valid_from = valid_from
        self.valid_to = valid_to

    @staticmethod
    def is_valid_term(days: int) -> bool:
        """Проверить допустимость срока в днях (логика из ПР1)."""
        return 0 < days <= MAX_VALIDITY_DAYS

    @classmethod
    def from_days(cls, start: date, days: int) -> "Validity":
        """Создать срок по дате начала и длительности в днях."""
        if not cls.is_valid_term(days):
            raise ValueError(
                f"Срок должен быть от 1 до {MAX_VALIDITY_DAYS} дней"
            )
        return cls(start, start + timedelta(days=days))

    @classmethod
    def from_data(cls, data: dict) -> "Validity":
        """Создать срок из данных JSON (даты ГГГГ-ММ-ДД)."""
        return cls(
            date.fromisoformat(data["valid_from"]),
            date.fromisoformat(data["valid_to"]),
        )

    @property
    def days_total(self) -> int:
        """Длительность срока в днях."""
        return (self.valid_to - self.valid_from).days

    def days_left(self, today: date) -> int:
        """Количество дней до окончания (отрицательное — срок прошел)."""
        return (self.valid_to - today).days

    def has_started(self, today: date) -> bool:
        """Проверить, что срок уже начался."""
        return today >= self.valid_from

    def is_expired(self, today: date) -> bool:
        """Проверить, что срок закончился."""
        return today > self.valid_to

    def is_expiring(self, today: date) -> bool:
        """Проверить, что до окончания осталось не больше WARNING_DAYS."""
        return 0 <= self.days_left(today) <= WARNING_DAYS

    def contains(self, day: date) -> bool:
        """Проверить, что дата day попадает в срок."""
        return self.valid_from <= day <= self.valid_to

    def overlaps(self, other: "Validity") -> bool:
        """Проверить, пересекается ли срок с другим сроком."""
        return (self.valid_from <= other.valid_to
                and other.valid_from <= self.valid_to)

    def next_start(self) -> date:
        """Дата начала следующего срока (для продления)."""
        return self.valid_to + timedelta(days=1)

    def to_dict(self) -> dict:
        """Вернуть даты срока для сохранения в JSON."""
        return {
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat(),
        }

    def __str__(self) -> str:
        """Вернуть срок в виде «01.03.2026 – 01.03.2027»."""
        return (f"{self.valid_from.strftime('%d.%m.%Y')} – "
                f"{self.valid_to.strftime('%d.%m.%Y')}")
