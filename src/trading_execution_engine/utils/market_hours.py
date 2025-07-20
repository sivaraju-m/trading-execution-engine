"""
Market Hours Validator
=====================

Validates market timing and trading hours for Indian markets.

Author: SJ Trading
Licensed by SJ Trading
"""

import pytz
from datetime import datetime, time as dt_time, date
from typing import List, Tuple

from .logger import get_logger

logger = get_logger(__name__)


class MarketHoursValidator:
    """
    Validates market hours and trading sessions for Indian markets
    """

    def __init__(self):
        # Indian timezone
        self.timezone = pytz.timezone("Asia/Kolkata")

        # Market timings (IST)
        self.market_open = dt_time(9, 15)  # 9:15 AM
        self.market_close = dt_time(15, 30)  # 3:30 PM
        self.pre_market_start = dt_time(9, 0)  # 9:00 AM
        self.post_market_end = dt_time(16, 0)  # 4:00 PM

        # Market holidays (2024-2025) - will be loaded from config in production
        self.market_holidays = {
            # 2024 holidays
            date(2024, 1, 26),  # Republic Day
            date(2024, 3, 8),  # Holi
            date(2024, 3, 29),  # Good Friday
            date(2024, 4, 17),  # Ram Navami
            date(2024, 8, 15),  # Independence Day
            date(2024, 10, 2),  # Gandhi Jayanti
            date(2024, 11, 1),  # Diwali
            date(2024, 12, 25),  # Christmas
            # 2025 holidays (partial list)
            date(2025, 1, 26),  # Republic Day
            date(2025, 8, 15),  # Independence Day
            date(2025, 10, 2),  # Gandhi Jayanti
            date(2025, 12, 25),  # Christmas
        }

        logger.info("Market hours validator initialized for Indian markets")

    def get_current_time(self) -> datetime:
        """Get current time in Indian timezone"""
        return datetime.now(self.timezone)

    def is_market_day(self, check_date: date = None) -> bool:
        """
        Check if given date is a market trading day

        Args:
            check_date: Date to check (default: today)

        Returns:
            True if market is open on the given date
        """
        if check_date is None:
            check_date = self.get_current_time().date()

        # Check if it's a weekday (Monday=0, Sunday=6)
        if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Check if it's a market holiday
        if check_date in self.market_holidays:
            return False

        return True

    def is_market_open(self, check_time: datetime = None) -> bool:
        """
        Check if market is currently open

        Args:
            check_time: Time to check (default: current time)

        Returns:
            True if market is open
        """
        if check_time is None:
            check_time = self.get_current_time()

        # Check if it's a market day
        if not self.is_market_day(check_time.date()):
            return False

        # Check if current time is within market hours
        current_time = check_time.time()
        return self.market_open <= current_time <= self.market_close

    def is_pre_market(self, check_time: datetime = None) -> bool:
        """
        Check if it's pre-market hours

        Args:
            check_time: Time to check (default: current time)

        Returns:
            True if it's pre-market hours
        """
        if check_time is None:
            check_time = self.get_current_time()

        if not self.is_market_day(check_time.date()):
            return False

        current_time = check_time.time()
        return self.pre_market_start <= current_time < self.market_open

    def is_post_market(self, check_time: datetime = None) -> bool:
        """
        Check if it's post-market hours

        Args:
            check_time: Time to check (default: current time)

        Returns:
            True if it's post-market hours
        """
        if check_time is None:
            check_time = self.get_current_time()

        if not self.is_market_day(check_time.date()):
            return False

        current_time = check_time.time()
        return self.market_close < current_time <= self.post_market_end

    def get_market_status(self, check_time: datetime = None) -> str:
        """
        Get current market status

        Args:
            check_time: Time to check (default: current time)

        Returns:
            Market status string
        """
        if check_time is None:
            check_time = self.get_current_time()

        if not self.is_market_day(check_time.date()):
            return "MARKET_CLOSED_HOLIDAY"

        if self.is_pre_market(check_time):
            return "PRE_MARKET"
        elif self.is_market_open(check_time):
            return "MARKET_OPEN"
        elif self.is_post_market(check_time):
            return "POST_MARKET"
        else:
            return "MARKET_CLOSED"

    def get_next_market_open(self, from_time: datetime = None) -> datetime:
        """
        Get the next market opening time

        Args:
            from_time: Starting time (default: current time)

        Returns:
            Next market opening datetime
        """
        if from_time is None:
            from_time = self.get_current_time()

        current_date = from_time.date()

        # If market is still open today, return today's market open
        if self.is_market_day(current_date) and from_time.time() < self.market_open:
            return self.timezone.localize(
                datetime.combine(current_date, self.market_open)
            )

        # Find next market day
        check_date = current_date
        while True:
            check_date = date.fromordinal(check_date.toordinal() + 1)
            if self.is_market_day(check_date):
                return self.timezone.localize(
                    datetime.combine(check_date, self.market_open)
                )

    def get_next_market_close(self, from_time: datetime = None) -> datetime:
        """
        Get the next market closing time

        Args:
            from_time: Starting time (default: current time)

        Returns:
            Next market closing datetime
        """
        if from_time is None:
            from_time = self.get_current_time()

        current_date = from_time.date()

        # If market is open today, return today's market close
        if self.is_market_day(current_date) and from_time.time() < self.market_close:
            return self.timezone.localize(
                datetime.combine(current_date, self.market_close)
            )

        # Find next market day
        check_date = current_date
        while True:
            check_date = date.fromordinal(check_date.toordinal() + 1)
            if self.is_market_day(check_date):
                return self.timezone.localize(
                    datetime.combine(check_date, self.market_close)
                )

    def get_trading_minutes_remaining(self, check_time: datetime = None) -> int:
        """
        Get minutes remaining in current trading session

        Args:
            check_time: Time to check (default: current time)

        Returns:
            Minutes remaining (0 if market is closed)
        """
        if check_time is None:
            check_time = self.get_current_time()

        if not self.is_market_open(check_time):
            return 0

        market_close_today = self.timezone.localize(
            datetime.combine(check_time.date(), self.market_close)
        )

        remaining = market_close_today - check_time
        return max(0, int(remaining.total_seconds() / 60))

    def get_trading_session_info(self, check_date: date = None) -> dict:
        """
        Get trading session information for a date

        Args:
            check_date: Date to check (default: today)

        Returns:
            Dictionary with session information
        """
        if check_date is None:
            check_date = self.get_current_time().date()

        session_info = {
            "date": check_date.isoformat(),
            "is_trading_day": self.is_market_day(check_date),
            "market_open": None,
            "market_close": None,
            "pre_market_start": None,
            "post_market_end": None,
        }

        if session_info["is_trading_day"]:
            session_info.update(
                {
                    "market_open": datetime.combine(
                        check_date, self.market_open
                    ).isoformat(),
                    "market_close": datetime.combine(
                        check_date, self.market_close
                    ).isoformat(),
                    "pre_market_start": datetime.combine(
                        check_date, self.pre_market_start
                    ).isoformat(),
                    "post_market_end": datetime.combine(
                        check_date, self.post_market_end
                    ).isoformat(),
                }
            )

        return session_info

    def validate_trading_time(self, target_time: datetime) -> Tuple[bool, str]:
        """
        Validate if a target time is suitable for trading

        Args:
            target_time: Time to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.is_market_day(target_time.date()):
            return False, "Market is closed (holiday/weekend)"

        if not self.is_market_open(target_time):
            status = self.get_market_status(target_time)
            return False, f"Market is not open (status: {status})"

        return True, "Valid trading time"
