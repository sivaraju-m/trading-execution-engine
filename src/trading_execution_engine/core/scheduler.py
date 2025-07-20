"""
Trading Execution Engine Core Scheduler
======================================

Provides scheduling and coordination for trading operations.

Author: SJ Trading
Licensed by SJ Trading
"""

import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TradingScheduler:
    """
    Core scheduler for trading operations
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.scheduled_tasks: List[asyncio.Task] = []

        # Market timing configuration
        self.market_open = self._parse_time(config.get("market_open_time", "09:15"))
        self.market_close = self._parse_time(config.get("market_close_time", "15:30"))
        self.signal_interval = config.get("signal_check_interval", 300)  # 5 minutes

        logger.info("Trading scheduler initialized")

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to time object"""
        hour, minute = map(int, time_str.split(":"))
        return dt_time(hour, minute)

    async def start_scheduler(self):
        """Start the trading scheduler"""
        self.is_running = True
        logger.info("Trading scheduler started")

    async def stop_scheduler(self):
        """Stop the trading scheduler"""
        self.is_running = False

        # Cancel all scheduled tasks
        for task in self.scheduled_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.scheduled_tasks:
            await asyncio.gather(*self.scheduled_tasks, return_exceptions=True)

        logger.info("Trading scheduler stopped")

    def schedule_task(self, coro, delay: float = 0):
        """Schedule a coroutine to run"""
        task = asyncio.create_task(self._delayed_execution(coro, delay))
        self.scheduled_tasks.append(task)
        return task

    async def _delayed_execution(self, coro, delay: float):
        """Execute a coroutine after a delay"""
        if delay > 0:
            await asyncio.sleep(delay)
        return await coro

    def is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now().time()
        return self.market_open <= now <= self.market_close

    def get_next_signal_time(self) -> Optional[datetime]:
        """Get the next scheduled signal check time"""
        if not self.is_market_hours():
            return None

        now = datetime.now()
        next_time = now.timestamp() + self.signal_interval
        return datetime.fromtimestamp(next_time)
