"""Date arithmetic expectations are hand derived, independent of engine output."""

from copy import deepcopy

import pytest

from trialtrace.engine import calculate, validate_rule
from trialtrace.errors import InputError


@pytest.mark.parametrize("actual,outside", [("2026-05-07", 1), ("2026-05-08", 0), ("2026-05-11", 0), ("2026-05-12", 1), ("2026-05-20", 9)])
def test_inclusive_boundaries_and_outside_distance(actual, outside):
    assert calculate("2026-05-01", actual) == {
        "target": "2026-05-08", "earliest": "2026-05-08", "latest": "2026-05-11", "actual": actual, "days_outside": outside,
    }


def test_leap_year():
    assert calculate("2028-02-22", "2028-02-29") == {
        "target": "2028-02-29", "earliest": "2028-02-29", "latest": "2028-03-03", "actual": "2028-02-29", "days_outside": 0,
    }


def test_asymmetric_synthetic_arithmetic_is_not_a_new_clinical_rule():
    assert calculate("2024-03-01", "2024-03-02", offset_days=4, lower_days=-2, upper_days=5) == {
        "target": "2024-03-05", "earliest": "2024-03-03", "latest": "2024-03-10", "actual": "2024-03-02", "days_outside": 1,
    }


@pytest.mark.parametrize("actual,outside", [("2024-03-04", 1), ("2024-03-05", 0), ("2024-03-06", 1)])
def test_zero_width_synthetic_window(actual, outside):
    result = calculate("2024-03-01", actual, offset_days=4, lower_days=0, upper_days=0)
    assert result == {"target": "2024-03-05", "earliest": "2024-03-05", "latest": "2024-03-05", "actual": actual, "days_outside": outside}


@pytest.mark.parametrize("anchor,offset,lower,upper", [("9999-12-29", 7, 0, 3), ("9999-12-22", 7, 0, 3), ("0001-01-01", 0, -1, 0)])
def test_representable_date_overflow_is_explicit(anchor, offset, lower, upper):
    with pytest.raises(OverflowError):
        calculate(anchor, "2026-05-08", offset_days=offset, lower_days=lower, upper_days=upper)


def test_shifted_dates_keep_distance():
    first = calculate("2026-05-01", "2026-05-12")
    second = calculate("2026-06-01", "2026-06-12")
    assert first["days_outside"] == second["days_outside"] == 1
    assert second["target"] == "2026-06-08"
    assert second["latest"] == "2026-06-11"


def test_pinned_candidate_configuration_is_valid(rule):
    assert validate_rule(rule) is None


@pytest.mark.parametrize("field,value", [
    ("upper_days", -1), ("lower_days", 1), ("offset_days", True),
    ("lower_days", False), ("upper_days", True), ("offset_days", 7.0),
    ("offset_days", "7"), ("units", "business_days"), ("bounds", "exclusive"),
    ("missing_data_policy", "treat_as_pass"),
])
def test_invalid_rule_configuration_fails_closed(rule, field, value):
    changed = deepcopy(rule)
    changed[field] = value
    with pytest.raises(InputError) as error:
        validate_rule(changed)
    assert error.value.code
