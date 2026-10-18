from datetime import date

import pytest

from models import Validity

START = date(2026, 1, 1)


def test_validity_from_days():
    validity = Validity.from_days(START, 365)
    assert validity.valid_to == date(2027, 1, 1)
    assert validity.days_total == 365
    assert str(validity) == "01.01.2026 – 01.01.2027"


def test_invalid_terms_forbidden():
    assert Validity.is_valid_term(398)
    assert not Validity.is_valid_term(399)
    with pytest.raises(ValueError):
        Validity.from_days(START, 0)
    with pytest.raises(ValueError):
        Validity(START, START)


def test_days_left_and_states():
    validity = Validity.from_days(START, 100)
    assert validity.days_left(START) == 100
    assert not validity.has_started(date(2025, 12, 31))
    assert validity.is_expiring(date(2026, 3, 20))
    assert not validity.is_expiring(START)
    assert validity.is_expired(date(2026, 4, 12))


def test_overlaps_and_next_start():
    first = Validity.from_days(START, 30)
    second = Validity.from_days(first.next_start(), 30)
    assert second.valid_from == date(2026, 2, 1)
    assert not first.overlaps(second)
    assert first.overlaps(Validity.from_days(date(2026, 1, 31), 10))


def test_to_dict_and_from_data():
    data = {"valid_from": "2026-01-01", "valid_to": "2027-01-01"}
    assert Validity.from_data(data).to_dict() == data
