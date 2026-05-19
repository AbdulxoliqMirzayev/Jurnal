from __future__ import annotations

import pytest

from app.utils.number_parser import NumberParseError, parse_lot, parse_number, parse_trade_count


def test_parse_number_formats():
    assert parse_number("200") == 200.0
    assert parse_number("200$") == 200.0
    assert parse_number("200 USD") == 200.0
    assert parse_number("1 000") == 1000.0
    assert parse_number("1,000.50") == 1000.5
    assert parse_number("0.05 lot") == 0.05


def test_parse_number_validation():
    with pytest.raises(NumberParseError):
        parse_number("abc")
    with pytest.raises(NumberParseError):
        parse_number("-50", allow_negative=False)


def test_lot_and_trade_count():
    assert parse_lot("0.10 lot") == 0.1
    assert parse_trade_count("5") == 5
    with pytest.raises(NumberParseError):
        parse_trade_count("2.5")
