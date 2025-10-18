"""Main trading bot orchestrator."""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from backend.config import settings
from backend.data_fetcher import MarketDataAggregator
from backend.ai_agent import GrokTradingAgent, TradeDecision
from backend.trading_engine import TradingSimulator

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot that orchestrates data fetching, AI decisions, and trade execution."""
    
    def __init__(self):
        """Initialize the trading bot."""
        self.market_aggregator = MarketDataAggregator()
        self.ai_agent = GrokTradingAgent()
        
        # Extract crypto symbol from pair (e.g., "BTC/USD" -> "BTC")
        crypto_symbol = settings.crypto_pair.split('/')[0]
        self.trading_simulator = TradingSimulator(crypto_symbol=crypto_symbol)
        
        self.current_pair = settings.crypto_pair
        self.is_running = False
        self.last_decision: Optional[Dict[str, Any]] = None
        self.last_market_data: Optional[Dict[str, Any]] = None
        self.activity_log: list = []
        
        logger.info(f"Trading bot initialized for {self.current_pair}")
    
    def log_activity(self, activity_type: str, message: str, data: Optional[Dict] = None):
        """Log bot activity.
        
        Args:
            activity_type: Type of activity (e.g., 'DATA_FETCH', 'AI_DECISION', 'TRADE')
            message: Activity message
            data: Additional data to log
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': activity_type,
            'message': message,
            'data': data or {}
        }
        self.activity_log.append(log_entry)
        
        # Keep only last 100 entries
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]
        
        logger.info(f"[{activity_type}] {message}")
    
    async def run_trading_cycle(self) -> Dict[str, Any]:
        """Run a single trading cycle: fetch data, get AI decision, execute trade.
        
        Returns:
            Dictionary with cycle results
        """
        try:
            # Step 1: Fetch market data
            self.log_activity('DATA_FETCH', f'Fetching market data for {self.current_pair}')
            market_snapshot = self.market_aggregator.get_complete_market_snapshot(self.current_pair)
            
            if not market_snapshot:
                error_msg = f'Failed to fetch market data for {self.current_pair}'
                self.log_activity('ERROR', error_msg)
                return {'success': False, 'error': error_msg}
            
            self.last_market_data = market_snapshot
            current_price = market_snapshot.get('price', 0)
            
            self.log_activity(
                'DATA_FETCH',
                f'Market data fetched: Price=${current_price}',
                {'market_data': market_snapshot}
            )
            
            # Step 2: Get AI trading decision
            self.log_activity('AI_DECISION', 'Requesting trading decision from Grok AI')
            ai_response = self.ai_agent.get_trading_decision(market_snapshot)
            
            if not ai_response.get('success'):
                error_msg = f"AI decision failed: {ai_response.get('error')}"
                self.log_activity('ERROR', error_msg)
                return {'success': False, 'error': error_msg}
            
            decision = ai_response['decision']
            reasoning = ai_response['reasoning']
            self.last_decision = ai_response
            
            self.log_activity(
                'AI_DECISION',
                f'AI Decision: {decision} - {reasoning[:100]}...',
                {'decision': decision, 'reasoning': reasoning}
            )
            
            # Step 3: Execute trade based on decision
            trade = None
            if decision != TradeDecision.HOLD:
                self.log_activity('TRADE', f'Executing {decision} order')
                trade = self.trading_simulator.execute_decision(
                    decision=decision,
                    price=current_price,
                    reasoning=reasoning,
                    pair=self.current_pair
                )
                
                if trade:
                    self.log_activity(
                        'TRADE',
                        f'{decision} executed: {trade.amount} {self.trading_simulator.crypto_symbol} at ${trade.price}',
                        {'trade': trade.to_dict()}
                    )
                else:
                    self.log_activity('TRADE', f'{decision} order failed (insufficient balance)')
            else:
                self.log_activity('TRADE', f'HOLD - No trade executed')
            
            # Get updated portfolio
            portfolio = self.trading_simulator.get_portfolio(current_price)
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'market_data': market_snapshot,
                'ai_decision': {
                    'decision': decision,
                    'reasoning': reasoning
                },
                'trade': trade.to_dict() if trade else None,
                'portfolio': portfolio.to_dict()
            }
            
        except Exception as e:
            error_msg = f'Error in trading cycle: {str(e)}'
            logger.error(error_msg, exc_info=True)
            self.log_activity('ERROR', error_msg)
            return {'success': False, 'error': error_msg}
    
    async def start(self):
        """Start the automated trading bot."""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        self.is_running = True
        self.log_activity('BOT_STATUS', 'Trading bot started')
        
        logger.info(f"Starting trading bot with {settings.fetch_interval}s interval")
        
        while self.is_running:
            try:
                await self.run_trading_cycle()
                await asyncio.sleep(settings.fetch_interval)
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                await asyncio.sleep(settings.fetch_interval)
    
    def stop(self):
        """Stop the automated trading bot."""
        if not self.is_running:
            logger.warning("Bot is not running")
            return
        
        self.is_running = False
        self.log_activity('BOT_STATUS', 'Trading bot stopped')
        logger.info("Trading bot stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status.
        
        Returns:
            Dictionary with bot status information
        """
        current_price = self.last_market_data.get('price', 0) if self.last_market_data else 0
        portfolio = self.trading_simulator.get_portfolio(current_price)
        
        return {
            'is_running': self.is_running,
            'current_pair': self.current_pair,
            'last_update': self.last_market_data.get('timestamp') if self.last_market_data else None,
            'portfolio': portfolio.to_dict(),
            'last_decision': {
                'decision': self.last_decision.get('decision') if self.last_decision else None,
                'reasoning': self.last_decision.get('reasoning') if self.last_decision else None
            } if self.last_decision else None,
            'statistics': self.trading_simulator.get_statistics()
        }
    
    def get_activity_log(self, limit: int = 50) -> list:
        """Get recent activity log.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of activity log entries
        """
        return self.activity_log[-limit:] if len(self.activity_log) > limit else self.activity_log

