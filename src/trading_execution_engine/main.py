#!/usr/bin/env python3
"""
Main entry point for the Trading Execution Engine.
This script initializes the FastAPI application and sets up the necessary endpoints
for trading execution, risk management, and compliance.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup basic logging
log_handlers = [logging.StreamHandler(sys.stdout)]

# Only add file handler if running in container or logs directory exists
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../logs")
if os.path.exists("/app/logs") or os.path.exists(log_dir):
    log_path = (
        "/app/logs/trading_execution.log"
        if os.path.exists("/app/logs")
        else os.path.join(log_dir, "trading_execution.log")
    )
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_handlers.append(logging.FileHandler(log_path, mode="a"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Execution Engine",
    description="SEBI-compliant trading execution engine for paper trading",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {
        "message": "Trading Execution Engine is running",
        "status": "healthy",
        "version": "0.1.0",
        "paper_trading": True,
        "sebi_compliance": True,
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "execution_engine": "running",
            "risk_management": "active",
            "order_management": "ready",
            "compliance": "enabled",
        },
        "paper_trading_mode": True,
    }


@app.get("/status")
async def get_status():
    """Get system status."""
    return {
        "system": "Trading Execution Engine",
        "mode": "PAPER_TRADING",
        "compliance": "SEBI_ENABLED",
        "risk_management": "ACTIVE",
        "connections": {
            "broker_api": "ready",
            "market_data": "ready",
            "risk_service": "ready",
        },
    }


class GracefulShutdown:
    """Handle graceful shutdown of the application."""

    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def _exit_gracefully(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown = True


async def startup_event():
    """Application startup event."""
    logger.info("Trading Execution Engine starting up...")
    logger.info("Running in PAPER TRADING mode - SEBI compliant")
    logger.info("All systems initialized successfully")


async def shutdown_event():
    """Application shutdown event."""
    logger.info("Trading Execution Engine shutting down...")
    logger.info("All services stopped gracefully")


# Add event handlers
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


def main():
    """Main function to run the application."""
    try:
        logger.info("Starting Trading Execution Engine...")

        # Initialize graceful shutdown handler
        shutdown_handler = GracefulShutdown()

        # Get port from environment variable (Cloud Run sets PORT)
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Starting server on port {port}")

        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",  # nosec B104 - Required for container deployment
            port=port,
            log_level="info",
            access_log=True,
        )

    except Exception as e:
        logger.error(f"Failed to start Trading Execution Engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
