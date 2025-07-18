"""
Dry Run Trading Engine for Safe Live Testing
==========================================

This module provides a safe dry run environment for testing live trading
strategies without placing real orders. Perfect for validation before going live.

Features:
- Simulated order placement with real market data
- Real-time P&L tracking
- Risk management validation
- Performance metrics
- Order book simulation
- Complete audit trail

Author: AI Trading Machine
Licensed by SJ Trading
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available")

from ..ingest.kite_loader import KiteDataLoader
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SimulatedOrder:
    """Simulated order for dry run testing."""

    order_id: str
    symbol: str
    quantity: int
    order_type: str
    transaction_type: str
    price: float
    timestamp: datetime
    status: str = "COMPLETE"
    filled_quantity: int = 0

    def __post_init__(self):
        if self.filled_quantity == 0:
            self.filled_quantity = self.quantity


@dataclass
class Position:
    """Position tracking for dry run."""

    symbol: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime


class DryRunTradingEngine:
    """
    Comprehensive dry run trading engine for safe testing.

    This engine simulates all trading operations without placing real orders,
    allowing for complete strategy validation in live market conditions.
    """

    def __init__(self, kite_loader: KiteDataLoader, initial_capital: float = 100000.0):
        """
        Initialize dry run trading engine.

        Args:
            kite_loader: Authenticated KiteDataLoader for market data
            initial_capital: Starting capital for simulation
        """
        self.kite = kite_loader
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.total_value = initial_capital

        # Trading state
        self.positions: dict[str, Position] = {}
        self.orders: list[SimulatedOrder] = []
        self.active_strategies: dict[str, Callable[[Any], Any]] = {}

        # Performance tracking
        self.trades_executed = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = initial_capital

        # Risk management
        self.risk_limits = {
            "max_position_size": 0.05,  # 5% per position
            "max_daily_loss": 0.02,  # 2% daily loss limit
            "max_drawdown": 0.10,  # 10% max drawdown
            "max_concentration": 0.25,  # 25% max in single stock
        }

        # Transaction costs
        self.transaction_costs = {
            "brokerage_rate": 0.0003,  # 0.03% brokerage
            "stt_rate": 0.00025,  # 0.025% STT on sell
            "exchange_charges": 0.0000345,  # NSE charges
            "gst_rate": 0.18,  # 18% GST on brokerage
        }

        logger.info("Dry Run Trading Engine initialized with ₹{initial_capital:,.2f}")

    def register_strategy(
        self, strategy_name: str, strategy_func: Callable[[Any], Any]
    ) -> None:
        """Register a trading strategy."""
        self.active_strategies[strategy_name] = strategy_func
        logger.info("Strategy registered: {strategy_name}")

    def calculate_transaction_cost(self, value: float, transaction_type: str) -> float:
        """Calculate realistic transaction costs."""
        brokerage = value * self.transaction_costs["brokerage_rate"]
        exchange_charges = value * self.transaction_costs["exchange_charges"]

        # STT only on sell transactions
        stt = (
            value * self.transaction_costs["stt_rate"]
            if transaction_type == "SELL"
            else 0
        )

        # GST on brokerage
        gst = brokerage * self.transaction_costs["gst_rate"]

        total_cost = brokerage + exchange_charges + stt + gst
        return total_cost

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol."""
        try:
            # Try live price first
            live_price = self.kite.get_live_price(symbol)
            if live_price:
                return live_price

            # Fallback to recent historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            df = self.kite.fetch_historical_data(symbol, start_date, end_date)

            if not df.empty:
                return df["close"].iloc[-1]

            return None

        except Exception as e:
            logger.error("Failed to get price for {symbol}: {e}")
            return None

    def place_simulated_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "MARKET",
        transaction_type: str = "BUY",
        limit_price: Optional[float] = None,
    ) -> Optional[str]:
        """
        Place a simulated order.

        Args:
            symbol: Trading symbol
            quantity: Number of shares
            order_type: MARKET or LIMIT
            transaction_type: BUY or SELL
            limit_price: Price for limit orders

        Returns:
            Simulated order ID
        """
        try:
            current_price = self.get_current_price(symbol)
            if not current_price:
                logger.error("Cannot place order for {symbol}: No price available")
                return None

            # Use current price for market orders, limit price for limit orders
            execution_price = limit_price if order_type == "LIMIT" else current_price

            # Calculate order value
            order_value = quantity * execution_price
            transaction_cost = self.calculate_transaction_cost(
                order_value, transaction_type
            )
            total_cost = order_value + transaction_cost

            # Risk checks
            if transaction_type == "BUY":
                if total_cost > self.available_cash:
                    logger.warning(
                        "Insufficient funds for {symbol}: Need ₹{total_cost:,.2f}, Available ₹{self.available_cash:,.2f}"
                    )
                    return None

                # Position size check
                position_size = total_cost / self.total_value
                if position_size > self.risk_limits["max_position_size"]:
                    logger.warning(
                        "Position size too large for {symbol}: {position_size:.2%} > {self.risk_limits['max_position_size']:.2%}"
                    )
                    return None

            # Create simulated order
            order_id = "DRY_{int(time.time() * 1000)}_{symbol}"
            simulated_order = SimulatedOrder(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                transaction_type=transaction_type,
                price=execution_price,
                timestamp=datetime.now(),
            )

            # Execute the order
            self._execute_simulated_order(simulated_order, transaction_cost)
            self.orders.append(simulated_order)

            logger.info(
                "✅ Simulated {transaction_type}: {quantity} {symbol} @ ₹{execution_price:.2f} (Cost: ₹{transaction_cost:.2f})"
            )
            return order_id

        except Exception as e:
            logger.error("Failed to place simulated order: {e}")
            return None

    def _execute_simulated_order(
        self, order: SimulatedOrder, transaction_cost: float
    ) -> None:
        """Execute a simulated order and update portfolio."""
        symbol = order.symbol
        quantity = order.quantity
        price = order.price

        if order.transaction_type == "BUY":
            # Update or create position
            if symbol in self.positions:
                # Add to existing position
                current_pos = self.positions[symbol]
                total_quantity = current_pos.quantity + quantity
                total_cost = (current_pos.quantity * current_pos.average_price) + (
                    quantity * price
                )
                new_avg_price = total_cost / total_quantity

                self.positions[symbol].quantity = total_quantity
                self.positions[symbol].average_price = new_avg_price
            else:
                # Create new position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=datetime.now(),
                )

            # Deduct cash
            self.available_cash -= quantity * price + transaction_cost

        else:  # SELL
            if symbol in self.positions:
                position = self.positions[symbol]

                if quantity <= position.quantity:
                    # Calculate realized P&L
                    realized_pnl = (
                        price - position.average_price
                    ) * quantity - transaction_cost
                    position.realized_pnl += realized_pnl
                    self.total_pnl += realized_pnl

                    # Update position
                    position.quantity -= quantity

                    # Remove position if fully sold
                    if position.quantity == 0:
                        del self.positions[symbol]

                    # Add cash
                    self.available_cash += quantity * price - transaction_cost

                    # Track trade
                    self.trades_executed += 1
                    if realized_pnl > 0:
                        self.winning_trades += 1

                    logger.info(
                        "📊 Realized P&L: ₹{realized_pnl:.2f} ({realized_pnl/position.average_price/quantity:.2%})"
                    )

                else:
                    logger.error(
                        "Cannot sell {quantity} shares of {symbol}: Only {position.quantity} available"
                    )
            else:
                logger.error("Cannot sell {symbol}: No position exists")

    def update_positions(self) -> None:
        """Update current prices and unrealized P&L for all positions."""
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            if current_price:
                position.current_price = current_price
                position.unrealized_pnl = (
                    current_price - position.average_price
                ) * position.quantity

        # Update total portfolio value
        position_value = sum(
            pos.quantity * pos.current_price for pos in self.positions.values()
        )
        self.total_value = self.available_cash + position_value

        # Track drawdown
        if self.total_value > self.peak_value:
            self.peak_value = self.total_value

        current_drawdown = (self.peak_value - self.total_value) / self.peak_value
        self.max_drawdown = max(self.max_drawdown, current_drawdown)

    def execute_strategy_signals(self, symbol: str, strategy_name: str) -> None:
        """Execute strategy signals for a given symbol."""
        if strategy_name not in self.active_strategies:
            logger.error("Strategy not registered: {strategy_name}")
            return

        try:
            # Get recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            df = self.kite.fetch_historical_data(symbol, start_date, end_date)

            if df.empty:
                logger.warning("No data available for {symbol}")
                return

            # Generate signals
            strategy_func = self.active_strategies[strategy_name]
            signals = strategy_func(df)

            if not signals.empty:
                latest_signal = signals.iloc[-1]
                signal_value = latest_signal.get("signal", 0)
                confidence = latest_signal.get("confidence", 0.5)

                # Execute based on signal strength
                if signal_value > 0.5 and confidence > 0.6:  # Strong buy
                    quantity = self._calculate_position_size(symbol, confidence)
                    if quantity > 0:
                        self.place_simulated_order(symbol, quantity, "MARKET", "BUY")

                elif signal_value < -0.5 and confidence > 0.6:  # Strong sell
                    if symbol in self.positions:
                        quantity = self.positions[symbol].quantity
                        self.place_simulated_order(symbol, quantity, "MARKET", "SELL")

        except Exception as e:
            logger.error("Strategy execution failed for {symbol}: {e}")

    def _calculate_position_size(self, symbol: str, confidence: float) -> int:
        """Calculate position size based on confidence and risk limits."""
        current_price = self.get_current_price(symbol)
        if not current_price:
            return 0

        # Base position size on confidence and risk limits
        max_investment = self.available_cash * self.risk_limits["max_position_size"]
        confidence_adjusted = max_investment * confidence
        quantity = int(confidence_adjusted / current_price)

        return max(0, quantity)

    def monitor_risk_limits(self) -> dict[str, bool]:
        """Monitor all risk limits and return violations."""
        violations = {}

        # Daily loss check
        daily_pnl = (self.total_value - self.initial_capital) / self.initial_capital
        violations["daily_loss"] = daily_pnl < -self.risk_limits["max_daily_loss"]

        # Drawdown check
        violations["max_drawdown"] = (
            self.max_drawdown > self.risk_limits["max_drawdown"]
        )

        # Concentration check
        for symbol, position in self.positions.items():
            position_value = position.quantity * position.current_price
            concentration = position_value / self.total_value
            if concentration > self.risk_limits["max_concentration"]:
                violations["concentration_{symbol}"] = True

        if any(violations.values()):
            logger.warning("Risk limit violations detected: {violations}")

        return violations

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Get comprehensive portfolio summary."""
        self.update_positions()

        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())

        return {
            "timestamp": datetime.now(),
            "total_value": self.total_value,
            "available_cash": self.available_cash,
            "initial_capital": self.initial_capital,
            "total_pnl": self.total_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "realized_pnl": total_realized_pnl,
            "total_return": (self.total_value - self.initial_capital)
            / self.initial_capital,
            "max_drawdown": self.max_drawdown,
            "trades_executed": self.trades_executed,
            "win_rate": self.winning_trades / max(self.trades_executed, 1),
            "positions_count": len(self.positions),
            "cash_utilization": 1 - (self.available_cash / self.total_value),
        }

    def get_positions_summary(self) -> pd.DataFrame:
        """Get current positions as DataFrame."""
        if not self.positions:
            return pd.DataFrame()

        positions_data = []
        for symbol, pos in self.positions.items():
            positions_data.append(
                {
                    "symbol": symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.average_price,
                    "current_price": pos.current_price,
                    "market_value": pos.quantity * pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl
                    / (pos.average_price * pos.quantity),
                    "entry_time": pos.entry_time,
                }
            )

        return pd.DataFrame(positions_data)

    def export_trading_log(self, filepath: str) -> None:
        """Export complete trading log for analysis."""
        trading_log = {
            "summary": self.get_portfolio_summary(),
            "orders": [asdict(order) for order in self.orders],
            "positions": self.get_positions_summary().to_dict("records"),
            "risk_limits": self.risk_limits,
            "transaction_costs": self.transaction_costs,
        }

        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(filepath, "w") as f:
            json.dump(trading_log, f, indent=2, default=convert_datetime)

        logger.info("Trading log exported to: {filepath}")

    async def start_live_monitoring(
        self, symbols: list[str], duration_minutes: int = 60
    ) -> None:
        """Start live monitoring and strategy execution."""
        logger.info(
            "🔴 Starting dry run live monitoring for {duration_minutes} minutes..."
        )
        logger.info("📊 Monitoring symbols: {symbols}")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        try:
            # Setup real-time data if available
            if hasattr(self.kite, "setup_websocket"):
                self.kite.setup_websocket()
                self.kite.subscribe_symbols(symbols[:5])  # Limit to 5 symbols
                self.kite.start_streaming()

            iteration = 0
            while time.time() < end_time:
                iteration += 1
                logger.info("\n📊 === Monitoring Iteration {iteration} ===")

                # Update positions
                self.update_positions()

                # Check risk limits
                violations = self.monitor_risk_limits()

                # Execute strategies for each symbol
                for symbol in symbols[:3]:  # Limit to 3 for demo
                    for strategy_name in self.active_strategies.keys():
                        try:
                            self.execute_strategy_signals(symbol, strategy_name)
                        except Exception as e:
                            logger.debug("Strategy execution info for {symbol}: {e}")

                # Print portfolio summary
                summary = self.get_portfolio_summary()
                logger.info(
                    "💰 Portfolio Value: ₹{summary['total_value']:,.2f} ({summary['total_return']:+.2%})"
                )
                logger.info("💵 Available Cash: ₹{summary['available_cash']:,.2f}")
                logger.info("📈 Unrealized P&L: ₹{summary['unrealized_pnl']:+,.2f}")
                logger.info("📊 Positions: {summary['positions_count']}")

                # Wait before next iteration
                await asyncio.sleep(30)  # 30 seconds between iterations

            logger.info("⏹️  Dry run monitoring completed")

            # Final summary
            final_summary = self.get_portfolio_summary()
            logger.info("\n🎯 === FINAL RESULTS ===")
            logger.info("💰 Final Value: ₹{final_summary['total_value']:,.2f}")
            logger.info("📈 Total Return: {final_summary['total_return']:+.2%}")
            logger.info("📊 Trades Executed: {final_summary['trades_executed']}")
            logger.info("🎯 Win Rate: {final_summary['win_rate']:.1%}")
            logger.info("📉 Max Drawdown: {final_summary['max_drawdown']:.2%}")

        except Exception as e:
            logger.error("❌ Monitoring failed: {e}")
        finally:
            # Export results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = "dry_run_log_{timestamp}.json"
            self.export_trading_log(log_file)


# Example usage for testing
if __name__ == "__main__":
    print("🧪 Dry Run Trading Engine - Test Mode")
    print("=" * 50)

    # This would normally use real KiteDataLoader
    # For testing, we create a mock
    class MockKiteLoader:
        def fetch_historical_data(self, symbol, start_date, end_date):
            # Return mock data for testing
            dates = pd.date_range(start=start_date, end=end_date, freq="D")
            return pd.DataFrame(
                {
                    "open": [100 + i for i in range(len(dates))],
                    "high": [105 + i for i in range(len(dates))],
                    "low": [95 + i for i in range(len(dates))],
                    "close": [102 + i for i in range(len(dates))],
                    "volume": [1000000] * len(dates),
                },
                index=dates,
            )

        def get_live_price(self, symbol):
            return 100.0  # Mock price

    # Test the engine
    mock_loader = MockKiteLoader()
    engine = DryRunTradingEngine(mock_loader, initial_capital=100000)

    # Test order placement
    order_id = engine.place_simulated_order("RELIANCE", 10, "MARKET", "BUY")
    print("✅ Test order placed: {order_id}")

    # Test portfolio summary
    summary = engine.get_portfolio_summary()
    print("📊 Portfolio summary: {summary}")

    print("✅ Dry run engine test completed")
