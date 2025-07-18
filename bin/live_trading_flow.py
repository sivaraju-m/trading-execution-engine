#!/usr/bin/env python3
"""
Live Trading Flow (DISABLED BY DEFAULT)
=======================================
Pulls delta data, runs strategy logic and places real orders via broker API.
This flow is disabled by default for SEBI compliance.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from flow.delta_data_pull import DeltaDataPuller

except ImportError as e:
    print("Warning: Some imports failed: {e}")
    print("Running in standalone mode...")


class LiveTradingFlow:
    """Handles live trading flow - DISABLED BY DEFAULT for SEBI compliance"""

    def __init__(self, config_path: Optional[str] = None, mode: str = "production"):
        self.mode = mode
        self.config = self._load_config(config_path)
        self.setup_logging()

        # SEBI Compliance check
        if not self._check_authorization():
            raise RuntimeError(
                "🚫 Live trading is DISABLED by default for SEBI compliance"
            )

        self.delta_puller = (
            DeltaDataPuller(config_path) if "DeltaDataPuller" in globals() else None
        )

    def _load_config(self, config_path: Optional[str]) -> dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "live_trading": {
                "enabled": False,  # DISABLED BY DEFAULT
                "require_explicit_enable": True,
                "authorization_file": "config/live_trading_authorization.json",
                "max_daily_trades": 10,
                "max_position_size_pct": 5,
            },
            "database": {
                "production": {
                    "source_db": "sqlite:///data/prod_source.db",
                    "results_db": "sqlite:///data/prod_results.db",
                }
            },
            "broker_api": {
                "provider": "kite",
                "paper_mode": True,  # Default to paper mode
                "api_key": None,
                "access_token": None,
            },
            "risk_management": {
                "max_loss_per_trade_pct": 2,
                "max_daily_loss_pct": 5,
                "position_sizing": "fixed",
                "stop_loss_pct": 3,
            },
            "symbols": ["RELIANCE.NS", "TCS.NS"],  # Limited symbols for live trading
            "strategies": ["rsi"],  # Limited strategies for live trading
            "compliance": {
                "sebi_compliant": True,
                "require_manual_authorization": True,
                "audit_all_orders": True,
                "real_time_monitoring": True,
            },
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def _check_authorization(self) -> bool:
        """Check if live trading is explicitly authorized"""
        config = self.config.get("live_trading", {})

        # Check if live trading is enabled in config
        if not config.get("enabled", False):
            self.logger.error("🚫 Live trading is DISABLED in configuration")
            return False

        # Check for authorization file
        auth_file = Path(
            config.get("authorization_file", "config/live_trading_authorization.json")
        )
        if not auth_file.exists():
            self.logger.error("🚫 Authorization file not found: {auth_file}")
            self.logger.error(
                "📋 To enable live trading, create authorization file with:"
            )
            self.logger.error(
                '   {"authorized": true, "authorized_by": "user", "date": "YYYY-MM-DD"}'
            )
            return False

        try:
            with open(auth_file) as f:
                auth_data = json.load(f)

            if not auth_data.get("authorized", False):
                self.logger.error(
                    "🚫 Live trading not authorized in authorization file"
                )
                return False

            self.logger.warning("⚠️ Live trading is ENABLED - proceed with caution")
            return True

        except Exception as e:
            self.logger.error("🚫 Error reading authorization file: {e}")
            return False

    def setup_logging(self):
        """Setup focused logging for live trading flow"""
        log_dir = Path("logs/flows")
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    log_dir
                    / "live_trading_{self.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Log critical warnings
        self.logger.warning("⚠️ LIVE TRADING FLOW INITIALIZED")
        self.logger.warning("🏛️ Ensure SEBI compliance at all times")
        self.logger.warning("💰 Real money at risk - proceed with extreme caution")

    def pull_delta_data(self, symbols: Optional[list[str]] = None) -> dict[str, Any]:
        """Pull delta data for live trading"""
        self.logger.info("🔄 Pulling delta data for live trading...")

        if self.delta_puller:
            results = self.delta_puller.pull_delta_data(symbols)
            self.logger.info(
                "✅ Delta data: {len(results.get('successful', []))} symbols updated"
            )
            return results
        else:
            self.logger.error("❌ Delta puller not available")
            return {
                "error": "Delta puller not available",
                "successful": [],
                "failed": symbols or [],
            }

    def generate_trading_signals(self, delta_results: dict[str, Any]) -> dict[str, Any]:
        """Generate trading signals from delta data"""
        self.logger.info("🧠 Generating trading signals...")

        successful_symbols = delta_results.get("successful", [])
        strategies = self.config["strategies"]

        signals = {
            "timestamp": datetime.now().isoformat(),
            "mode": "LIVE_TRADING",
            "signals": [],
            "summary": {
                "symbols_analyzed": len(successful_symbols),
                "strategies_used": len(strategies),
                "signals_generated": 0,
                "high_confidence_signals": 0,
            },
        }

        # Generate signals (simplified implementation)
        for symbol in successful_symbols:
            for strategy in strategies:
                # Mock signal generation
                signal = {
                    "signal_id": f"LIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}_{strategy}",
                    "symbol": symbol,
                    "strategy": strategy,
                    "action": "HOLD",  # Default to HOLD for safety
                    "confidence": 0.5,
                    "timestamp": datetime.now().isoformat(),
                    "live_trading": True,
                }

                signals["signals"].append(signal)

        signals["summary"]["signals_generated"] = len(signals["signals"])
        signals["summary"]["high_confidence_signals"] = len(
            [s for s in signals["signals"] if s["confidence"] > 0.8]
        )

        self.logger.info(
            "✅ Generated {signals['summary']['signals_generated']} signals"
        )
        return signals

    def execute_risk_management(self, signals: dict[str, Any]) -> dict[str, Any]:
        """Apply risk management filters to signals"""
        self.logger.info("🛡️ Applying risk management...")

        risk_config = self.config["risk_management"]
        filtered_signals = []
        risk_summary = {
            "original_signals": len(signals.get("signals", [])),
            "filtered_signals": 0,
            "rejected_signals": 0,
            "rejection_reasons": [],
        }

        for signal in signals.get("signals", []):
            # Apply risk filters
            if signal["confidence"] < 0.8:
                risk_summary["rejection_reasons"].append(
                    "Low confidence: {signal['confidence']}"
                )
                risk_summary["rejected_signals"] += 1
                continue

            if signal["action"] == "HOLD":
                # HOLD signals are always safe
                filtered_signals.append(signal)
                risk_summary["filtered_signals"] += 1
            else:
                # For actual trading signals, apply additional checks
                risk_summary["rejection_reasons"].append(
                    "Non-HOLD signal rejected for safety: {signal['action']}"
                )
                risk_summary["rejected_signals"] += 1

        filtered_result = signals.copy()
        filtered_result["signals"] = filtered_signals
        filtered_result["risk_management"] = risk_summary

        self.logger.info(
            "🛡️ Risk filter: {risk_summary['filtered_signals']}/{risk_summary['original_signals']} signals passed"
        )
        return filtered_result

    def place_orders(self, filtered_signals: dict[str, Any]) -> dict[str, Any]:
        """Place orders via broker API (CURRENTLY DISABLED FOR SAFETY)"""
        self.logger.warning("🚫 ORDER PLACEMENT IS DISABLED FOR SAFETY")

        order_results = {
            "timestamp": datetime.now().isoformat(),
            "mode": "DISABLED",
            "orders_attempted": 0,
            "orders_successful": 0,
            "orders_failed": 0,
            "orders": [],
            "safety_message": "Order placement is disabled by default for SEBI compliance and safety",
        }

        # Count signals that would have been orders
        signals = filtered_signals.get("signals", [])
        non_hold_signals = [s for s in signals if s["action"] != "HOLD"]

        order_results["orders_attempted"] = len(non_hold_signals)

        # Log what would have happened
        for signal in non_hold_signals:
            self.logger.warning(
                "🚫 Would place order: {signal['action']} {signal['symbol']} (confidence: {signal['confidence']:.2f})"
            )

            mock_order = {
                "order_id": f"MOCK_{signal['signal_id']}",
                "symbol": signal["symbol"],
                "action": signal["action"],
                "status": "DISABLED",
                "message": "Order placement disabled for safety",
            }
            order_results["orders"].append(mock_order)

        self.logger.warning(
            "🚫 {len(non_hold_signals)} orders would have been placed (but were blocked for safety)"
        )
        return order_results

    def monitor_and_audit(self, order_results: dict[str, Any]) -> dict[str, Any]:
        """Monitor orders and maintain audit trail"""
        self.logger.info("📊 Monitoring and auditing...")

        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_status": "ACTIVE",
            "audit_trail_complete": True,
            "compliance_check": "PASS",
            "orders_monitored": len(order_results.get("orders", [])),
            "real_orders_placed": 0,  # Should always be 0
            "safety_status": "PROTECTED",
        }

        # Verify no real orders were placed
        real_orders = [
            o for o in order_results.get("orders", []) if o.get("status") != "DISABLED"
        ]
        audit_results["real_orders_placed"] = len(real_orders)

        if audit_results["real_orders_placed"] > 0:
            audit_results["compliance_check"] = "VIOLATION"
            audit_results["safety_status"] = "COMPROMISED"
            self.logger.error(
                "🚨 COMPLIANCE VIOLATION: {audit_results['real_orders_placed']} real orders detected!"
            )

        self.logger.info("📊 Audit complete: {audit_results['compliance_check']}")
        return audit_results

    def save_live_trading_results(self, results: dict[str, Any]):
        """Save live trading results to database"""
        db_config = self.config["database"][self.mode]
        results_db = db_config["results_db"]

        # Create live trading directory structure
        live_dir = Path("data") / self.mode / "live_trading"
        live_dir.mkdir(parents=True, exist_ok=True)

        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = live_dir / "live_trading_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info("💾 Live trading results saved to {results_file}")
        self.logger.info("🗄️ Target database: {results_db}")

    def run_full_flow(self, symbols: Optional[list[str]] = None) -> dict[str, Any]:
        """Run the complete live trading flow"""
        if symbols is None:
            symbols = self.config["symbols"]

        self.logger.warning("🚀 Starting LIVE TRADING flow ({self.mode} mode)")
        self.logger.warning("⚠️ REAL MONEY AT RISK - PROCEED WITH EXTREME CAUTION")

        try:
            # Step 1: Pull delta data
            delta_results = self.pull_delta_data(symbols)

            # Step 2: Generate trading signals
            signals = self.generate_trading_signals(delta_results)

            # Step 3: Apply risk management
            filtered_signals = self.execute_risk_management(signals)

            # Step 4: Place orders (DISABLED FOR SAFETY)
            order_results = self.place_orders(filtered_signals)

            # Step 5: Monitor and audit
            audit_results = self.monitor_and_audit(order_results)

            # Compile final results
            final_results = {
                "flow_type": "live_trading",
                "mode": self.mode,
                "timestamp": datetime.now().isoformat(),
                "status": "COMPLETED_SAFELY",
                "delta_data_results": delta_results,
                "signals": signals,
                "filtered_signals": filtered_signals,
                "order_results": order_results,
                "audit_results": audit_results,
                "safety_summary": {
                    "real_orders_placed": audit_results["real_orders_placed"],
                    "safety_status": audit_results["safety_status"],
                    "compliance_check": audit_results["compliance_check"],
                    "protection_active": True,
                },
            }

            # Save results
            self.save_live_trading_results(final_results)

            # Log summary
            self.logger.warning("✅ Live trading flow completed SAFELY")
            self.logger.warning(
                "🛡️ No real orders placed: {order_results['orders_attempted']} blocked"
            )
            self.logger.warning("📊 Compliance: {audit_results['compliance_check']}")

            return final_results

        except Exception as e:
            self.logger.error("❌ Live trading flow failed: {e}")
            return {
                "flow_type": "live_trading",
                "mode": self.mode,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "FAILED",
                "safety_status": "PROTECTED",
            }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Live Trading Flow (DISABLED BY DEFAULT)"
    )
    parser.add_argument(
        "--mode",
        choices=["production"],
        default="production",
        help="Run mode (only production supported for live trading)",
    )
    parser.add_argument("--symbols", nargs="+", help="Symbols to trade")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument(
        "--force-enable",
        action="store_true",
        help="Force enable (requires authorization file)",
    )

    args = parser.parse_args()

    if not args.force_enable:
        print("🚫 Live trading is DISABLED by default for SEBI compliance")
        print("🏛️ Use --force-enable only after proper authorization")
        return

    try:
        # Initialize flow
        flow = LiveTradingFlow(args.config, args.mode)

        # Run flow
        results = flow.run_full_flow(args.symbols)

        # Save results
        results_dir = Path("logs/flows/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        results_file = (
            results_dir
            / "live_trading_{args.mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print("\n📋 Results saved to: {results_file}")
        print("⚠️ Live trading flow completed")

        if "error" not in results:
            print("🛡️ Safety status: {results['safety_summary']['safety_status']}")
            print("📊 Compliance: {results['safety_summary']['compliance_check']}")
            print("🚫 Orders blocked: {results['order_results']['orders_attempted']}")
        else:
            print("❌ Flow failed: {results['error']}")

    except RuntimeError as e:
        print("🚫 {e}")
        print("🏛️ Live trading requires explicit authorization for SEBI compliance")


if __name__ == "__main__":
    main()
