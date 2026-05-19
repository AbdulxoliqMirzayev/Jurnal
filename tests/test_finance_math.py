from __future__ import annotations

import pytest

from app.utils.finance_math import calculate_compound_projection, calculate_compound_projection_for_days, calculate_risk_amount


def test_compound_trading_days():
    result = calculate_compound_projection(200, 5)
    assert result["1_week"] == pytest.approx(200 * (1.05**5))
    assert result["3_months"] == pytest.approx(200 * (1.05**60))


def test_risk_amount():
    assert calculate_risk_amount(1000, 5) == 50.0
    assert calculate_risk_amount(200, 2) == 4.0


def test_onboarding_projection_days():
    result = calculate_compound_projection_for_days(500, 5)
    assert result[3] == pytest.approx(500 * (1.05**3))
    assert result[60] == pytest.approx(500 * (1.05**60))
    assert result[100] == pytest.approx(500 * (1.05**100))
    assert result[240] == pytest.approx(500 * (1.05**240))
