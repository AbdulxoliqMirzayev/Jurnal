from __future__ import annotations

import pytest

from app.utils.finance_math import calculate_compound_projection, calculate_risk_amount


def test_compound_trading_days():
    result = calculate_compound_projection(200, 5)
    assert result["1_week"] == pytest.approx(200 * (1.05**5))
    assert result["3_months"] == pytest.approx(200 * (1.05**60))


def test_risk_amount():
    assert calculate_risk_amount(1000, 5) == 50.0
    assert calculate_risk_amount(200, 2) == 4.0
