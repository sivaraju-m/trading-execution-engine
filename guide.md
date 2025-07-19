# Trading Execution Engine - Complete Guide

## 📋 Overview
This comprehensive guide covers everything you need to know about the Trading Execution Engine, from basic setup to advanced trading operations and SEBI compliance.

## 🎯 Project Purpose
The Trading Execution Engine provides:
1. **SEBI-compliant manual trading execution** for Indian markets
2. **Paper trading simulation** for strategy validation
3. **Real-time risk management** and position monitoring
4. **Performance analytics** and execution quality measurement
5. **Integration with Strategy Engine** for automated signal processing

## 🏗️ System Architecture

### Core Components

#### 1. Daily Trading Scheduler (`bin/daily_trading_scheduler.py`)
**Purpose**: Orchestrates the entire daily trading workflow
**Key Features**:
- Market hours validation for Indian markets (NSE/BSE)
- Automated paper trading execution
- Manual execution interface for SEBI compliance
- Real-time risk monitoring and alerts
- Performance tracking and daily reporting

**Usage**:
```bash
# Dry run mode (recommended for testing)
python bin/daily_trading_scheduler.py --dry-run

# Paper trading mode
python bin/daily_trading_scheduler.py --mode paper

# Manual execution mode (SEBI compliant)
python bin/daily_trading_scheduler.py --mode manual

# Combined mode (paper + manual)
python bin/daily_trading_scheduler.py --mode both
```

#### 2. Paper Trading Engine (`src/trading_execution_engine/execution/paper_trader.py`)
**Purpose**: Simulates real trading with realistic market conditions
**Key Features**:
- Realistic slippage calculation (5 basis points default)
- Commission modeling (₹20 per trade default)
- Portfolio tracking with average price calculation
- Daily P&L and performance reporting
- Capital management and position sizing

**Configuration**:
```yaml
paper_trading:
  enabled: true
  initial_capital: 1000000     # ₹10 Lakh
  commission_per_trade: 20     # ₹20 per trade
  slippage_bps: 5             # 5 basis points
  simulate_market_impact: true
  use_realistic_fills: true
```

#### 3. Manual Execution Interface (`src/trading_execution_engine/execution/manual_interface.py`)
**Purpose**: SEBI-compliant manual trading workflow
**Key Features**:
- Signal presentation with complete trade details
- User decision tracking and audit trails
- Manual execution confirmation system
- Cooling period enforcement between trades
- Comprehensive compliance logging

**SEBI Compliance Features**:
- All trades require explicit manual approval
- Complete audit trail of all decisions
- User discretion over all trade executions
- No automated live trading capabilities
- Regulatory reporting and documentation

#### 4. Risk Management System (`src/trading_execution_engine/risk/manager.py`)
**Purpose**: Comprehensive risk control and monitoring
**Key Features**:
- Position size limits (5% of capital max)
- Daily loss limits (3% of capital max)
- Stop-loss enforcement (2% default)
- Concentration risk monitoring (20% max per sector)
- Real-time risk violation alerts

**Risk Parameters**:
```yaml
risk_management:
  max_position_size_pct: 5      # Max position size
  max_daily_loss_pct: 3         # Daily loss limit
  stop_loss_pct: 2              # Stop-loss requirement
  max_concentration_pct: 20     # Sector concentration limit
  total_capital: 1000000        # Total capital (₹10 Lakh)
```

#### 5. Performance Tracker (`src/trading_execution_engine/monitoring/performance_tracker.py`)
**Purpose**: Real-time performance monitoring and analytics
**Key Features**:
- Signal-level performance tracking
- Execution quality metrics
- Daily performance reporting
- Strategy and symbol-level analytics
- Alert system for performance thresholds

#### 6. Market Hours Validator (`src/trading_execution_engine/utils/market_hours.py`)
**Purpose**: Indian market timing and holiday validation
**Key Features**:
- NSE/BSE market hours validation
- Holiday calendar integration (2024-2025)
- Pre-market and post-market session detection
- Trading session status monitoring
- Market timing calculations

**Market Timings**:
- **Pre-Market**: 9:00 AM - 9:15 AM IST
- **Market Hours**: 9:15 AM - 3:30 PM IST
- **Post-Market**: 3:30 PM - 4:00 PM IST

## 🚀 Getting Started

### Step 1: Installation and Setup
```bash
# Navigate to the project directory
cd /Users/sivarajumalladi/Documents/GitHub/trading-execution-engine

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Step 2: Configuration
```bash
# Edit the main configuration file
vim config/daily_scheduler/config.yaml

# Key sections to configure:
# 1. Risk management parameters
# 2. Trading universe symbols
# 3. Paper trading settings
# 4. SEBI compliance options
# 5. Performance thresholds
```

### Step 3: Strategy Engine Integration
```bash
# Ensure strategy engine is running and generating signals
cd ../strategy-engine
python bin/daily_strategy_runner.py

# Verify signal file exists
ls outputs/daily_signals.json
```

### Step 4: First Run
```bash
# Start with dry-run mode
python bin/daily_trading_scheduler.py --dry-run

# Check logs for any issues
tail -f logs/trading_execution_engine_*.log
```

## 📊 Daily Operations Workflow

### Pre-Market Operations (9:00 AM - 9:15 AM IST)

#### 1. System Health Check
```bash
# Verify all components are operational
python -c "
from src.trading_execution_engine.utils.market_hours import MarketHoursValidator
from src.trading_execution_engine.risk.manager import RiskManager
print('Market Status:', MarketHoursValidator().get_market_status())
print('Risk Manager initialized successfully')
"
```

#### 2. Configuration Validation
```bash
# Validate configuration file
python -c "
import yaml
with open('config/daily_scheduler/config.yaml') as f:
    config = yaml.safe_load(f)
print('Configuration loaded successfully')
print(f'Risk limits: {config[\"risk_management\"]}')
"
```

#### 3. Strategy Signal Check
```bash
# Check for new signals from strategy engine
ls -la ../strategy-engine/outputs/daily_signals.json
```

### Market Hours Operations (9:15 AM - 3:30 PM IST)

#### 1. Start Daily Scheduler
```bash
# Start the main trading system
python bin/daily_trading_scheduler.py --mode both

# Monitor in separate terminal
tail -f logs/trading_execution_engine_*.log
```

#### 2. Signal Processing Flow
1. **Signal Ingestion**: Read signals from strategy engine
2. **Risk Validation**: Check against risk parameters
3. **Paper Trading**: Execute simulation trades
4. **Manual Interface**: Present signals for manual review
5. **Performance Tracking**: Monitor execution quality

#### 3. Real-Time Monitoring
```bash
# Monitor paper trading performance
python -c "
from src.trading_execution_engine.monitoring.performance_tracker import ExecutionPerformanceTracker
tracker = ExecutionPerformanceTracker({})
print('Performance tracking active')
"
```

### Post-Market Operations (3:30 PM - 4:00 PM IST)

#### 1. Session Closure
- Automatic closure of paper trading positions
- Generation of daily performance reports
- Risk management summary
- Compliance audit export

#### 2. Daily Reports
```bash
# View daily performance report
ls outputs/daily_reports/trading_performance_*.json

# Check risk management summary
python -c "
import json
from datetime import datetime
date_str = datetime.now().strftime('%Y%m%d')
with open(f'outputs/daily_reports/trading_performance_{date_str}.json') as f:
    report = json.load(f)
print('Daily P&L:', report.get('paper_trading', {}).get('daily_pnl', 0))
"
```

## 🛡️ SEBI Compliance Guide

### Manual Execution Requirements

#### 1. Signal Presentation
When a signal is received from the strategy engine:
```
🚨 NEW TRADING SIGNAL FOR MANUAL EXECUTION
============================================================
Signal ID: signal_001
Symbol: RELIANCE.NS
Action: BUY
Strategy: rsi
Signal Strength: 0.85
Recommended Price: ₹2,850.50
Recommended Quantity: 35
Estimated Value: ₹99,767.50
Stop Loss: ₹2,793.00
Target: ₹2,965.00
Risk/Reward: 1:2.0

⚠️  SEBI COMPLIANCE NOTICE:
This is a signal for manual execution only.
Please review and execute manually through your broker.
============================================================
```

#### 2. User Decision Process
- **Review Signal**: Analyze all signal parameters
- **Risk Assessment**: Validate against personal risk tolerance
- **Manual Execution**: Execute through your broker platform
- **Record Keeping**: System maintains audit trail

#### 3. Compliance Features
- **No Automated Execution**: System never places live orders
- **Complete Audit Trail**: All signals and decisions logged
- **User Discretion**: Full control over all trade decisions
- **Regulatory Reporting**: Built-in compliance documentation

### Audit Trail Example
```json
{
  "signal_id": "signal_001",
  "timestamp": "2025-07-19T10:30:00+05:30",
  "symbol": "RELIANCE.NS",
  "action": "BUY",
  "signal_strength": 0.85,
  "user_decision": "executed",
  "execution_method": "manual",
  "execution_time": "2025-07-19T10:32:15+05:30",
  "execution_price": 2849.75,
  "broker_order_id": "user_provided",
  "compliance_notes": "Manual execution via broker platform"
}
```

## 📈 Performance Analytics

### Key Metrics Tracked

#### 1. Execution Quality
- **Slippage Analysis**: Difference between signal price and execution price
- **Fill Rate**: Percentage of signals successfully executed
- **Execution Latency**: Time from signal generation to execution
- **Market Impact**: Effect of trades on market prices

#### 2. Strategy Performance
- **Signal Accuracy**: Percentage of profitable signals
- **Risk-Adjusted Returns**: Sharpe ratio and other metrics
- **Drawdown Analysis**: Maximum portfolio decline
- **Win/Loss Ratios**: Success rate by strategy and symbol

#### 3. Risk Metrics
- **Position Concentration**: Exposure by symbol and sector
- **VaR (Value at Risk)**: Potential portfolio loss
- **Risk Limit Utilization**: Usage of available risk limits
- **Violation Frequency**: Risk limit breach frequency

### Daily Performance Report Structure
```json
{
  "summary": {
    "date": "2025-07-19",
    "signals_received": 25,
    "signals_executed_paper": 22,
    "signals_executed_manual": 8,
    "total_pnl": 15750.50,
    "success_rate": 0.68
  },
  "analytics": {
    "strategy_performance": {
      "rsi": {"count": 12, "pnl": 8500.25},
      "momentum": {"count": 8, "pnl": 4250.75},
      "bollinger_bands": {"count": 5, "pnl": 3000.00}
    },
    "execution_analytics": {
      "total_slippage": 125.50,
      "avg_execution_time_ms": 85,
      "commission_paid": 440.00
    }
  },
  "recommendations": [
    "RSI strategy showing strong performance",
    "Consider increasing position size for momentum strategy",
    "Review bollinger bands parameters"
  ]
}
```

## 🔧 Advanced Configuration

### Risk Management Customization
```yaml
risk_management:
  # Position sizing
  max_position_size_pct: 5          # 5% of capital max
  max_daily_loss_pct: 3             # 3% daily loss limit
  stop_loss_pct: 2                  # 2% stop-loss
  max_concentration_pct: 20         # 20% sector max
  
  # Dynamic adjustments
  volatility_adjustment: true       # Adjust limits based on volatility
  market_regime_adjustment: true    # Adjust for bull/bear markets
  
  # Circuit breakers
  enable_circuit_breakers: true
  circuit_breaker_loss_pct: 5       # Halt trading at 5% loss
  cooling_period_minutes: 60        # 1-hour cool-down
```

### Strategy-Specific Settings
```yaml
strategies:
  rsi:
    enabled: true
    max_signals_per_day: 5
    position_size_multiplier: 1.0
    custom_risk_params:
      max_position_size_pct: 4      # Lower limit for RSI
  
  momentum:
    enabled: true
    max_signals_per_day: 3
    position_size_multiplier: 1.2    # Higher allocation
    custom_risk_params:
      stop_loss_pct: 1.5            # Tighter stop-loss
```

### Universe Configuration
```yaml
universe:
  # Load symbols from external file
  symbols_file: "config/universe_250.json"
  
  # Or define directly
  symbols:
    - "RELIANCE.NS"
    - "TCS.NS"
    - "HDFCBANK.NS"
    # ... 247 more symbols
  
  # Symbol filtering
  filters:
    min_market_cap: 1000000000      # ₹1000 Cr minimum
    max_volatility: 0.05            # 5% max daily volatility
    min_volume: 100000              # Minimum daily volume
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Market Hours Validation Errors
**Issue**: "Market is closed today - skipping trading cycle"
**Solution**:
```bash
# Check market status
python -c "
from src.trading_execution_engine.utils.market_hours import MarketHoursValidator
validator = MarketHoursValidator()
print('Is market day:', validator.is_market_day())
print('Market status:', validator.get_market_status())
"

# For testing on weekends/holidays, modify the validator temporarily
```

#### 2. Strategy Signal File Not Found
**Issue**: Strategy signals file not found at expected location
**Solution**:
```bash
# Check if strategy engine is running
cd ../strategy-engine
python bin/daily_strategy_runner.py

# Verify signal file creation
ls -la outputs/daily_signals.json

# Update path in config if needed
vim config/daily_scheduler/config.yaml
```

#### 3. Risk Limit Violations
**Issue**: All signals rejected due to risk violations
**Solution**:
```bash
# Check current risk parameters
python -c "
from src.trading_execution_engine.risk.manager import RiskManager
risk_mgr = RiskManager({'total_capital': 1000000})
print('Available buying power:', risk_mgr.get_available_buying_power())
"

# Adjust risk limits in config
vim config/daily_scheduler/config.yaml
```

#### 4. Paper Trading Execution Failures
**Issue**: Paper trades not executing properly
**Solution**:
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python bin/daily_trading_scheduler.py --dry-run

# Check paper trader configuration
python -c "
from src.trading_execution_engine.execution.paper_trader import PaperTrader
config = {'enabled': True, 'initial_capital': 1000000}
trader = PaperTrader(config)
print('Paper trader initialized successfully')
"
```

### Log Analysis
```bash
# View recent logs
tail -n 100 logs/trading_execution_engine_*.log

# Search for errors
grep -i error logs/trading_execution_engine_*.log

# Monitor real-time
tail -f logs/trading_execution_engine_*.log | grep -E "(ERROR|WARNING|INFO)"
```

## 📚 Integration with Other Subprojects

### Strategy Engine Integration
```bash
# 1. Strategy engine generates signals
cd ../strategy-engine
python bin/daily_strategy_runner.py

# 2. Trading execution engine processes signals
cd ../trading-execution-engine
python bin/daily_trading_scheduler.py --mode both

# 3. Check integration status
python -c "
import json
import os
signals_file = '../strategy-engine/outputs/daily_signals.json'
if os.path.exists(signals_file):
    with open(signals_file) as f:
        data = json.load(f)
    print(f'Found {len(data.get(\"signals\", []))} signals')
else:
    print('No signals file found')
"
```

### Shared Services Integration
```python
# Using shared configuration management
from shared_services.config.config_manager import ConfigManager

config_mgr = ConfigManager()
trading_config = config_mgr.get_config('trading_execution_engine')
```

### Monitoring Dashboard Integration
```python
# Export metrics to monitoring dashboard
from trading_execution_engine.monitoring.performance_tracker import ExecutionPerformanceTracker

tracker = ExecutionPerformanceTracker({})
metrics = tracker.get_real_time_metrics()

# Send to monitoring dashboard
# (Implementation depends on monitoring dashboard API)
```

## 🎯 Best Practices

### 1. Daily Operations Checklist
- [ ] **Pre-Market**: Validate system health and configuration
- [ ] **Market Open**: Start daily scheduler and monitor logs
- [ ] **During Market**: Monitor risk limits and performance
- [ ] **Market Close**: Review daily reports and performance
- [ ] **Post-Market**: Archive logs and prepare for next day

### 2. Risk Management
- **Never Override Risk Limits**: Always respect configured limits
- **Regular Risk Review**: Weekly review of risk parameters
- **Position Monitoring**: Continuous monitoring of concentration
- **Stop-Loss Discipline**: Always enforce stop-loss requirements

### 3. Performance Monitoring
- **Daily Performance Review**: Analyze daily reports
- **Strategy Evaluation**: Regular assessment of strategy performance
- **Execution Quality**: Monitor slippage and fill rates
- **Continuous Improvement**: Regular parameter optimization

### 4. Compliance Maintenance
- **Audit Trail**: Maintain complete records of all decisions
- **Manual Execution**: Never automate live trading
- **Documentation**: Keep detailed operational logs
- **Regulatory Updates**: Stay current with SEBI regulations

## 📖 Additional Resources

### Documentation Files
- **[TODO.md](todo.md)**: Detailed implementation roadmap
- **[README.md](README.md)**: Project overview and quick start
- **API Reference**: Complete module documentation
- **Operations Manual**: Detailed operational procedures

### Code Examples
```python
# Example: Manual signal processing
from src.trading_execution_engine.execution.manual_interface import ManualExecutionInterface

interface = ManualExecutionInterface({'enabled': True})
signal = {
    'symbol': 'RELIANCE.NS',
    'action': 'BUY',
    'price': 2850.50,
    'quantity': 35,
    'strategy': 'rsi',
    'strength': 0.85
}

result = await interface.present_signal(signal)
print(f"User executed: {result['user_executed']}")
```

### Configuration Templates
```yaml
# Minimal configuration for testing
scheduler:
  signal_check_interval: 300
paper_trading:
  enabled: true
  initial_capital: 100000    # ₹1 Lakh for testing
risk_management:
  max_position_size_pct: 2   # Conservative 2%
  max_daily_loss_pct: 1      # Conservative 1%
```

---

**Last Updated**: July 19, 2025  
**Version**: 1.0.0  
**Author**: SJ Trading Team  
**Contact**: For questions and support, check the project's GitHub issues page
