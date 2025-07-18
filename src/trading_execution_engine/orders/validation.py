"""
Order validation module for trading execution engine.

This module provides utilities for validating orders before submission to brokers.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union


class OrderType(Enum):
    """Order types supported by the trading system."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderDirection(Enum):
    """Order direction (buy/sell)."""
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    """Time in force options for orders."""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class ValidationError:
    """Represents an order validation error."""
    field: str
    message: str
    severity: str  # 'error' or 'warning'


@dataclass
class ValidationResult:
    """Result of order validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]


def validate_order(
    order: Dict[str, Union[str, float, int]]
) -> ValidationResult:
    """
    Validate a trading order before submission.
    
    Args:
        order: Dictionary with order details
        
    Returns:
        ValidationResult object with validation status and any errors/warnings
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ["symbol", "quantity", "direction", "order_type"]
    for field in required_fields:
        if field not in order or not order[field]:
            errors.append(
                ValidationError(
                    field=field,
                    message=f"Missing required field: {field}",
                    severity="error"
                )
            )
    
    # If critical fields are missing, return early
    if len(errors) > 0:
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    # Validate quantity
    quantity = order.get("quantity", 0)
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        errors.append(
            ValidationError(
                field="quantity",
                message="Quantity must be a positive number",
                severity="error"
            )
        )
    
    # Validate direction
    direction = order.get("direction", "")
    valid_directions = [d.value for d in OrderDirection]
    if direction not in valid_directions:
        errors.append(
            ValidationError(
                field="direction",
                message=f"Invalid direction. Must be one of: {valid_directions}",
                severity="error"
            )
        )
    
    # Validate order type
    order_type = order.get("order_type", "")
    valid_order_types = [t.value for t in OrderType]
    if order_type not in valid_order_types:
        errors.append(
            ValidationError(
                field="order_type",
                message=f"Invalid order type. Must be one of: {valid_order_types}",
                severity="error"
            )
        )
    
    # Validate order type specific requirements
    if order_type == OrderType.LIMIT.value and "limit_price" not in order:
        errors.append(
            ValidationError(
                field="limit_price",
                message="Limit price is required for LIMIT orders",
                severity="error"
            )
        )
    
    if order_type == OrderType.STOP.value and "stop_price" not in order:
        errors.append(
            ValidationError(
                field="stop_price",
                message="Stop price is required for STOP orders",
                severity="error"
            )
        )
    
    if order_type == OrderType.STOP_LIMIT.value:
        if "stop_price" not in order:
            errors.append(
                ValidationError(
                    field="stop_price",
                    message="Stop price is required for STOP_LIMIT orders",
                    severity="error"
                )
            )
        if "limit_price" not in order:
            errors.append(
                ValidationError(
                    field="limit_price",
                    message="Limit price is required for STOP_LIMIT orders",
                    severity="error"
                )
            )
    
    # Validate prices if present
    if "limit_price" in order:
        limit_price = order.get("limit_price", 0)
        if not isinstance(limit_price, (int, float)) or limit_price <= 0:
            errors.append(
                ValidationError(
                    field="limit_price",
                    message="Limit price must be a positive number",
                    severity="error"
                )
            )
    
    if "stop_price" in order:
        stop_price = order.get("stop_price", 0)
        if not isinstance(stop_price, (int, float)) or stop_price <= 0:
            errors.append(
                ValidationError(
                    field="stop_price",
                    message="Stop price must be a positive number",
                    severity="error"
                )
            )
    
    # Optional validations
    # Time in force
    if "time_in_force" in order:
        time_in_force = order.get("time_in_force", "")
        valid_tif = [tif.value for tif in TimeInForce]
        if time_in_force not in valid_tif:
            errors.append(
                ValidationError(
                    field="time_in_force",
                    message=f"Invalid time in force. Must be one of: {valid_tif}",
                    severity="error"
                )
            )
    
    # Validate symbol format (basic check)
    symbol = order.get("symbol", "")
    if not symbol or len(symbol) < 1 or len(symbol) > 20:
        errors.append(
            ValidationError(
                field="symbol",
                message="Invalid symbol format",
                severity="error"
            )
        )
    
    # Add warnings for large orders
    if quantity > 10000:
        warnings.append(
            ValidationError(
                field="quantity",
                message="Large order quantity detected",
                severity="warning"
            )
        )
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_orders(orders: List[Dict[str, Union[str, float, int]]]) -> Dict[int, ValidationResult]:
    """
    Validate multiple orders at once.
    
    Args:
        orders: List of order dictionaries
        
    Returns:
        Dictionary mapping order index to ValidationResult
    """
    results = {}
    for idx, order in enumerate(orders):
        results[idx] = validate_order(order)
    return results
