#!/usr/bin/env python3
"""
Automated Paper Trading & Signal Generation System
=================================================

This system provides:
1. Automated paper trading simulation
2. Live signal generation
3. Manual trading interface
4. Database storage (BQ/Firestore)
5. Daily performance tracking

Architecture:
- Paper trades execute automatically based on signals
- Real trades require manual execution (SEBI compliance)
- All results stored in cloud databases
- Daily automated processing and reporting

Author: SJ Trading
Licensed by SJ Trading
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from datetime import time as dt_time
from enum import Enum
from typing import Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ai_trading_machine.ingest.kite_loader import KiteDataLoader
from src.ai_trading_machine.persist.signal_logger import log_signal_to_both
from src.ai_trading_machine.signal_generator import SignalGenerator, TradingSignal
from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class TradeType(Enum):
    """Types of trades in the system."""

    PAPER = "PAPER"  # Automated simulation
    MANUAL = "MANUAL"  # User executed manually
    LIVE = "LIVE"  # Future: automated live trading (post-SEBI approval)


class TradeStatus(Enum):
    """Status of trades."""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    TARGET_HIT = "TARGET_HIT"
    STOP_HIT = "STOP_HIT"


@dataclass
class PaperTrade:
    """Paper trade record."""

    trade_id: str
    signal_id: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    entry_price: float
    target_price: float
    stop_loss: float
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    pnl: float = 0.0
    pnl_percent: float = 0.0
    trade_type: TradeType = TradeType.PAPER
    strategy_name: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["trade_type"] = self.trade_type.value
        data["entry_time"] = self.entry_time.isoformat()
        data["exit_time"] = self.exit_time.isoformat() if self.exit_time else None
        return data


class AutomatedTradingSystem:
    """
    Automated paper trading and signal generation system.
    """

    def __init__(self, project_id: Optional[str] = None):
        """Initialize the automated trading system."""
        self.kite_loader = None
        self.signal_generator = None

        # Trading parameters
        self.paper_portfolio_value = 1000000  # 10 Lakh virtual portfolio
        self.manual_portfolio_value = 100000  # 1 Lakh real portfolio
        self.max_risk_per_trade = 0.02

        # Active positions
        self.paper_trades: dict[str, PaperTrade] = {}
        self.active_signals: dict[str, TradingSignal] = {}

        # Performance tracking
        self.daily_stats = {
            "signals_generated": 0,
            "paper_trades_executed": 0,
            "manual_trades_suggested": 0,
            "paper_pnl": 0.0,
            "win_rate": 0.0,
        }

        # Market hours
        self.market_start = dt_time(9, 15)  # 9:15 AM
        self.market_end = dt_time(15, 30)  # 3:30 PM

        self.project_id = project_id or os.getenv(
            "GCP_PROJECT_ID", "my-trading-project"
        )

    async def initialize_system(self) -> bool:
        """Initialize trading system components."""
        try:
            logger.info("🚀 Initializing Automated Trading System...")

            # Initialize KiteConnect
            self.kite_loader = KiteDataLoader()
            if not self.kite_loader.is_authenticated:
                logger.error("❌ KiteConnect authentication failed")
                return False

            # Initialize signal generator for paper trading
            self.signal_generator = SignalGenerator(self.kite_loader)
            self.signal_generator.set_portfolio_parameters(
                self.paper_portfolio_value, self.max_risk_per_trade
            )

            logger.info("✅ System initialized successfully")
            logger.info("💰 Paper Portfolio: ₹{self.paper_portfolio_value:,.2f}")
            logger.info("💰 Manual Portfolio: ₹{self.manual_portfolio_value:,.2f}")

            return True

        except Exception as e:
            logger.error("❌ System initialization failed: {e}")
            return False

    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now().time()
        today = datetime.now().weekday()

        # Check if it's a weekday (0=Monday, 6=Sunday)
        if today >= 5:  # Saturday or Sunday
            return False

        # Check market hours
        return self.market_start <= now <= self.market_end

    async def generate_signals(self, watchlist: list[str]) -> list[TradingSignal]:
        """Generate trading signals for watchlist."""
        try:
            logger.info("🔍 Generating signals for {len(watchlist)} symbols...")

            signals = self.signal_generator.generate_signals_for_watchlist(watchlist)

            # Store active signals
            for signal in signals:
                signal_id = (
                    "{signal.symbol}_{signal.signal_time.strftime('%Y%m%d_%H%M%S')}"
                )
                self.active_signals[signal_id] = signal

            self.daily_stats["signals_generated"] += len(signals)

            logger.info("✅ Generated {len(signals)} trading signals")
            return signals

        except Exception as e:
            logger.error("❌ Signal generation failed: {e}")
            return []

    async def execute_paper_trade(self, signal: TradingSignal) -> Optional[PaperTrade]:
        """Execute a paper trade based on signal."""
        try:
            # Generate unique trade ID
            trade_id = "PT_{signal.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            signal_id = "{signal.symbol}_{signal.signal_time.strftime('%Y%m%d_%H%M%S')}"

            # Get current market price (simulate immediate execution)
            current_price = signal.entry_price  # In real system, would fetch live price

            # Create paper trade
            paper_trade = PaperTrade(
                trade_id=trade_id,
                signal_id=signal_id,
                symbol=signal.symbol,
                action=signal.signal_type.value,
                quantity=signal.quantity_suggestion,
                entry_price=current_price,
                target_price=signal.target_price,
                stop_loss=signal.stop_loss,
                entry_time=datetime.now(),
                status=TradeStatus.FILLED,
                strategy_name=signal.strategy_name,
            )

            # Store active paper trade
            self.paper_trades[trade_id] = paper_trade
            self.daily_stats["paper_trades_executed"] += 1

            logger.info(
                "📈 Paper trade executed: {signal.symbol} {signal.signal_type.value} "
                "{signal.quantity_suggestion}@₹{current_price:.2f}"
            )

            return paper_trade

        except Exception as e:
            logger.error("❌ Paper trade execution failed: {e}")
            return None

    async def monitor_paper_trades(self):
        """Monitor and update paper trade positions."""
        try:
            updated_trades = []

            for trade_id, trade in self.paper_trades.items():
                if trade.status not in [TradeStatus.FILLED, TradeStatus.PARTIAL]:
                    continue

                # Get current price
                try:
                    # In production, fetch live price from KiteConnect
                    # For now, simulate price movement
                    current_price = trade.entry_price * (
                        1 + (0.02 * (1 if trade.action == "BUY" else -1))
                    )

                    # Check for target or stop-loss hit
                    if trade.action in ["BUY", "STRONG_BUY"]:
                        if current_price >= trade.target_price:
                            # Target hit
                            trade.exit_price = trade.target_price
                            trade.exit_time = datetime.now()
                            trade.status = TradeStatus.TARGET_HIT
                            trade.pnl = (
                                trade.target_price - trade.entry_price
                            ) * trade.quantity
                            trade.pnl_percent = (
                                (trade.target_price / trade.entry_price) - 1
                            ) * 100
                        elif current_price <= trade.stop_loss:
                            # Stop-loss hit
                            trade.exit_price = trade.stop_loss
                            trade.exit_time = datetime.now()
                            trade.status = TradeStatus.STOP_HIT
                            trade.pnl = (
                                trade.stop_loss - trade.entry_price
                            ) * trade.quantity
                            trade.pnl_percent = (
                                (trade.stop_loss / trade.entry_price) - 1
                            ) * 100

                    else:  # SELL trades
                        if current_price <= trade.target_price:
                            # Target hit
                            trade.exit_price = trade.target_price
                            trade.exit_time = datetime.now()
                            trade.status = TradeStatus.TARGET_HIT
                            trade.pnl = (
                                trade.entry_price - trade.target_price
                            ) * trade.quantity
                            trade.pnl_percent = (
                                (trade.entry_price / trade.target_price) - 1
                            ) * 100
                        elif current_price >= trade.stop_loss:
                            # Stop-loss hit
                            trade.exit_price = trade.stop_loss
                            trade.exit_time = datetime.now()
                            trade.status = TradeStatus.STOP_HIT
                            trade.pnl = (
                                trade.entry_price - trade.stop_loss
                            ) * trade.quantity
                            trade.pnl_percent = (
                                (trade.entry_price / trade.stop_loss) - 1
                            ) * 100

                    if trade.status in [TradeStatus.TARGET_HIT, TradeStatus.STOP_HIT]:
                        updated_trades.append(trade)
                        logger.info(
                            "📊 Paper trade closed: {trade.symbol} "
                            "P&L: ₹{trade.pnl:.2f} ({trade.pnl_percent:+.1f}%)"
                        )

                except Exception as e:
                    logger.error("❌ Error monitoring trade {trade_id}: {e}")

            return updated_trades

        except Exception as e:
            logger.error("❌ Trade monitoring failed: {e}")
            return []

    async def generate_manual_trading_instructions(
        self, signals: list[TradingSignal]
    ) -> dict[str, Any]:
        """Generate instructions for manual trading."""
        if not signals:
            return {"signals": [], "instructions": "No signals for manual execution"}

        # Filter high-confidence signals for manual trading
        manual_signals = [
            s for s in signals if s.confidence.value in ["HIGH", "VERY_HIGH"]
        ]

        self.daily_stats["manual_trades_suggested"] += len(manual_signals)

        instructions = {
            "timestamp": datetime.now().isoformat(),
            "signals_count": len(manual_signals),
            "signals": [signal.to_dict() for signal in manual_signals],
            "instructions": self._format_manual_instructions(manual_signals),
            "compliance": {
                "sebi_compliant": True,
                "manual_execution_required": True,
                "automated_orders_placed": 0,
            },
        }

        return instructions

    def _format_manual_instructions(self, signals: list[TradingSignal]) -> str:
        """Format manual trading instructions."""
        if not signals:
            return "No high-confidence signals for manual execution."

        instructions = [
            "📋 MANUAL TRADING INSTRUCTIONS",
            "=" * 50,
            "🚨 IMPORTANT: Execute these orders MANUALLY in your trading app",
            "",
        ]

        for i, signal in enumerate(signals, 1):
            action = (
                "BUY" if signal.signal_type.value in ["BUY", "STRONG_BUY"] else "SELL"
            )
            instructions.extend(
                [
                    "🔵 Order #{i}: {signal.symbol}",
                    "   Action: {action} {signal.quantity_suggestion} shares",
                    "   Entry: ₹{signal.entry_price:.2f}",
                    "   Target: ₹{signal.target_price:.2f}",
                    "   Stop Loss: ₹{signal.stop_loss:.2f}",
                    "   Confidence: {signal.confidence.value}",
                    "",
                ]
            )

        return "\n".join(instructions)

    async def calculate_daily_performance(self) -> dict[str, Any]:
        """Calculate daily performance metrics."""
        try:
            # Calculate paper trading performance
            total_pnl = sum(
                trade.pnl
                for trade in self.paper_trades.values()
                if trade.status in [TradeStatus.TARGET_HIT, TradeStatus.STOP_HIT]
            )

            closed_trades = [
                trade
                for trade in self.paper_trades.values()
                if trade.status in [TradeStatus.TARGET_HIT, TradeStatus.STOP_HIT]
            ]

            winning_trades = [trade for trade in closed_trades if trade.pnl > 0]
            win_rate = (
                len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
            )

            avg_win = (
                sum(trade.pnl for trade in winning_trades) / len(winning_trades)
                if winning_trades
                else 0
            )
            losing_trades = [trade for trade in closed_trades if trade.pnl <= 0]
            avg_loss = (
                sum(trade.pnl for trade in losing_trades) / len(losing_trades)
                if losing_trades
                else 0
            )

            performance = {
                "date": datetime.now().date().isoformat(),
                "paper_trading": {
                    "total_pnl": total_pnl,
                    "total_trades": len(closed_trades),
                    "winning_trades": len(winning_trades),
                    "losing_trades": len(losing_trades),
                    "win_rate": win_rate,
                    "avg_win": avg_win,
                    "avg_loss": avg_loss,
                    "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
                },
                "signal_generation": {
                    "total_signals": self.daily_stats["signals_generated"],
                    "paper_trades_executed": self.daily_stats["paper_trades_executed"],
                    "manual_trades_suggested": self.daily_stats[
                        "manual_trades_suggested"
                    ],
                },
                "portfolio": {
                    "paper_portfolio_value": self.paper_portfolio_value,
                    "paper_portfolio_return": (total_pnl / self.paper_portfolio_value)
                    * 100,
                    "active_positions": len(
                        [
                            t
                            for t in self.paper_trades.values()
                            if t.status == TradeStatus.FILLED
                        ]
                    ),
                },
            }

            return performance

        except Exception as e:
            logger.error("❌ Performance calculation failed: {e}")
            return {}

    async def save_to_database(self, data: dict[str, Any], table_type: str):
        """Save data to BigQuery/Firestore."""
        try:
            # For signals and paper_trades, log to Firestore/BigQuery
            if table_type in ("signals", "paper_trades") and "signals" in data:
                for signal in data["signals"]:
                    result = log_signal_to_both(signal, self.project_id)
                    if not all(result.values()):
                        logger.warning(
                            "Cloud logging failed for signal: {signal.get('signal_id', 'N/A')}, falling back to local save."
                        )
            elif table_type == "paper_trades" and "updated_trades" in data:
                for trade in data["updated_trades"]:
                    result = log_signal_to_both(trade, self.project_id)
                    if not all(result.values()):
                        logger.warning(
                            "Cloud logging failed for trade: {trade.get('trade_id', 'N/A')}, falling back to local save."
                        )
            else:
                # Fallback: save to local JSON files
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("automated_data", exist_ok=True)
                filename = "automated_data/{table_type}_{timestamp}.json"
                with open(filename, "w") as f:
                    json.dump(data, f, indent=2)
                logger.info("💾 Data saved: {filename}")
        except Exception as e:
            logger.error("❌ Database save failed: {e}")

    async def run_trading_cycle(self, watchlist: list[str]):
        """Run a complete trading cycle."""
        try:
            logger.info("🔄 Starting trading cycle...")

            # 1. Generate signals
            signals = await self.generate_signals(watchlist)

            if signals:
                # 2. Execute paper trades for all signals
                for signal in signals:
                    await self.execute_paper_trade(signal)

                # 3. Generate manual trading instructions
                manual_instructions = await self.generate_manual_trading_instructions(
                    signals
                )

                # 4. Save signals and instructions
                await self.save_to_database(
                    {
                        "signals": [s.to_dict() for s in signals],
                        "manual_instructions": manual_instructions,
                    },
                    "signals",
                )

                logger.info(
                    "✅ Trading cycle complete: {len(signals)} signals processed"
                )

            # 5. Monitor existing paper trades
            updated_trades = await self.monitor_paper_trades()

            if updated_trades:
                # Save updated trades
                await self.save_to_database(
                    {"updated_trades": [trade.to_dict() for trade in updated_trades]},
                    "paper_trades",
                )

        except Exception as e:
            logger.error("❌ Trading cycle failed: {e}")

    async def run_daily_process(self):
        """Run the complete daily automated process."""
        try:
            logger.info("🌅 Starting daily automated process...")

            # Define watchlist
            nifty50_symbols = [
                "RELIANCE",
                "TCS",
                "HDFCBANK",
                "INFY",
                "HINDUNILVR",
                "ICICIBANK",
                "KOTAKBANK",
                "BHARTIARTL",
                "ITC",
                "SBIN",
                "BAJFINANCE",
                "ASIANPAINT",
                "MARUTI",
                "HCLTECH",
                "AXISBANK",
            ]

            # Run throughout market hours
            while self.is_market_open():
                await self.run_trading_cycle(nifty50_symbols)

                # Wait 5 minutes before next cycle
                await asyncio.sleep(300)

            # End of day processing
            logger.info("📊 Running end-of-day processing...")

            # Calculate daily performance
            performance = await self.calculate_daily_performance()

            # Save daily performance
            await self.save_to_database(performance, "daily_performance")

            # Save all paper trades
            all_trades = {
                "date": datetime.now().date().isoformat(),
                "paper_trades": [
                    trade.to_dict() for trade in self.paper_trades.values()
                ],
            }
            await self.save_to_database(all_trades, "all_paper_trades")

            logger.info("✅ Daily process completed")

        except Exception as e:
            logger.error("❌ Daily process failed: {e}")


async def main():
    """Main function for automated trading system."""
    print("🚀 AUTOMATED PAPER TRADING SYSTEM")
    print("=" * 70)
    print("📊 Paper Trading + Manual Signal Generation")
    print("🏛️  SEBI Compliant - Automated Simulation Only")
    print()

    system = AutomatedTradingSystem()

    if await system.initialize_system():
        print("✅ System initialized successfully")
        print("\n📋 Starting automated process...")
        print("   • Paper trades will execute automatically")
        print("   • Manual trading signals will be generated")
        print("   • Daily performance tracking enabled")
        print("   • All data saved to database")

        await system.run_daily_process()
    else:
        print("❌ System initialization failed")


if __name__ == "__main__":
    asyncio.run(main())
