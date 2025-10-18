"""FastAPI application for AI Crypto Trading Bot."""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.bot import TradingBot
from backend.data_fetcher import FreeCryptoAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global bot instance
bot: TradingBot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global bot
    # Startup
    logger.info("Starting AI Crypto Trading Bot API")
    bot = TradingBot()
    yield
    # Shutdown
    if bot and bot.is_running:
        bot.stop()
    logger.info("AI Crypto Trading Bot API shutdown")


# Create FastAPI app
app = FastAPI(
    title="AI Crypto Trading Bot",
    description="Cryptocurrency trading simulator powered by xAI Grok",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class BotControlRequest(BaseModel):
    """Request model for bot control."""
    action: str  # "start" or "stop"


class PairChangeRequest(BaseModel):
    """Request model for changing trading pair."""
    pair: str


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - serves the frontend."""
    return FileResponse("frontend/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Crypto Trading Bot",
        "version": "1.0.0"
    }


@app.get("/api/status")
async def get_status():
    """Get current bot status including portfolio and last decision."""
    try:
        status = bot.get_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio status."""
    try:
        current_price = bot.last_market_data.get('price', 0) if bot.last_market_data else 0
        portfolio = bot.trading_simulator.get_portfolio(current_price)
        
        return {
            "success": True,
            "data": portfolio.to_dict()
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-data")
async def get_market_data():
    """Get current market data."""
    try:
        if not bot.last_market_data:
            # Fetch fresh data if none exists
            market_snapshot = bot.market_aggregator.get_complete_market_snapshot(bot.current_pair)
            if market_snapshot:
                bot.last_market_data = market_snapshot
        
        return {
            "success": True,
            "data": bot.last_market_data
        }
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades")
async def get_trade_history(limit: int = 50):
    """Get trade history.
    
    Args:
        limit: Maximum number of trades to return (default: 50)
    """
    try:
        trades = bot.trading_simulator.get_trade_history(limit=limit)
        return {
            "success": True,
            "data": trades
        }
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activity-log")
async def get_activity_log(limit: int = 50):
    """Get activity log.
    
    Args:
        limit: Maximum number of entries to return (default: 50)
    """
    try:
        log = bot.get_activity_log(limit=limit)
        return {
            "success": True,
            "data": log
        }
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get trading statistics."""
    try:
        stats = bot.trading_simulator.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/control")
async def control_bot(request: BotControlRequest):
    """Start or stop the trading bot.
    
    Args:
        request: Control request with action ("start" or "stop")
    """
    try:
        if request.action == "start":
            if bot.is_running:
                return {
                    "success": False,
                    "message": "Bot is already running"
                }
            # Start bot in background
            import asyncio
            asyncio.create_task(bot.start())
            return {
                "success": True,
                "message": "Bot started successfully"
            }
        elif request.action == "stop":
            if not bot.is_running:
                return {
                    "success": False,
                    "message": "Bot is not running"
                }
            bot.stop()
            return {
                "success": True,
                "message": "Bot stopped successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")
    except Exception as e:
        logger.error(f"Error controlling bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/run-cycle")
async def run_single_cycle():
    """Run a single trading cycle manually."""
    try:
        result = await bot.run_trading_cycle()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error running trading cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crypto-list")
async def get_crypto_list():
    """Get list of available cryptocurrencies."""
    try:
        client = FreeCryptoAPIClient()
        crypto_list = client.get_crypto_list()
        
        if crypto_list is None:
            raise HTTPException(status_code=503, detail="Failed to fetch crypto list")
        
        return {
            "success": True,
            "data": crypto_list
        }
    except Exception as e:
        logger.error(f"Error getting crypto list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/change-pair")
async def change_trading_pair(request: PairChangeRequest):
    """Change the trading pair.
    
    Args:
        request: Request with new trading pair
    """
    try:
        if bot.is_running:
            return {
                "success": False,
                "message": "Cannot change pair while bot is running. Stop the bot first."
            }
        
        bot.current_pair = request.pair
        # Update crypto symbol in simulator
        crypto_symbol = request.pair.split('/')[0]
        bot.trading_simulator.crypto_symbol = crypto_symbol
        
        return {
            "success": True,
            "message": f"Trading pair changed to {request.pair}"
        }
    except Exception as e:
        logger.error(f"Error changing trading pair: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )

