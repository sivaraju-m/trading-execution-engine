# Trading Execution Engine

## 🎯 Overview
The Trading Execution Engine is a sophisticated, SEBI-compliant trading system for Indian markets that handles live trading execution, paper trading simulation, and manual trading interfaces. It provides institutional-grade execution capabilities while maintaining full regulatory compliance.

## ✅ **CURRENT STATUS** (July 19, 2025)
- ✅ **Daily Trading Scheduler**: Fully operational with market hours validation
- ✅ **Paper Trading Engine**: Complete simulation with realistic slippage and commission
- ✅ **Manual Execution Interface**: SEBI-compliant manual trading workflow
- ✅ **Risk Management System**: Comprehensive risk controls and monitoring
- ✅ **Performance Tracking**: Real-time analytics and daily reporting
- ✅ **Market Hours Validator**: Indian market timing and holiday validation
- 🔄 **Live Trading Integration**: In development (broker API integration)

## 🚀 Key Features

### 📈 Trading Capabilities
- **Paper Trading**: Realistic simulation with slippage, commission, and market impact
- **Manual Execution**: SEBI-compliant manual trading interface with audit trails
- **Risk Management**: Real-time position limits, stop-losses, and circuit breakers
- **Order Management**: Comprehensive order lifecycle tracking and monitoring
- **Performance Analytics**: Detailed execution quality and P&L analysis

### 🛡️ SEBI Compliance
- **Manual Execution Only**: All real trades require manual user approval
- **Comprehensive Audit Trail**: Complete logging of all signals and decisions
- **Risk Limit Enforcement**: Automated position and loss limit monitoring
- **Regulatory Reporting**: Built-in compliance reporting and documentation

### ⚡ Real-Time Capabilities
- **Market Hours Validation**: Indian market timing with holiday calendar
- **Signal Processing**: Real-time signal ingestion from strategy engine
- **Performance Monitoring**: Live P&L and risk metric tracking
- **Alert System**: Multi-level alerts for risks and performance thresholds

## 🏗️ Architecture

```
trading-execution-engine/
├── bin/
│   ├── daily_trading_scheduler.py    # ✅ Main daily trading coordinator
│   ├── automated_trading_system.py   # ✅ Paper trading system
│   └── live_trading_flow.py          # ✅ Live trading workflow
├── src/trading_execution_engine/
│   ├── core/
│   │   └── scheduler.py              # ✅ Trading scheduler
│   ├── execution/
│   │   ├── paper_trader.py           # ✅ Paper trading engine
│   │   └── manual_interface.py       # ✅ Manual execution interface
│   ├── risk/
│   │   └── manager.py                # ✅ Risk management system
│   ├── monitoring/
│   │   └── performance_tracker.py    # ✅ Performance analytics
│   └── utils/
│       ├── logger.py                 # ✅ Logging utilities
│       └── market_hours.py           # ✅ Market timing validation
├── config/
│   └── daily_scheduler/
│       └── config.yaml               # ✅ Configuration management
└── tests/                            # 🔄 Test suite (in development)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Required dependencies (see requirements.txt)
- Strategy Engine signals (from strategy-engine project)

### Installation
```bash
# Clone the repository
git clone https://github.com/sivarajumalladi/trading-execution-engine.git
cd trading-execution-engine

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Configuration
```bash
# Edit configuration file
vim config/daily_scheduler/config.yaml

# Key configuration areas:
# - Risk management parameters
# - Trading universe (250 symbols)
# - Paper trading settings
# - SEBI compliance options
```

### Running the System

#### Daily Trading Scheduler (Recommended)
```bash
# Run in dry-run mode (no actual trades)
python bin/daily_trading_scheduler.py --dry-run

# Run with paper trading only
python bin/daily_trading_scheduler.py --mode paper

# Run with manual execution interface
python bin/daily_trading_scheduler.py --mode manual

# Run with both paper and manual trading
python bin/daily_trading_scheduler.py --mode both
```

#### Paper Trading System
```bash
# Start paper trading system
python bin/automated_trading_system.py

# Monitor paper trading performance
tail -f logs/trading_execution_engine_*.log
```

## 📊 Configuration

### Risk Management (`config/daily_scheduler/config.yaml`)
```yaml
risk_management:
  max_position_size_pct: 5      # Maximum 5% of capital per position
  max_daily_loss_pct: 3         # Maximum 3% daily loss limit
  stop_loss_pct: 2              # 2% stop-loss requirement
  max_concentration_pct: 20     # Maximum 20% sector concentration
  total_capital: 1000000        # 10 Lakh total capital
```

### Trading Universe
- **250 carefully selected symbols** from NSE
- **No hardcoded tickers** - all symbols loaded from config
- **Sector diversification** across IT, Finance, Energy, Consumer, etc.
- **Market cap coverage** from large cap to small cap stocks

### SEBI Compliance Settings
```yaml
compliance:
  sebi_compliant: true           # Enable SEBI compliance mode
  manual_execution_only: true   # Require manual approval for all trades
  comprehensive_audit: true     # Enable complete audit logging
  maintain_audit_trail: true    # Keep detailed audit records
```

## 📈 Performance Metrics

### Execution Quality (Target KPIs)
- **Slippage**: < 5 basis points average
- **Fill Rate**: > 99% for paper trades
- **Execution Latency**: < 100ms for signal processing
- **System Uptime**: > 99.9% during market hours

### Risk Management
- **Daily Loss Limit**: Never exceeded in paper trading
- **Position Limits**: 100% compliance with risk parameters
- **Stop-Loss Adherence**: Automatic enforcement in paper mode
- **Risk Violations**: < 0.1% of total signals

### Current Performance (July 19, 2025)
- **Paper Trading Capital**: ₹10,00,000 initial
- **Risk Management**: Fully operational with real-time monitoring
- **Signal Processing**: Ready for strategy-engine integration
- **Compliance Status**: 100% SEBI compliant with audit trails

## 🔄 Integration with Other Subprojects

### Strategy Engine Integration
```bash
# Strategy engine outputs signals to:
../strategy-engine/outputs/daily_signals.json

# Trading execution engine reads signals and processes them through:
# 1. Risk validation
# 2. Paper trading simulation
# 3. Manual execution interface
# 4. Performance tracking
```

### Shared Services Integration
- **Configuration Management**: Centralized config via shared-services
- **Logging**: Unified logging across all subprojects
- **Utilities**: Common helper functions and data structures

### Monitoring Dashboard Integration
- **Real-time Data Feed**: Live execution and performance metrics
- **Alert Integration**: Risk and performance alerts
- **Reporting**: Daily execution and performance reports

## 🛡️ Risk Management Features

### Position Risk Controls
- **Position Size Limits**: Maximum 5% of capital per position
- **Concentration Limits**: Maximum 20% per sector/strategy
- **Stop-Loss Enforcement**: Automatic 2% stop-loss requirement
- **Daily Loss Limits**: Maximum 3% daily portfolio loss

### Real-Time Monitoring
- **Live P&L Tracking**: Real-time profit and loss monitoring
- **Risk Violation Alerts**: Immediate alerts for limit breaches
- **Circuit Breakers**: Automatic trading halt on extreme losses
- **Performance Analytics**: Continuous performance evaluation

## 📊 Daily Operations

### Pre-Market (9:00 AM - 9:15 AM IST)
1. **System Health Check**: Validate all components
2. **Risk Limit Reset**: Initialize daily risk parameters
3. **Signal Validation**: Check strategy engine connectivity
4. **Paper Trading Setup**: Initialize daily trading session

### Market Hours (9:15 AM - 3:30 PM IST)
1. **Signal Processing**: Real-time signal ingestion and validation
2. **Paper Trading**: Automatic simulation of all valid signals
3. **Manual Interface**: Present signals for manual execution
4. **Risk Monitoring**: Continuous risk and performance tracking

### Post-Market (3:30 PM - 4:00 PM IST)
1. **Session Closure**: Close all paper trading positions
2. **Performance Report**: Generate daily analytics report
3. **Risk Summary**: Daily risk management summary
4. **Audit Export**: Export compliance and audit data

## 🔧 Development & Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src/trading_execution_engine tests/
```

### Development Mode
```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run with debug logging
LOG_LEVEL=DEBUG python bin/daily_trading_scheduler.py --dry-run

# Monitor logs in real-time
tail -f logs/trading_execution_engine_*.log
```

## 📚 Documentation

- **[TODO.md](todo.md)**: Detailed implementation roadmap and task list
- **[Guide.md](guide.md)**: Comprehensive user and developer guide
- **[API Reference](docs/api_reference.md)**: Complete API documentation
- **[Operations Manual](docs/operations_manual.md)**: Daily operations guide

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes and test**: Ensure all tests pass
4. **Commit changes**: `git commit -am 'Add new feature'`
5. **Push to branch**: `git push origin feature/new-feature`
6. **Create Pull Request**: Submit for review

## 📋 Support & Issues

For support and issue reporting:
- **GitHub Issues**: [Create an issue](https://github.com/sivarajumalladi/trading-execution-engine/issues)
- **Documentation**: Check docs/ directory for detailed guides
- **Logs**: Check logs/ directory for system logs and errors

## ⚖️ Compliance & Legal

### SEBI Compliance
- **Manual Execution Requirement**: All real trades require manual approval
- **Audit Trail**: Complete logging of all trading decisions
- **Risk Management**: Comprehensive risk controls and monitoring
- **Regulatory Reporting**: Built-in compliance reporting capabilities

### Disclaimer
This software is for educational and research purposes. Users are responsible for compliance with all applicable regulations and laws. Past performance does not guarantee future results.

---

**Project Status**: 🟢 Operational  
**Last Updated**: July 19, 2025  
**Version**: 0.1.0  
**License**: Proprietary - SJ Trading
