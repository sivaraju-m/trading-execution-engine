"""
Risk Management System
=====================

Comprehensive risk management for trading operations.

Author: SJ Trading
Licensed by SJ Trading
"""

from datetime import datetime
from typing import Any, Dict, List

from ..utils.logger import get_logger

logger = get_logger(__name__)


class RiskManager:
    """
    Risk management system for trading operations
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.daily_limits = {}
        self.current_positions = {}
        self.daily_pnl = 0.0
        self.risk_violations = []

        # Risk parameters
        self.max_position_size_pct = config.get("max_position_size_pct", 5)
        self.max_daily_loss_pct = config.get("max_daily_loss_pct", 3)
        self.stop_loss_pct = config.get("stop_loss_pct", 2)
        self.max_concentration_pct = config.get("max_concentration_pct", 20)

        # Portfolio parameters
        self.total_capital = config.get("total_capital", 1000000)  # 10 Lakh default

        logger.info("Risk management system initialized")

    async def reset_daily_limits(self):
        """Reset daily risk limits"""
        self.daily_limits = {
            "max_daily_loss": self.total_capital * (self.max_daily_loss_pct / 100),
            "max_position_size": self.total_capital
            * (self.max_position_size_pct / 100),
            "trades_count": 0,
            "daily_pnl": 0.0,
            "violations": [],
        }

        self.daily_pnl = 0.0
        self.risk_violations = []

        logger.info("Daily risk limits reset")

    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Validate a signal against risk parameters

        Returns True if signal passes all risk checks
        """
        symbol = signal.get("symbol")
        action = signal.get("action", "").upper()
        quantity = signal.get("quantity", 0)
        price = signal.get("price", 0)

        # Basic validation
        if not all([symbol, action in ["BUY", "SELL"], quantity > 0, price > 0]):
            self._log_violation("invalid_signal_parameters", signal)
            return False

        # Calculate position value
        position_value = quantity * price

        # Check position size limit
        if position_value > self.daily_limits["max_position_size"]:
            self._log_violation(
                "position_size_exceeded",
                {
                    "signal": signal,
                    "position_value": position_value,
                    "max_allowed": self.daily_limits["max_position_size"],
                },
            )
            return False

        # Check daily loss limit
        if self.daily_pnl < -self.daily_limits["max_daily_loss"]:
            self._log_violation(
                "daily_loss_limit_exceeded",
                {
                    "current_pnl": self.daily_pnl,
                    "max_loss": -self.daily_limits["max_daily_loss"],
                },
            )
            return False

        # Check concentration risk
        if not await self._validate_concentration_risk(symbol, position_value, action):
            return False

        # Check stop loss requirements
        if not await self._validate_stop_loss(signal):
            return False

        logger.debug(f"Signal validated: {action} {quantity} {symbol}")
        return True

    async def _validate_concentration_risk(
        self, symbol: str, position_value: float, action: str
    ) -> bool:
        """Validate concentration risk limits"""
        current_exposure = self.current_positions.get(symbol, {}).get("value", 0)

        if action == "BUY":
            new_exposure = current_exposure + position_value
        else:
            new_exposure = max(0, current_exposure - position_value)

        concentration_pct = (new_exposure / self.total_capital) * 100

        if concentration_pct > self.max_concentration_pct:
            self._log_violation(
                "concentration_risk_exceeded",
                {
                    "symbol": symbol,
                    "concentration_pct": concentration_pct,
                    "max_allowed_pct": self.max_concentration_pct,
                },
            )
            return False

        return True

    async def _validate_stop_loss(self, signal: Dict[str, Any]) -> bool:
        """Validate stop loss requirements"""
        stop_loss = signal.get("stop_loss")
        price = signal.get("price", 0)
        action = signal.get("action", "").upper()

        if not stop_loss:
            self._log_violation("missing_stop_loss", signal)
            return False

        # Calculate stop loss percentage
        if action == "BUY":
            stop_loss_pct = ((price - stop_loss) / price) * 100
        else:
            stop_loss_pct = ((stop_loss - price) / price) * 100

        if stop_loss_pct > self.stop_loss_pct:
            self._log_violation(
                "stop_loss_too_wide",
                {
                    "signal": signal,
                    "stop_loss_pct": stop_loss_pct,
                    "max_allowed_pct": self.stop_loss_pct,
                },
            )
            return False

        return True

    def _log_violation(self, violation_type: str, details: Any):
        """Log a risk violation"""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "type": violation_type,
            "details": details,
        }

        self.risk_violations.append(violation)
        self.daily_limits["violations"].append(violation)

        logger.warning(f"Risk violation: {violation_type}")

    async def update_position(
        self, symbol: str, action: str, quantity: int, price: float
    ):
        """Update position tracking"""
        if symbol not in self.current_positions:
            self.current_positions[symbol] = {"quantity": 0, "avg_price": 0, "value": 0}

        position = self.current_positions[symbol]

        if action.upper() == "BUY":
            total_quantity = position["quantity"] + quantity
            total_value = (position["quantity"] * position["avg_price"]) + (
                quantity * price
            )

            position["quantity"] = total_quantity
            position["avg_price"] = (
                total_value / total_quantity if total_quantity > 0 else 0
            )
            position["value"] = total_value

        elif action.upper() == "SELL":
            position["quantity"] = max(0, position["quantity"] - quantity)
            if position["quantity"] == 0:
                position["avg_price"] = 0
                position["value"] = 0
            else:
                position["value"] = position["quantity"] * position["avg_price"]

        logger.debug(
            f"Position updated: {symbol} - {position['quantity']} @ ₹{position['avg_price']:.2f}"
        )

    async def update_pnl(self, pnl_change: float):
        """Update daily P&L tracking"""
        self.daily_pnl += pnl_change
        self.daily_limits["daily_pnl"] = self.daily_pnl

        # Check if daily loss limit is breached
        if self.daily_pnl < -self.daily_limits["max_daily_loss"]:
            self._log_violation(
                "daily_loss_limit_breached",
                {
                    "current_pnl": self.daily_pnl,
                    "limit": -self.daily_limits["max_daily_loss"],
                },
            )

    async def generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily risk management summary"""
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "risk_limits": self.daily_limits,
            "current_positions": self.current_positions,
            "daily_pnl": self.daily_pnl,
            "risk_violations": self.risk_violations,
            "risk_metrics": {
                "max_position_utilization_pct": self._calculate_max_position_utilization(),
                "concentration_risk_pct": self._calculate_concentration_risk(),
                "daily_loss_utilization_pct": abs(self.daily_pnl)
                / self.daily_limits["max_daily_loss"]
                * 100,
                "total_violations": len(self.risk_violations),
            },
        }

        logger.info(
            f"Risk summary: {len(self.risk_violations)} violations, "
            f"P&L: ₹{self.daily_pnl:.2f}, "
            f"Max position: {summary['risk_metrics']['max_position_utilization_pct']:.1f}%"
        )

        return summary

    def _calculate_max_position_utilization(self) -> float:
        """Calculate maximum position size utilization"""
        max_position_value = max(
            [pos["value"] for pos in self.current_positions.values()], default=0
        )
        return (max_position_value / self.daily_limits["max_position_size"]) * 100

    def _calculate_concentration_risk(self) -> float:
        """Calculate concentration risk percentage"""
        max_exposure = max(
            [pos["value"] for pos in self.current_positions.values()], default=0
        )
        return (max_exposure / self.total_capital) * 100

    def get_available_buying_power(self) -> float:
        """Get available buying power considering risk limits"""
        total_position_value = sum(
            pos["value"] for pos in self.current_positions.values()
        )
        remaining_capital = self.total_capital - total_position_value

        # Consider daily loss impact
        if self.daily_pnl < 0:
            remaining_capital += self.daily_pnl  # Reduce available capital by losses

        return max(0, remaining_capital)

    def is_trading_halted(self) -> bool:
        """Check if trading should be halted due to risk limits"""
        # Halt if daily loss limit exceeded
        if self.daily_pnl < -self.daily_limits["max_daily_loss"]:
            return True

        # Halt if too many violations
        if len(self.risk_violations) > 10:
            return True

        return False
