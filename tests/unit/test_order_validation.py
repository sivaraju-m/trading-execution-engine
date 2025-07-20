import pytest
from trading_execution_engine.orders.validation import (
    validate_order,
    OrderType,
    OrderDirection,
    TimeInForce,
)


def test_validate_order():
    """Test order validation for various scenarios."""

    # Test valid market order
    valid_market_order = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "BUY",
        "order_type": "MARKET",
    }

    result = validate_order(valid_market_order)
    assert result.is_valid
    assert len(result.errors) == 0

    # Test valid limit order
    valid_limit_order = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "BUY",
        "order_type": "LIMIT",
        "limit_price": 150.50,
    }

    result = validate_order(valid_limit_order)
    assert result.is_valid
    assert len(result.errors) == 0

    # Test invalid order (missing required field)
    invalid_order_missing_field = {
        "symbol": "AAPL",
        "direction": "BUY",
        "order_type": "MARKET",
        # Missing quantity
    }

    result = validate_order(invalid_order_missing_field)
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any(error.field == "quantity" for error in result.errors)

    # Test invalid order (invalid direction)
    invalid_order_direction = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "INVALID",
        "order_type": "MARKET",
    }

    result = validate_order(invalid_order_direction)
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any(error.field == "direction" for error in result.errors)

    # Test invalid limit order (missing limit price)
    invalid_limit_order = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "BUY",
        "order_type": "LIMIT",
        # Missing limit_price
    }

    result = validate_order(invalid_limit_order)
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any(error.field == "limit_price" for error in result.errors)

    # Test order with warning (large quantity)
    large_order = {
        "symbol": "AAPL",
        "quantity": 20000,  # Large quantity
        "direction": "BUY",
        "order_type": "MARKET",
    }

    result = validate_order(large_order)
    assert result.is_valid  # Still valid despite warning
    assert len(result.warnings) > 0
    assert any(warning.field == "quantity" for warning in result.warnings)
