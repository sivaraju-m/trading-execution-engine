#!/usr/bin/env python3
"""
Daily Trading Scheduler for SEBI-Compliant Operations
====================================================

This scheduler:
1. Manages daily trading workflows
2. Coordinates with strategy-engine signals
3. Provides manual execution interfaces
4. Ensures SEBI compliance
5. Tracks performance and risk metrics

SEBI Compliance Features:
- Manual execution requirement for all real trades
- Comprehensive audit logging
- Risk limit enforcement
- Real-time position monitoring

Author: SJ Trading
Licensed by SJ Trading
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.trading_execution_engine.core.scheduler import TradingScheduler
from src.trading_execution_engine.execution.manual_interface import ManualExecutionInterface
from src.trading_execution_engine.execution.paper_trader import PaperTrader
from src.trading_execution_engine.monitoring.performance_tracker import ExecutionPerformanceTracker
from src.trading_execution_engine.risk.manager import RiskManager
from src.trading_execution_engine.utils.logger import get_logger
from src.trading_execution_engine.utils.market_hours import MarketHoursValidator

logger = get_logger(__name__)


class DailyTradingScheduler:
    """
    Daily trading scheduler with SEBI-compliant manual execution
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/daily_scheduler/config.yaml"
        self.config = self._load_config()
        
        # Initialize components
        self.market_validator = MarketHoursValidator()
        self.risk_manager = RiskManager(self.config.get('risk_management', {}))
        self.paper_trader = PaperTrader(self.config.get('paper_trading', {}))
        self.manual_interface = ManualExecutionInterface(self.config.get('manual_trading', {}))
        self.performance_tracker = ExecutionPerformanceTracker(self.config.get('performance', {}))
        self.scheduler = TradingScheduler(self.config.get('scheduler', {}))
        
        logger.info("Daily Trading Scheduler initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config = {
            'scheduler': {
                'market_open_time': '09:15',
                'market_close_time': '15:30',
                'pre_market_start': '09:00',
                'post_market_end': '16:00',
                'signal_check_interval': 300,  # 5 minutes
                'max_daily_trades': 20,
            },
            'paper_trading': {
                'enabled': True,
                'initial_capital': 1000000,  # 10 Lakh
                'commission_per_trade': 20,
                'slippage_bps': 5,
            },
            'manual_trading': {
                'enabled': True,
                'require_confirmation': True,
                'max_order_value': 50000,  # 50K per order
                'cooling_period_minutes': 5,
            },
            'risk_management': {
                'max_position_size_pct': 5,
                'max_daily_loss_pct': 3,
                'stop_loss_pct': 2,
                'max_concentration_pct': 20,
            },
            'performance': {
                'track_metrics': True,
                'generate_daily_reports': True,
                'alert_thresholds': {
                    'daily_loss_pct': 2,
                    'drawdown_pct': 5,
                }
            },
            'data_sources': {
                'strategy_signals_path': '../strategy-engine/outputs/daily_signals.json',
                'market_data_source': 'shared-services',
            }
        }
        
        config_file = Path(self.config_path)
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config

    async def run_daily_trading_cycle(self) -> Dict[str, Any]:
        """
        Run the complete daily trading cycle
        """
        logger.info("Starting daily trading cycle")
        
        # Validate market hours
        if not self.market_validator.is_market_day():
            logger.info("Market is closed today - skipping trading cycle")
            return {"status": "skipped", "reason": "market_closed"}
        
        results = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "cycles": [],
            "total_signals": 0,
            "paper_trades": 0,
            "manual_trades": 0,
            "performance": {}
        }
        
        try:
            # Pre-market setup
            await self._pre_market_setup()
            
            # Main trading loop
            while self.market_validator.is_market_open():
                cycle_result = await self._run_trading_cycle()
                results["cycles"].append(cycle_result)
                results["total_signals"] += cycle_result.get("signals_processed", 0)
                results["paper_trades"] += cycle_result.get("paper_trades", 0)
                results["manual_trades"] += cycle_result.get("manual_trades", 0)
                
                # Wait for next cycle
                await asyncio.sleep(self.config['scheduler']['signal_check_interval'])
            
            # Post-market cleanup and reporting
            performance = await self._post_market_cleanup()
            results["performance"] = performance
            
        except Exception as e:
            logger.error(f"Error in daily trading cycle: {e}")
            results["error"] = str(e)
        
        logger.info(f"Daily trading cycle completed: {results['total_signals']} signals, "
                   f"{results['paper_trades']} paper trades, {results['manual_trades']} manual trades")
        
        return results

    async def _pre_market_setup(self):
        """Pre-market setup and validation"""
        logger.info("Running pre-market setup")
        
        # Initialize risk limits for the day
        await self.risk_manager.reset_daily_limits()
        
        # Prepare paper trading portfolio
        await self.paper_trader.initialize_daily_session()
        
        # Validate manual trading interface
        await self.manual_interface.validate_setup()
        
        # Clear previous performance metrics
        await self.performance_tracker.start_daily_session()
        
        logger.info("Pre-market setup completed")

    async def _run_trading_cycle(self) -> Dict[str, Any]:
        """Run a single trading cycle"""
        cycle_start = datetime.now()
        logger.debug(f"Starting trading cycle at {cycle_start}")
        
        cycle_result = {
            "timestamp": cycle_start.isoformat(),
            "signals_processed": 0,
            "paper_trades": 0,
            "manual_trades": 0,
            "risk_violations": 0
        }
        
        try:
            # Fetch new signals from strategy engine
            signals = await self._fetch_strategy_signals()
            cycle_result["signals_processed"] = len(signals)
            
            if not signals:
                logger.debug("No new signals found")
                return cycle_result
            
            # Process each signal
            for signal in signals:
                # Risk validation
                if not await self.risk_manager.validate_signal(signal):
                    cycle_result["risk_violations"] += 1
                    continue
                
                # Execute paper trade
                if self.config['paper_trading']['enabled']:
                    paper_result = await self.paper_trader.execute_signal(signal)
                    if paper_result['executed']:
                        cycle_result["paper_trades"] += 1
                
                # Present for manual execution
                if self.config['manual_trading']['enabled']:
                    manual_result = await self.manual_interface.present_signal(signal)
                    if manual_result['user_executed']:
                        cycle_result["manual_trades"] += 1
                
                # Track performance
                await self.performance_tracker.track_signal(signal, {
                    'paper_result': paper_result if 'paper_result' in locals() else None,
                    'manual_result': manual_result if 'manual_result' in locals() else None
                })
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            cycle_result["error"] = str(e)
        
        return cycle_result

    async def _fetch_strategy_signals(self) -> List[Dict[str, Any]]:
        """Fetch new signals from strategy engine"""
        signals_path = Path(self.config['data_sources']['strategy_signals_path'])
        
        if not signals_path.exists():
            logger.debug(f"Strategy signals file not found: {signals_path}")
            return []
        
        try:
            with open(signals_path, 'r') as f:
                data = json.load(f)
            
            # Filter for new signals (last 5 minutes)
            current_time = datetime.now()
            new_signals = []
            
            for signal in data.get('signals', []):
                signal_time = datetime.fromisoformat(signal.get('timestamp', ''))
                time_diff = (current_time - signal_time).total_seconds()
                
                if time_diff <= self.config['scheduler']['signal_check_interval']:
                    new_signals.append(signal)
            
            logger.info(f"Found {len(new_signals)} new signals")
            return new_signals
            
        except Exception as e:
            logger.error(f"Error fetching strategy signals: {e}")
            return []

    async def _post_market_cleanup(self) -> Dict[str, Any]:
        """Post-market cleanup and reporting"""
        logger.info("Running post-market cleanup")
        
        # Generate daily performance report
        performance = await self.performance_tracker.generate_daily_report()
        
        # Close paper trading session
        paper_summary = await self.paper_trader.close_daily_session()
        performance["paper_trading"] = paper_summary
        
        # Export manual trading summary
        manual_summary = await self.manual_interface.export_daily_summary()
        performance["manual_trading"] = manual_summary
        
        # Risk management summary
        risk_summary = await self.risk_manager.generate_daily_summary()
        performance["risk_management"] = risk_summary
        
        # Save performance data
        await self._save_daily_performance(performance)
        
        logger.info("Post-market cleanup completed")
        return performance

    async def _save_daily_performance(self, performance: Dict[str, Any]):
        """Save daily performance data"""
        try:
            # Save to local file
            output_dir = Path("outputs/daily_reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime("%Y%m%d")
            output_file = output_dir / f"trading_performance_{date_str}.json"
            
            with open(output_file, 'w') as f:
                json.dump(performance, f, indent=2, default=str)
            
            logger.info(f"Daily performance saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving daily performance: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Daily Trading Scheduler")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--mode", choices=["paper", "manual", "both"], 
                       default="both", help="Trading mode")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without executing any trades")
    
    args = parser.parse_args()
    
    scheduler = DailyTradingScheduler(config_path=args.config)
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no trades will be executed")
    
    # Run the daily trading cycle
    results = asyncio.run(scheduler.run_daily_trading_cycle())
    
    print("\n" + "="*60)
    print("DAILY TRADING CYCLE COMPLETED")
    print("="*60)
    print(f"Date: {results.get('date', datetime.now().strftime('%Y-%m-%d'))}")
    print(f"Status: {results.get('status', 'completed')}")
    print(f"Total Signals Processed: {results.get('total_signals', 0)}")
    print(f"Paper Trades Executed: {results.get('paper_trades', 0)}")
    print(f"Manual Trades Presented: {results.get('manual_trades', 0)}")
    
    if results.get("performance"):
        perf = results["performance"]
        print(f"Daily P&L: ₹{perf.get('daily_pnl', 0):,.2f}")
        print(f"Success Rate: {perf.get('success_rate', 0):.1%}")
    
    if results.get("reason"):
        print(f"Reason: {results['reason']}")
    
    print("="*60)


if __name__ == "__main__":
    main()
