
import pytest

from src.ab_testing import (
    calculate_conversion_rate,
    calculate_uplift,
    calculate_p_value,
    calculate_confidence_interval,
    calculate_srm_p_value,
    calculate_sample_size,
)


def test_conversion_rate():
    conversions = 50
    total_users = 500

    result = calculate_conversion_rate(conversions, total_users)

    assert result == 0.10


def test_zero_users():
    with pytest.raises(ValueError):
        calculate_conversion_rate(0, 0)


def test_positive_uplift():
    control_rate = 0.10
    treatment_rate = 0.12

    result = calculate_uplift(control_rate, treatment_rate)

    assert round(result, 2) == 0.20


def test_negative_uplift():
    control_rate = 0.10
    treatment_rate = 0.08

    result = calculate_uplift(control_rate, treatment_rate)

    assert round(result, 2) == -0.20


def test_not_statistically_significant():
    p_value = calculate_p_value(50, 500, 65, 500)

    assert p_value > 0.05


def test_statistically_significant():
    p_value = calculate_p_value(50, 500, 100, 500)

    assert p_value < 0.05


def test_confidence_interval_includes_zero():
    lower, upper = calculate_confidence_interval(
        50, 500, 65, 500
    )

    assert lower < 0 < upper


def test_confidence_interval_excludes_zero():
    lower, upper = calculate_confidence_interval(
        50, 500, 100, 500
    )

    assert lower > 0
    assert upper > lower

def test_srm_balanced_groups():
    p_value = calculate_srm_p_value(500, 500)

    assert p_value == pytest.approx(1.0)


def test_srm_unbalanced_groups():
    p_value = calculate_srm_p_value(700, 300)

    assert p_value < 0.001


def test_srm_zero_users():
    with pytest.raises(ValueError):
        calculate_srm_p_value(0, 0)


def test_sample_size_positive():
    result = calculate_sample_size(0.10, 0.12)

    assert isinstance(result, int)
    assert result > 0


def test_sample_size_smaller_effect():
    small_effect = calculate_sample_size(0.10, 0.11)
    large_effect = calculate_sample_size(0.10, 0.15)

    assert small_effect > large_effect


def test_sample_size_invalid_rates():
    with pytest.raises(ValueError):
        calculate_sample_size(0.10, 0.10)
