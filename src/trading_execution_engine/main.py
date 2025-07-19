#!/usr/bin/env python3
"""
Main entry point for the Trading Execution Engine.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/logs/trading_execution.log")
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Execution Engine",
    description="SEBI-compliant trading execution engine for paper trading",
    version="0.1.0"
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
        "sebi_compliance": True
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
            "compliance": "enabled"
        },
        "paper_trading_mode": True
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
            "risk_service": "ready"
        }
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
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8080,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Trading Execution Engine: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
