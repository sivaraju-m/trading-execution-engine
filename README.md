# Trading Execution Engine

A modular trading execution engine for placing and managing orders through various brokers.

## Features

- Multiple broker integrations (Zerodha, Angel One, etc.)
- Order management and validation
- Real-time execution tracking
- SEBI compliance checks
- Paper trading mode

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trading-execution-engine.git
cd trading-execution-engine

# Install the package
pip install -e .
```

## Usage

```bash
# Run in simulation mode
execution-engine --config config/execution_config.yaml --mode simulation

# Run with paper trading
execution-engine --config config/execution_config.yaml --mode paper

# Run with live trading (use with caution)
execution-engine --config config/execution_config.yaml --mode live
```

See documentation for more details.
