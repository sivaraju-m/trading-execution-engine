#!/usr/bin/env python3
"""
Portfolio Management System
Advanced position sizing, risk management, and multi-asset portfolio optimization
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from trading_execution_engine.ingest.yfinance_loader import load_yfinance_data
from trading_execution_engine.strategies.enhanced_strategies import (
    enhanced_rsi_signals,
    macd_signals,
)
from trading_execution_engine.utils.data_cleaner import clean_ohlcv_data

logger = logging.getLogger(__name__)


class PositionSizeMethod(Enum):
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_TARGET = "volatility_target"


@dataclass
class Position:
    ticker: str
    shares: float
    entry_price: float
    current_price: float
    entry_date: datetime
    strategy: str
    confidence: float

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.shares

    @property
    def unrealized_return(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class Trade:
    ticker: str
    action: str  # BUY/SELL
    shares: float
    price: float
    timestamp: datetime
    strategy: str
    reason: str
    commission: float = 0.0


class RiskManager:
    """Risk management and position sizing"""

    def __init__(
        self,
        max_position_size: float = 0.1,  # 10% max per position
        max_portfolio_risk: float = 0.02,  # 2% daily portfolio risk
        stop_loss_pct: float = 0.05,  # 5% stop loss
        take_profit_pct: float = 0.15,
    ):  # 15% take profit
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        volatility: float,
        confidence: float,
        method: PositionSizeMethod = PositionSizeMethod.VOLATILITY_TARGET,
    ) -> float:
        """Calculate optimal position size based on risk management rules"""

        if method == PositionSizeMethod.EQUAL_WEIGHT:
            return portfolio_value * self.max_position_size / entry_price

        elif method == PositionSizeMethod.RISK_PARITY:
            # Size inversely proportional to volatility
            target_risk = portfolio_value * self.max_portfolio_risk
            position_risk = volatility * entry_price
            if position_risk > 0:
                return min(
                    target_risk / position_risk,
                    portfolio_value * self.max_position_size / entry_price,
                )
            else:
                return portfolio_value * self.max_position_size / entry_price

        elif method == PositionSizeMethod.VOLATILITY_TARGET:
            # Target volatility approach with confidence scaling
            target_vol = 0.02  # 2% target volatility
            confidence_multiplier = confidence  # Scale by signal confidence

            if volatility > 0:
                position_value = (
                    portfolio_value * target_vol * confidence_multiplier
                ) / volatility
                return min(
                    position_value / entry_price,
                    portfolio_value * self.max_position_size / entry_price,
                )
            else:
                return portfolio_value * self.max_position_size / entry_price

        elif method == PositionSizeMethod.KELLY_CRITERION:
            # Simplified Kelly criterion (requires win rate and avg win/loss)
            # This is a simplified version - in practice you'd use historical data
            win_rate = confidence  # Use confidence as proxy for win rate
            avg_win = 0.1  # Assume 10% average win
            avg_loss = 0.05  # Assume 5% average loss

            if avg_loss > 0:
                kelly_fraction = (
                    win_rate * avg_win - (1 - win_rate) * avg_loss
                ) / avg_win
                kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
                return portfolio_value * kelly_fraction / entry_price
            else:
                return portfolio_value * self.max_position_size / entry_price

        return 0.0

    def should_stop_loss(self, position: Position) -> bool:
        """Check if position should be stopped out"""
        return position.unrealized_return <= -self.stop_loss_pct

    def should_take_profit(self, position: Position) -> bool:
        """Check if position should take profit"""
        return position.unrealized_return >= self.take_profit_pct


class Portfolio:
    """Multi-asset portfolio with advanced management"""

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.001,
        position_size_method: PositionSizeMethod = PositionSizeMethod.VOLATILITY_TARGET,
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.commission_rate = commission_rate
        self.risk_manager = RiskManager()
        self.position_size_method = position_size_method

        # Performance tracking
        self.daily_values = []
        self.daily_returns = []
        self.benchmark_returns = []

    @property
    def portfolio_value(self) -> float:
        """Current total portfolio value"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    @property
    def total_return(self) -> float:
        """Total portfolio return since inception"""
        return (self.portfolio_value / self.initial_capital - 1) * 100

    def update_position_prices(self, price_data: dict[str, float]):
        """Update current prices for all positions"""
        for ticker, position in self.positions.items():
            if ticker in price_data:
                position.current_price = price_data[ticker]

    def calculate_portfolio_volatility(
        self, price_data: dict[str, np.ndarray], window: int = 30
    ) -> float:
        """Calculate portfolio-level volatility"""
        if not self.positions:
            return 0.0

        portfolio_returns = []
        for ticker, position in self.positions.items():
            if ticker in price_data and len(price_data[ticker]) > window:
                returns = (
                    np.diff(price_data[ticker][-window:])
                    / price_data[ticker][-window:-1]
                )
                weight = position.market_value / self.portfolio_value
                portfolio_returns.append(returns * weight)

        if portfolio_returns:
            total_returns = np.sum(portfolio_returns, axis=0)
            return np.std(total_returns)

        return 0.0

    def execute_trade(
        self,
        ticker: str,
        action: str,
        price: float,
        timestamp: datetime,
        strategy: str,
        confidence: float,
        reason: str,
        volatility: float = 0.02,
    ) -> bool:
        """Execute a trade with risk management"""

        commission = 0.0

        if action == "BUY":
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                self.portfolio_value,
                price,
                volatility,
                confidence,
                self.position_size_method,
            )

            cost = position_size * price
            commission = cost * self.commission_rate
            total_cost = cost + commission

            # Check if we have enough cash
            if total_cost <= self.cash:
                self.cash -= total_cost

                # Create or update position
                if ticker in self.positions:
                    # Average down/up
                    old_position = self.positions[ticker]
                    total_shares = old_position.shares + position_size
                    avg_price = (
                        (old_position.shares * old_position.entry_price)
                        + (position_size * price)
                    ) / total_shares

                    self.positions[ticker] = Position(
                        ticker=ticker,
                        shares=total_shares,
                        entry_price=avg_price,
                        current_price=price,
                        entry_date=old_position.entry_date,
                        strategy=strategy,
                        confidence=max(old_position.confidence, confidence),
                    )
                else:
                    self.positions[ticker] = Position(
                        ticker=ticker,
                        shares=position_size,
                        entry_price=price,
                        current_price=price,
                        entry_date=timestamp,
                        strategy=strategy,
                        confidence=confidence,
                    )

                self.trades.append(
                    Trade(
                        ticker=ticker,
                        action=action,
                        shares=position_size,
                        price=price,
                        timestamp=timestamp,
                        strategy=strategy,
                        reason=reason,
                        commission=commission,
                    )
                )

                return True

        elif action == "SELL":
            if ticker in self.positions:
                position = self.positions[ticker]

                # Sell all shares
                proceeds = position.shares * price
                commission = proceeds * self.commission_rate
                net_proceeds = proceeds - commission

                self.cash += net_proceeds

                self.trades.append(
                    Trade(
                        ticker=ticker,
                        action=action,
                        shares=position.shares,
                        price=price,
                        timestamp=timestamp,
                        strategy=strategy,
                        reason=reason,
                        commission=commission,
                    )
                )

                del self.positions[ticker]
                return True

        return False

    def apply_risk_management(
        self, current_prices: dict[str, float], timestamp: datetime
    ):
        """Apply stop-loss and take-profit rules"""
        positions_to_close = []

        for ticker, position in self.positions.items():
            if ticker in current_prices:
                position.current_price = current_prices[ticker]

                if self.risk_manager.should_stop_loss(position):
                    positions_to_close.append((ticker, "Stop Loss"))
                elif self.risk_manager.should_take_profit(position):
                    positions_to_close.append((ticker, "Take Profit"))

        for ticker, reason in positions_to_close:
            self.execute_trade(
                ticker=ticker,
                action="SELL",
                price=current_prices[ticker],
                timestamp=timestamp,
                strategy=self.positions[ticker].strategy,
                confidence=self.positions[ticker].confidence,
                reason=reason,
            )

    def get_performance_metrics(self) -> dict[str, float]:
        """Calculate comprehensive portfolio performance metrics"""
        if len(self.daily_returns) < 2:
            return {}

        returns = np.array(self.daily_returns)

        # Basic metrics
        total_return = self.total_return
        volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized

        # Sharpe ratio
        sharpe = (
            (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
            if np.std(returns) > 0
            else 0
        )

        # Maximum drawdown
        cumulative = np.cumprod(1 + returns / 100)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max * 100
        max_drawdown = np.min(drawdowns)

        # Win rate
        winning_trades = sum(
            1
            for trade in self.trades
            if trade.action == "SELL"
            and any(
                p.ticker == trade.ticker
                for p in self.positions.values()
                if (trade.price - p.entry_price) > 0
            )
        )
        total_trades = sum(1 for trade in self.trades if trade.action == "SELL")
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return {
            "total_return_pct": round(total_return, 2),
            "volatility_pct": round(volatility, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown_pct": round(max_drawdown, 2),
            "win_rate_pct": round(win_rate, 2),
            "total_trades": len(self.trades),
            "current_positions": len(self.positions),
            "cash_pct": round(self.cash / self.portfolio_value * 100, 2),
        }


def run_portfolio_backtest(
    tickers: list[str],
    strategies: dict[str, callable],
    start_date: str,
    end_date: str,
    initial_capital: float = 100000,
) -> dict[str, Any]:
    """Run a comprehensive portfolio backtest"""

    logger.info("Running portfolio backtest with {len(tickers)} assets")
    logger.info("Strategies: {list(strategies.keys())}")

    # Load data for all tickers
    data = {}
    for ticker in tickers:
        try:
            raw_df = load_yfinance_data(ticker, start_date, end_date)
            clean_df = clean_ohlcv_data(raw_df)
            clean_df.ffill(inplace=True)
            clean_df.bfill(inplace=True)

            if len(clean_df) > 50:  # Minimum data requirement
                data[ticker] = clean_df
                logger.info("Loaded {len(clean_df)} data points for {ticker}")
            else:
                logger.warning("Insufficient data for {ticker}")
        except Exception as e:
            logger.error("Failed to load data for {ticker}: {e}")

    if not data:
        return {"error": "No valid data loaded"}

    # Initialize portfolio
    portfolio = Portfolio(initial_capital=initial_capital)

    # Get all unique dates
    all_dates = set()
    for df in data.values():
        all_dates.update(df.index)

    all_dates = sorted(list(all_dates))
    logger.info("Backtesting over {len(all_dates)} trading days")

    # Run backtest day by day
    for date in all_dates:
        current_prices = {}

        # Get current prices and generate signals
        for ticker, df in data.items():
            if date in df.index:
                current_price = df.loc[date, "close"]
                current_prices[ticker] = current_price

                # Get data up to current date for signal generation
                historical_data = df.loc[df.index <= date]

                if len(historical_data) >= 30:  # Minimum for signal generation
                    # Generate signals for each strategy
                    for strategy_name, strategy_func in strategies.items():
                        try:
                            signals, confidence = strategy_func(historical_data)
                            current_signal = signals[-1] if signals else 0

                            # Calculate volatility
                            if len(historical_data) >= 20:
                                returns = historical_data["close"].pct_change().dropna()
                                volatility = returns.rolling(20).std().iloc[-1]
                                if pd.isna(volatility):
                                    volatility = 0.02
                            else:
                                volatility = 0.02

                            # Execute trades based on signals
                            if current_signal > 0 and ticker not in portfolio.positions:
                                # Buy signal
                                portfolio.execute_trade(
                                    ticker=ticker,
                                    action="BUY",
                                    price=current_price,
                                    timestamp=date,
                                    strategy=strategy_name,
                                    confidence=confidence,
                                    reason="{strategy_name} buy signal",
                                    volatility=volatility,
                                )

                            elif current_signal < 0 and ticker in portfolio.positions:
                                # Sell signal
                                portfolio.execute_trade(
                                    ticker=ticker,
                                    action="SELL",
                                    price=current_price,
                                    timestamp=date,
                                    strategy=strategy_name,
                                    confidence=confidence,
                                    reason="{strategy_name} sell signal",
                                )

                        except Exception as e:
                            logger.debug(
                                "Error generating {strategy_name} signal for {ticker}: {e}"
                            )

        # Update portfolio with current prices
        portfolio.update_position_prices(current_prices)

        # Apply risk management
        portfolio.apply_risk_management(current_prices, date)

        # Record daily performance
        portfolio.daily_values.append(portfolio.portfolio_value)
        if len(portfolio.daily_values) > 1:
            daily_return = (
                portfolio.daily_values[-1] / portfolio.daily_values[-2] - 1
            ) * 100
            portfolio.daily_returns.append(daily_return)

    # Calculate final metrics
    metrics = portfolio.get_performance_metrics()

    # Calculate buy & hold benchmark
    if data:
        first_ticker = list(data.keys())[0]
        first_df = data[first_ticker]
        buy_hold_return = (
            first_df["close"].iloc[-1] / first_df["close"].iloc[0] - 1
        ) * 100
        metrics["benchmark_return_pct"] = round(buy_hold_return, 2)
        metrics["outperformance"] = round(
            metrics.get("total_return_pct", 0) - buy_hold_return, 2
        )

    return {
        "portfolio": portfolio,
        "metrics": metrics,
        "trades": portfolio.trades,
        "positions": portfolio.positions,
        "success": True,
    }


if __name__ == "__main__":
    # Test portfolio management
    print("🚀 AI Trading Machine - Portfolio Management Test")
    print("=" * 60)

    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    strategies = {"enhanced_rsi": enhanced_rsi_signals, "macd": macd_signals}

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    result = run_portfolio_backtest(
        tickers=tickers,
        strategies=strategies,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        initial_capital=100000,
    )

    if result.get("success"):
        metrics = result["metrics"]
        print("\\n📊 Portfolio Performance:")
        print("   Total Return: {metrics.get('total_return_pct', 0):+.2f}%")
        print("   Volatility: {metrics.get('volatility_pct', 0):.2f}%")
        print("   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print("   Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print("   Total Trades: {metrics.get('total_trades', 0)}")
        print("   Current Positions: {metrics.get('current_positions', 0)}")
        print("   Cash Allocation: {metrics.get('cash_pct', 0):.1f}%")

        if "outperformance" in metrics:
            print("   vs Benchmark: {metrics['outperformance']:+.2f}%")

        print("\\n✅ Portfolio backtest completed!")
    else:
        print("❌ Portfolio backtest failed: {result.get('error')}")
