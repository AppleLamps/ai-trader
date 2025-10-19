"""Main trading bot orchestrator."""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from backend.config import settings
from backend.data_fetcher import MarketDataAggregator
from backend.ai_agent import GrokTradingAgent, TradeDecision
from backend.trading_engine import TradingSimulator
from backend.risk_management import RiskManager

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot that orchestrates data fetching, AI decisions, and trade execution."""
    
    def __init__(self):
        """Initialize the trading bot."""
        self.market_aggregator = MarketDataAggregator()
        self.ai_agent = GrokTradingAgent()
        self.risk_manager = RiskManager(
            max_position_size=settings.trade_percentage,
            stop_loss_percentage=0.05,  # 5% stop loss
            take_profit_percentage=0.10,  # 10% take profit
            max_daily_trades=20,
            cooldown_minutes=5
        )

        # Get list of trading pairs and extract crypto symbols
        self.trading_pairs = settings.trading_pairs
        crypto_symbols = [pair.split('/')[0] for pair in self.trading_pairs]

        # Initialize single trading simulator for all cryptos
        self.trading_simulator = TradingSimulator(crypto_symbols=crypto_symbols)

        self.is_running = False
        self.last_decisions: Dict[str, Dict[str, Any]] = {}  # {pair: decision}
        self.last_market_data: Dict[str, Dict[str, Any]] = {}  # {pair: market_data}
        self.activity_log: list = []

        logger.info(f"Trading bot initialized for {len(self.trading_pairs)} pairs: {', '.join(self.trading_pairs)}")
    
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
        """Run a single trading cycle: fetch data, get AI decision, execute trade for all pairs.

        Returns:
            Dictionary with cycle results for all pairs
        """
        try:
            all_results = {}

            # Process each trading pair
            for pair in self.trading_pairs:
                pair_result = await self._process_single_pair(pair)
                all_results[pair] = pair_result

            # Get current prices for portfolio calculation
            current_prices = {}
            for pair in self.trading_pairs:
                if pair in self.last_market_data and self.last_market_data[pair]:
                    crypto_symbol = pair.split('/')[0]
                    current_prices[crypto_symbol] = self.last_market_data[pair].get('price', 0)

            # Get updated portfolio
            portfolio = self.trading_simulator.get_portfolio(current_prices)

            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'pairs': all_results,
                'portfolio': portfolio.to_dict(),
                'risk_stats': self.risk_manager.get_statistics()
            }

        except Exception as e:
            error_msg = f'Error in trading cycle: {str(e)}'
            logger.error(error_msg, exc_info=True)
            self.log_activity('ERROR', error_msg)
            return {'success': False, 'error': error_msg}

    async def _process_single_pair(self, pair: str) -> Dict[str, Any]:
        """Process a single trading pair.

        Args:
            pair: Trading pair to process

        Returns:
            Dictionary with results for this pair
        """
        try:
            # Step 1: Fetch market data with multi-timeframe analysis
            self.log_activity('DATA_FETCH', f'Fetching market data for {pair}')
            market_snapshot = self.market_aggregator.get_complete_market_snapshot(pair)

            if not market_snapshot:
                error_msg = f'Failed to fetch market data for {pair}'
                self.log_activity('ERROR', error_msg)
                return {'success': False, 'error': error_msg}

            # Get multi-timeframe analysis
            multi_timeframe = self.market_aggregator.get_multi_timeframe_analysis(pair)
            market_snapshot['multi_timeframe'] = multi_timeframe

            self.last_market_data[pair] = market_snapshot
            current_price = market_snapshot.get('price', 0)

            self.log_activity(
                'DATA_FETCH',
                f'[{pair}] Market data fetched: Price=${current_price}, Timeframes analyzed: {len(multi_timeframe)}',
                {'pair': pair, 'market_data': market_snapshot}
            )

            # Check risk management rules
            can_trade, trade_reason = self.risk_manager.can_trade()

            # Check for stop loss or take profit triggers
            if pair in self.risk_manager.open_positions:
                if self.risk_manager.should_stop_loss(pair, current_price):
                    self.log_activity('RISK_MGMT', f'[{pair}] Stop loss triggered - forcing SELL')
                    # Force sell due to stop loss
                    trade = self.trading_simulator.execute_decision(
                        decision=TradeDecision.SELL,
                        price=current_price,
                        reasoning="Stop loss triggered",
                        pair=pair
                    )
                    if trade:
                        self.risk_manager.close_position(pair, current_price, "Stop Loss")
                        self.log_activity('TRADE', f'[{pair}] Stop loss executed at ${current_price}')
                    return {'success': True, 'reason': 'stop_loss_triggered', 'trade': trade.to_dict() if trade else None}

                elif self.risk_manager.should_take_profit(pair, current_price):
                    self.log_activity('RISK_MGMT', f'[{pair}] Take profit triggered - forcing SELL')
                    # Force sell due to take profit
                    trade = self.trading_simulator.execute_decision(
                        decision=TradeDecision.SELL,
                        price=current_price,
                        reasoning="Take profit triggered",
                        pair=pair
                    )
                    if trade:
                        self.risk_manager.close_position(pair, current_price, "Take Profit")
                        self.log_activity('TRADE', f'[{pair}] Take profit executed at ${current_price}')
                    return {'success': True, 'reason': 'take_profit_triggered', 'trade': trade.to_dict() if trade else None}

            # Step 2: Get AI trading decision with performance stats
            self.log_activity('AI_DECISION', f'[{pair}] Requesting trading decision from Grok AI')

            # Get performance statistics
            trading_stats = self.trading_simulator.get_statistics()
            risk_stats = self.risk_manager.get_statistics()
            performance_stats = {**trading_stats, **risk_stats}

            ai_response = self.ai_agent.get_trading_decision(market_snapshot, performance_stats)

            if not ai_response.get('success'):
                error_msg = f"[{pair}] AI decision failed: {ai_response.get('error')}"
                self.log_activity('ERROR', error_msg)
                return {'success': False, 'error': error_msg}

            decision = ai_response['decision']
            reasoning = ai_response['reasoning']
            confidence = ai_response.get('confidence', 0.5)
            risk_level = ai_response.get('risk_level', 'MEDIUM')
            self.last_decisions[pair] = ai_response

            self.log_activity(
                'AI_DECISION',
                f'[{pair}] AI Decision: {decision} (confidence: {confidence:.2f}, risk: {risk_level}) - {reasoning[:100]}...',
                {'pair': pair, 'decision': decision, 'reasoning': reasoning, 'confidence': confidence, 'risk_level': risk_level}
            )
            
            # Step 3: Execute trade based on decision and risk management
            trade = None
            if decision != TradeDecision.HOLD:
                # Check if trading is allowed
                if not can_trade:
                    self.log_activity('RISK_MGMT', f'[{pair}] Trade blocked: {trade_reason}')
                    return {
                        'success': True,
                        'decision_made': decision,
                        'trade_executed': False,
                        'reason': trade_reason
                    }

                self.log_activity('TRADE', f'[{pair}] Executing {decision} order (confidence: {confidence:.2f})')

                # Execute trade
                trade = self.trading_simulator.execute_decision(
                    decision=decision,
                    price=current_price,
                    reasoning=reasoning,
                    pair=pair
                )

                if trade:
                    # Update risk management
                    if decision == TradeDecision.BUY:
                        self.risk_manager.open_position(
                            pair=pair,
                            entry_price=current_price,
                            amount=trade.amount
                        )
                    elif decision == TradeDecision.SELL:
                        if pair in self.risk_manager.open_positions:
                            self.risk_manager.close_position(
                                pair=pair,
                                exit_price=current_price,
                                reason="AI Decision"
                            )

                    crypto_symbol = pair.split('/')[0]
                    self.log_activity(
                        'TRADE',
                        f'[{pair}] {decision} executed: {trade.amount} {crypto_symbol} at ${trade.price}',
                        {'pair': pair, 'trade': trade.to_dict()}
                    )
                else:
                    self.log_activity('TRADE', f'[{pair}] {decision} order failed (insufficient balance)')
            else:
                self.log_activity('TRADE', f'[{pair}] HOLD - No trade executed (confidence: {confidence:.2f})')

            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'market_data': market_snapshot,
                'ai_decision': {
                    'decision': decision,
                    'reasoning': reasoning,
                    'confidence': confidence,
                    'risk_level': risk_level,
                    'key_factors': ai_response.get('key_factors', [])
                },
                'trade': trade.to_dict() if trade else None
            }

        except Exception as e:
            error_msg = f'[{pair}] Error processing pair: {str(e)}'
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
        # Get current prices for all pairs
        current_prices = {}
        for pair in self.trading_pairs:
            if pair in self.last_market_data and self.last_market_data[pair]:
                crypto_symbol = pair.split('/')[0]
                current_prices[crypto_symbol] = self.last_market_data[pair].get('price', 0)

        portfolio = self.trading_simulator.get_portfolio(current_prices)

        # Get last update timestamp (most recent across all pairs)
        last_update = None
        for pair_data in self.last_market_data.values():
            if pair_data and 'timestamp' in pair_data:
                if last_update is None or pair_data['timestamp'] > last_update:
                    last_update = pair_data['timestamp']

        # Format last decisions for each pair
        last_decisions_formatted = {}
        for pair, decision_data in self.last_decisions.items():
            last_decisions_formatted[pair] = {
                'decision': decision_data.get('decision'),
                'reasoning': decision_data.get('reasoning'),
                'confidence': decision_data.get('confidence'),
                'risk_level': decision_data.get('risk_level')
            }

        return {
            'is_running': self.is_running,
            'trading_pairs': self.trading_pairs,
            'last_update': last_update,
            'portfolio': portfolio.to_dict(),
            'last_decisions': last_decisions_formatted,
            'last_market_data': self.last_market_data,
            'statistics': self.trading_simulator.get_statistics(),
            'risk_statistics': self.risk_manager.get_statistics()
        }
    
    def get_activity_log(self, limit: int = 50) -> list:
        """Get recent activity log.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of activity log entries
        """
        return self.activity_log[-limit:] if len(self.activity_log) > limit else self.activity_log

