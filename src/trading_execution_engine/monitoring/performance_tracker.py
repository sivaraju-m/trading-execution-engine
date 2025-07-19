"""
Execution Performance Tracker
============================

Tracks and analyzes trading execution performance.

Author: SJ Trading
Licensed by SJ Trading
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionPerformanceTracker:
    """
    Tracks and analyzes execution performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.daily_metrics = {}
        self.signal_tracking = []
        self.execution_tracking = []
        
        # Alert thresholds
        self.alert_thresholds = config.get('alert_thresholds', {
            'daily_loss_pct': 2,
            'drawdown_pct': 5,
            'low_success_rate': 0.4
        })
        
        logger.info("Execution performance tracker initialized")
    
    async def start_daily_session(self):
        """Start a new daily tracking session"""
        self.daily_metrics = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'session_start': datetime.now().isoformat(),
            'signals_received': 0,
            'signals_executed_paper': 0,
            'signals_executed_manual': 0,
            'total_pnl': 0.0,
            'success_rate': 0.0,
            'max_drawdown': 0.0,
            'alerts_triggered': []
        }
        
        self.signal_tracking = []
        self.execution_tracking = []
        
        logger.info("Daily performance tracking session started")
    
    async def track_signal(self, signal: Dict[str, Any], execution_results: Dict[str, Any]):
        """Track a signal and its execution results"""
        tracking_entry = {
            'timestamp': datetime.now().isoformat(),
            'signal_id': signal.get('signal_id', f"signal_{len(self.signal_tracking)}"),
            'symbol': signal.get('symbol'),
            'action': signal.get('action'),
            'strategy': signal.get('strategy'),
            'signal_strength': signal.get('strength', 0),
            'signal_price': signal.get('price', 0),
            'paper_result': execution_results.get('paper_result'),
            'manual_result': execution_results.get('manual_result'),
            'signal_data': signal
        }
        
        self.signal_tracking.append(tracking_entry)
        self.daily_metrics['signals_received'] += 1
        
        # Track execution counts
        if execution_results.get('paper_result', {}).get('executed'):
            self.daily_metrics['signals_executed_paper'] += 1
            
        if execution_results.get('manual_result', {}).get('user_executed'):
            self.daily_metrics['signals_executed_manual'] += 1
        
        # Update P&L if available
        paper_pnl = execution_results.get('paper_result', {}).get('pnl', 0)
        self.daily_metrics['total_pnl'] += paper_pnl
        
        # Check for alerts
        await self._check_alerts()
        
        logger.debug(f"Signal tracked: {tracking_entry['signal_id']} for {tracking_entry['symbol']}")
    
    async def track_execution(self, execution_data: Dict[str, Any]):
        """Track execution details"""
        execution_entry = {
            'timestamp': datetime.now().isoformat(),
            'execution_id': execution_data.get('execution_id', f"exec_{len(self.execution_tracking)}"),
            'signal_id': execution_data.get('signal_id'),
            'execution_type': execution_data.get('execution_type', 'unknown'),  # paper, manual, live
            'symbol': execution_data.get('symbol'),
            'action': execution_data.get('action'),
            'quantity': execution_data.get('quantity', 0),
            'execution_price': execution_data.get('execution_price', 0),
            'expected_price': execution_data.get('expected_price', 0),
            'slippage': execution_data.get('slippage', 0),
            'commission': execution_data.get('commission', 0),
            'pnl': execution_data.get('pnl', 0),
            'execution_time_ms': execution_data.get('execution_time_ms', 0)
        }
        
        self.execution_tracking.append(execution_entry)
        
        logger.debug(f"Execution tracked: {execution_entry['execution_id']}")
    
    async def _check_alerts(self):
        """Check for performance alerts"""
        # Check daily loss threshold
        if self.daily_metrics['total_pnl'] < 0:
            loss_pct = abs(self.daily_metrics['total_pnl']) / 1000000 * 100  # Assuming 10L capital
            if loss_pct > self.alert_thresholds['daily_loss_pct']:
                alert = {
                    'type': 'daily_loss_exceeded',
                    'message': f"Daily loss of {loss_pct:.2f}% exceeds threshold of {self.alert_thresholds['daily_loss_pct']}%",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'high'
                }
                self.daily_metrics['alerts_triggered'].append(alert)
                logger.warning(alert['message'])
        
        # Check success rate
        total_executed = self.daily_metrics['signals_executed_paper'] + self.daily_metrics['signals_executed_manual']
        if total_executed > 0:
            # For simplicity, assume successful if P&L > 0
            successful_trades = len([t for t in self.signal_tracking 
                                   if t.get('paper_result', {}).get('pnl', 0) > 0])
            success_rate = successful_trades / total_executed
            self.daily_metrics['success_rate'] = success_rate
            
            if success_rate < self.alert_thresholds['low_success_rate']:
                alert = {
                    'type': 'low_success_rate',
                    'message': f"Success rate of {success_rate:.1%} below threshold of {self.alert_thresholds['low_success_rate']:.1%}",
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'medium'
                }
                self.daily_metrics['alerts_triggered'].append(alert)
                logger.warning(alert['message'])
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily performance report"""
        # Finalize daily metrics
        self.daily_metrics['session_end'] = datetime.now().isoformat()
        
        # Calculate detailed analytics
        analytics = await self._calculate_analytics()
        
        report = {
            'summary': self.daily_metrics,
            'analytics': analytics,
            'signal_details': self.signal_tracking,
            'execution_details': self.execution_tracking,
            'alerts': self.daily_metrics['alerts_triggered']
        }
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(analytics)
        report['recommendations'] = recommendations
        
        logger.info(f"Daily performance report generated: {self.daily_metrics['signals_received']} signals, "
                   f"P&L: ₹{self.daily_metrics['total_pnl']:.2f}, "
                   f"Success Rate: {self.daily_metrics['success_rate']:.1%}")
        
        return report
    
    async def _calculate_analytics(self) -> Dict[str, Any]:
        """Calculate detailed performance analytics"""
        analytics = {
            'signal_analytics': {},
            'execution_analytics': {},
            'strategy_performance': {},
            'symbol_performance': {}
        }
        
        # Signal analytics
        if self.signal_tracking:
            signals_by_strategy = {}
            signals_by_symbol = {}
            
            for signal in self.signal_tracking:
                strategy = signal.get('strategy', 'unknown')
                symbol = signal.get('symbol', 'unknown')
                
                if strategy not in signals_by_strategy:
                    signals_by_strategy[strategy] = {'count': 0, 'pnl': 0}
                if symbol not in signals_by_symbol:
                    signals_by_symbol[symbol] = {'count': 0, 'pnl': 0}
                
                signals_by_strategy[strategy]['count'] += 1
                signals_by_symbol[symbol]['count'] += 1
                
                paper_pnl = signal.get('paper_result', {}).get('pnl', 0)
                signals_by_strategy[strategy]['pnl'] += paper_pnl
                signals_by_symbol[symbol]['pnl'] += paper_pnl
            
            analytics['strategy_performance'] = signals_by_strategy
            analytics['symbol_performance'] = signals_by_symbol
        
        # Execution analytics
        if self.execution_tracking:
            total_slippage = sum(exec['slippage'] for exec in self.execution_tracking)
            total_commission = sum(exec['commission'] for exec in self.execution_tracking)
            avg_execution_time = sum(exec['execution_time_ms'] for exec in self.execution_tracking) / len(self.execution_tracking)
            
            analytics['execution_analytics'] = {
                'total_executions': len(self.execution_tracking),
                'total_slippage': total_slippage,
                'total_commission': total_commission,
                'avg_execution_time_ms': avg_execution_time,
                'avg_slippage_per_trade': total_slippage / len(self.execution_tracking)
            }
        
        return analytics
    
    async def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Strategy recommendations
        strategy_perf = analytics.get('strategy_performance', {})
        for strategy, perf in strategy_perf.items():
            if perf['pnl'] < 0:
                recommendations.append(f"Review {strategy} strategy - negative P&L of ₹{perf['pnl']:.2f}")
        
        # Execution recommendations
        exec_analytics = analytics.get('execution_analytics', {})
        if exec_analytics.get('avg_slippage_per_trade', 0) > 50:
            recommendations.append("High slippage detected - consider adjusting execution timing")
        
        # Success rate recommendations
        if self.daily_metrics['success_rate'] < 0.5:
            recommendations.append("Low success rate - review signal quality and entry criteria")
        
        # Risk recommendations
        if self.daily_metrics['total_pnl'] < -10000:
            recommendations.append("High daily loss - consider reducing position sizes")
        
        return recommendations
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        return {
            'current_pnl': self.daily_metrics['total_pnl'],
            'signals_today': self.daily_metrics['signals_received'],
            'executions_today': self.daily_metrics['signals_executed_paper'] + self.daily_metrics['signals_executed_manual'],
            'success_rate': self.daily_metrics['success_rate'],
            'alerts_count': len(self.daily_metrics['alerts_triggered'])
        }
