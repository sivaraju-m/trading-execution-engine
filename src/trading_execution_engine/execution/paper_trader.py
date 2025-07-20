"""
Paper Trading Engine
===================

Simulates trading operations for backtesting and strategy validation.

Author: SJ Trading
Licensed by SJ Trading
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PaperTrader:
    """
    Paper trading engine for strategy validation
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.portfolio = {}
        self.trades = []
        self.daily_pnl = 0.0
        self.initial_capital = config.get("initial_capital", 1000000)
        self.available_capital = self.initial_capital
        self.commission_per_trade = config.get("commission_per_trade", 20)
        self.slippage_bps = config.get("slippage_bps", 5)  # basis points

        logger.info(
            f"Paper trader initialized with capital: ₹{self.initial_capital:,.2f}"
        )

    async def initialize_daily_session(self):
        """Initialize daily paper trading session"""
        self.daily_pnl = 0.0
        self.trades = []

        logger.info("Daily paper trading session initialized")

    async def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a signal in paper trading mode"""
        if not self.config.get("enabled", True):
            return {"executed": False, "reason": "Paper trading disabled"}

        symbol = signal.get("symbol")
        action = signal.get("action", "").upper()
        quantity = signal.get("quantity", 0)
        price = signal.get("price", 0)

        if not all([symbol, action in ["BUY", "SELL"], quantity > 0, price > 0]):
            return {"executed": False, "reason": "Invalid signal parameters"}

        # Apply slippage
        slippage_factor = 1 + (self.slippage_bps / 10000)
        if action == "BUY":
            execution_price = price * slippage_factor
        else:
            execution_price = price / slippage_factor

        # Calculate trade value
        trade_value = execution_price * quantity
        total_cost = trade_value + self.commission_per_trade

        # Check available capital for BUY orders
        if action == "BUY" and total_cost > self.available_capital:
            return {
                "executed": False,
                "reason": f"Insufficient capital: need ₹{total_cost:,.2f}, have ₹{self.available_capital:,.2f}",
            }

        # Execute the trade
        trade = {
            "trade_id": f"paper_{len(self.trades) + 1}",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "signal_price": price,
            "execution_price": execution_price,
            "trade_value": trade_value,
            "commission": self.commission_per_trade,
            "total_cost": total_cost,
            "slippage_bps": self.slippage_bps,
            "signal_data": signal,
        }

        # Update portfolio
        self._update_portfolio(trade)

        # Update available capital
        if action == "BUY":
            self.available_capital -= total_cost
        else:
            self.available_capital += trade_value - self.commission_per_trade

        # Calculate P&L
        pnl = self._calculate_trade_pnl(trade)
        trade["pnl"] = pnl
        self.daily_pnl += pnl

        self.trades.append(trade)

        logger.info(
            f"Paper trade executed: {action} {quantity} {symbol} @ ₹{execution_price:.2f} "
            f"(P&L: ₹{pnl:.2f})"
        )

        return {
            "executed": True,
            "trade_id": trade["trade_id"],
            "execution_price": execution_price,
            "trade_value": trade_value,
            "pnl": pnl,
            "available_capital": self.available_capital,
        }

    def _update_portfolio(self, trade: Dict[str, Any]):
        """Update portfolio with executed trade"""
        symbol = trade["symbol"]
        action = trade["action"]
        quantity = trade["quantity"]

        if symbol not in self.portfolio:
            self.portfolio[symbol] = {
                "quantity": 0,
                "avg_price": 0,
                "total_cost": 0,
                "realized_pnl": 0,
            }

        position = self.portfolio[symbol]

        if action == "BUY":
            # Add to position
            total_quantity = position["quantity"] + quantity
            total_cost = position["total_cost"] + trade["total_cost"]
            position["avg_price"] = (
                total_cost / total_quantity if total_quantity > 0 else 0
            )
            position["quantity"] = total_quantity
            position["total_cost"] = total_cost

        elif action == "SELL":
            # Reduce position
            if position["quantity"] >= quantity:
                # Calculate realized P&L
                avg_cost = position["avg_price"]
                sell_proceeds = trade["trade_value"] - trade["commission"]
                cost_basis = avg_cost * quantity
                realized_pnl = sell_proceeds - cost_basis

                position["quantity"] -= quantity
                position["total_cost"] -= cost_basis
                position["realized_pnl"] += realized_pnl

                trade["realized_pnl"] = realized_pnl
            else:
                logger.warning(
                    f"Attempting to sell {quantity} {symbol}, but only have {position['quantity']}"
                )

    def _calculate_trade_pnl(self, trade: Dict[str, Any]) -> float:
        """Calculate P&L for a trade"""
        # For paper trading, we'll use a simple mark-to-market approach
        # In real implementation, this would use current market prices

        signal_price = trade["signal_price"]
        execution_price = trade["execution_price"]
        quantity = trade["quantity"]
        action = trade["action"]

        if action == "BUY":
            # For demo, assume immediate small gain/loss based on slippage
            return (signal_price - execution_price) * quantity
        else:
            # For SELL, calculate based on average cost
            return trade.get("realized_pnl", 0)

    async def close_daily_session(self) -> Dict[str, Any]:
        """Close daily paper trading session and generate summary"""
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "initial_capital": self.initial_capital,
            "available_capital": self.available_capital,
            "capital_utilized": self.initial_capital - self.available_capital,
            "daily_pnl": self.daily_pnl,
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len([t for t in self.trades if t["action"] == "SELL"]),
            "total_commission": sum(t["commission"] for t in self.trades),
            "portfolio": self.portfolio.copy(),
            "trades": self.trades.copy(),
        }

        # Calculate portfolio value
        portfolio_value = sum(
            pos["quantity"] * pos["avg_price"] for pos in self.portfolio.values()
        )
        summary["portfolio_value"] = portfolio_value
        summary["total_value"] = self.available_capital + portfolio_value
        summary["return_pct"] = (
            (summary["total_value"] - self.initial_capital) / self.initial_capital * 100
        )

        logger.info(
            f"Paper trading session closed: {summary['total_trades']} trades, "
            f"P&L: ₹{self.daily_pnl:,.2f}, Return: {summary['return_pct']:.2f}%"
        )

        return summary

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        return {
            "positions": self.portfolio.copy(),
            "available_capital": self.available_capital,
            "daily_pnl": self.daily_pnl,
            "total_trades": len(self.trades),
        }

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history"""
        return self.trades.copy()
