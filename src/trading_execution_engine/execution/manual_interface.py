"""
Manual Execution Interface for SEBI Compliance
==============================================

Provides interface for manual trade execution to ensure SEBI compliance.

Author: SJ Trading
Licensed by SJ Trading
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ManualExecutionInterface:
    """
    Interface for manual trade execution with SEBI compliance
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pending_signals: List[Dict[str, Any]] = []
        self.executed_trades: List[Dict[str, Any]] = []
        self.user_confirmations: Dict[str, bool] = {}

        # Configuration
        self.require_confirmation = config.get("require_confirmation", True)
        self.max_order_value = config.get("max_order_value", 50000)
        self.cooling_period = (
            config.get("cooling_period_minutes", 5) * 60
        )  # Convert to seconds

        logger.info("Manual execution interface initialized")

    async def validate_setup(self):
        """Validate manual trading setup"""
        logger.info("Validating manual execution interface setup")

        # Check if interface is enabled
        if not self.config.get("enabled", True):
            logger.warning("Manual trading interface is disabled")
            return False

        # Validate configuration
        if self.max_order_value <= 0:
            logger.error("Invalid max order value configuration")
            return False

        logger.info("Manual execution interface validation passed")
        return True

    async def present_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Present a signal for manual execution

        SEBI Compliance:
        - All trades must be manually executed
        - System only provides signals and recommendations
        - User has full discretion over execution
        """
        signal_id = signal.get("signal_id", f"signal_{len(self.pending_signals)}")

        logger.info(f"Presenting signal for manual execution: {signal_id}")

        # Add to pending signals
        enhanced_signal = {
            **signal,
            "signal_id": signal_id,
            "presented_at": datetime.now().isoformat(),
            "status": "pending",
            "requires_manual_execution": True,
        }

        self.pending_signals.append(enhanced_signal)

        # Display signal information
        self._display_signal_for_user(enhanced_signal)

        # For automation purposes, we'll simulate user decision
        # In real implementation, this would integrate with UI/alerts
        user_decision = await self._simulate_user_decision(enhanced_signal)

        result = {
            "signal_id": signal_id,
            "user_executed": user_decision["executed"],
            "execution_time": (
                datetime.now().isoformat() if user_decision["executed"] else None
            ),
            "execution_price": user_decision.get("price"),
            "execution_quantity": user_decision.get("quantity"),
            "user_notes": user_decision.get("notes", ""),
        }

        if user_decision["executed"]:
            self.executed_trades.append(
                {**enhanced_signal, **result, "execution_method": "manual"}
            )

            # Remove from pending
            self.pending_signals = [
                s for s in self.pending_signals if s["signal_id"] != signal_id
            ]

        return result

    def _display_signal_for_user(self, signal: Dict[str, Any]):
        """Display signal information for user review"""
        print("\n" + "=" * 60)
        print("🚨 NEW TRADING SIGNAL FOR MANUAL EXECUTION")
        print("=" * 60)
        print(f"Signal ID: {signal['signal_id']}")
        print(f"Symbol: {signal.get('symbol', 'N/A')}")
        print(f"Action: {signal.get('action', 'N/A')}")
        print(f"Strategy: {signal.get('strategy', 'N/A')}")
        print(f"Signal Strength: {signal.get('strength', 'N/A')}")
        print(f"Recommended Price: ₹{signal.get('price', 0):,.2f}")
        print(f"Recommended Quantity: {signal.get('quantity', 0)}")
        print(f"Estimated Value: ₹{signal.get('estimated_value', 0):,.2f}")
        print(f"Stop Loss: ₹{signal.get('stop_loss', 0):,.2f}")
        print(f"Target: ₹{signal.get('target', 0):,.2f}")
        print(f"Risk/Reward: {signal.get('risk_reward_ratio', 'N/A')}")
        print("\n⚠️  SEBI COMPLIANCE NOTICE:")
        print("This is a signal for manual execution only.")
        print("Please review and execute manually through your broker.")
        print("=" * 60)

    async def _simulate_user_decision(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate user decision for automation
        In real implementation, this would wait for actual user input
        """
        # For demo purposes, simulate different user behaviors

        # Extract signal strength to make decision
        strength = signal.get("strength", 0.5)
        estimated_value = signal.get("estimated_value", 0)

        # Decision logic based on signal quality
        will_execute = (
            strength > 0.7  # High confidence signals only
            and estimated_value <= self.max_order_value  # Within order limits
            and signal.get("action", "").upper() in ["BUY", "SELL"]  # Valid actions
        )

        if will_execute:
            # Simulate manual execution with slight variations
            price_adjustment = (
                0.99 if signal.get("action", "").upper() == "BUY" else 1.01
            )
            execution_price = signal.get("price", 0) * price_adjustment

            return {
                "executed": True,
                "price": execution_price,
                "quantity": signal.get("quantity", 0),
                "notes": f"Executed manually based on signal strength {strength:.2f}",
            }
        else:
            return {
                "executed": False,
                "reason": f"Signal strength {strength:.2f} below threshold or value too high",
            }

    async def export_daily_summary(self) -> Dict[str, Any]:
        """Export daily manual trading summary"""
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_signals_presented": len(self.pending_signals)
            + len(self.executed_trades),
            "signals_executed": len(self.executed_trades),
            "execution_rate": len(self.executed_trades)
            / max(1, len(self.pending_signals) + len(self.executed_trades)),
            "total_trade_value": sum(
                trade.get("estimated_value", 0) for trade in self.executed_trades
            ),
            "executed_trades": self.executed_trades,
            "pending_signals": self.pending_signals,
        }

        logger.info(
            f"Manual trading summary: {summary['signals_executed']} trades executed "
            f"out of {summary['total_signals_presented']} signals presented"
        )

        return summary

    def get_pending_signals(self) -> List[Dict[str, Any]]:
        """Get all pending signals"""
        return self.pending_signals.copy()

    def get_executed_trades(self) -> List[Dict[str, Any]]:
        """Get all executed trades"""
        return self.executed_trades.copy()

    async def mark_signal_executed(
        self, signal_id: str, execution_details: Dict[str, Any]
    ) -> bool:
        """Mark a signal as manually executed"""
        for signal in self.pending_signals:
            if signal["signal_id"] == signal_id:
                executed_trade = {
                    **signal,
                    **execution_details,
                    "execution_method": "manual",
                    "execution_time": datetime.now().isoformat(),
                }

                self.executed_trades.append(executed_trade)
                self.pending_signals.remove(signal)

                logger.info(f"Signal {signal_id} marked as manually executed")
                return True

        logger.warning(f"Signal {signal_id} not found in pending signals")
        return False
