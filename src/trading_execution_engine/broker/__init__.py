"""
Broker module for trading execution engine

This module provides interfaces and implementations for interacting with brokers.
"""

from trading_execution_engine.broker.broker_interface import (
    BrokerInterface,
    MockBrokerInterface,
    broker_interface,
)

__all__ = [
    "BrokerInterface",
    "MockBrokerInterface",
    "broker_interface",
]
