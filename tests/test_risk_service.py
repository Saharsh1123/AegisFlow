"""Unit tests for every risk-evaluation outcome."""

from app.services.risk_service import MAX_ORDER_VALUE, evaluate_risk


def test_order_at_maximum_value_is_approved():
    approved, reason = evaluate_risk(5000, 10, MAX_ORDER_VALUE)

    assert approved is True
    assert reason is None


def test_order_above_maximum_value_is_rejected():
    approved, reason = evaluate_risk(5000, 11, 55000)

    assert approved is False
    assert reason == "MAX_ORDER_VALUE_EXCEEDED"


def test_mismatched_order_value_is_rejected():
    approved, reason = evaluate_risk(100, 2, 199)

    assert approved is False
    assert reason == "PRICE_MISMATCH_ERROR"
