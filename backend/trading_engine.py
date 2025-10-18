"""Trading simulation engine for managing portfolio and executing trades."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from backend.config import settings
from backend.ai_agent import TradeDecision

logger = logging.getLogger(__name__)


class TradeType(str, Enum):
    """Types of trades."""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """Represents a single trade execution."""
    timestamp: str
    trade_type: TradeType
    pair: str
    price: float
    amount: float  # Amount of crypto
    usd_value: float  # USD value of trade
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return asdict(self)


@dataclass
class Portfolio:
    """Represents the current portfolio state."""
    usd_balance: float
    crypto_balance: float
    crypto_symbol: str
    total_value_usd: float
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio to dictionary."""
        return asdict(self)


class TradingSimulator:
    """Simulates cryptocurrency trading with a virtual portfolio."""
    
    def __init__(self, initial_usd: float = None, crypto_symbol: str = "BTC"):
        """Initialize the trading simulator.
        
        Args:
            initial_usd: Initial USD balance (defaults to settings value)
            crypto_symbol: Symbol of the cryptocurrency being traded
        """
        self.usd_balance = initial_usd or settings.initial_usd_balance
        self.crypto_balance = 0.0
        self.crypto_symbol = crypto_symbol
        self.trade_history: List[Trade] = []
        self.trade_percentage = settings.trade_percentage
        
        logger.info(f"Initialized trading simulator with ${self.usd_balance} USD")
    
    def get_portfolio(self, current_price: float) -> Portfolio:
        """Get current portfolio status.
        
        Args:
            current_price: Current price of the cryptocurrency
            
        Returns:
            Portfolio object with current state
        """
        crypto_value_usd = self.crypto_balance * current_price
        total_value = self.usd_balance + crypto_value_usd
        
        return Portfolio(
            usd_balance=round(self.usd_balance, 2),
            crypto_balance=round(self.crypto_balance, 8),
            crypto_symbol=self.crypto_symbol,
            total_value_usd=round(total_value, 2),
            last_updated=datetime.utcnow().isoformat()
        )
    
    def execute_buy(self, price: float, reasoning: str, pair: str) -> Optional[Trade]:
        """Execute a BUY trade.
        
        Args:
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the trade
            pair: Trading pair
            
        Returns:
            Trade object if successful, None otherwise
        """
        # Calculate amount to buy (percentage of available USD)
        usd_to_spend = self.usd_balance * self.trade_percentage
        
        if usd_to_spend < 1.0:  # Minimum $1 trade
            logger.warning(f"Insufficient USD balance for BUY: ${self.usd_balance}")
            return None
        
        # Calculate crypto amount
        crypto_amount = usd_to_spend / price
        
        # Update balances
        self.usd_balance -= usd_to_spend
        self.crypto_balance += crypto_amount
        
        # Create trade record
        trade = Trade(
            timestamp=datetime.utcnow().isoformat(),
            trade_type=TradeType.BUY,
            pair=pair,
            price=round(price, 2),
            amount=round(crypto_amount, 8),
            usd_value=round(usd_to_spend, 2),
            reasoning=reasoning
        )
        
        self.trade_history.append(trade)
        
        logger.info(f"BUY executed: {crypto_amount:.8f} {self.crypto_symbol} at ${price:.2f} (${usd_to_spend:.2f})")
        
        return trade
    
    def execute_sell(self, price: float, reasoning: str, pair: str) -> Optional[Trade]:
        """Execute a SELL trade.
        
        Args:
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the trade
            pair: Trading pair
            
        Returns:
            Trade object if successful, None otherwise
        """
        # Calculate amount to sell (percentage of available crypto)
        crypto_to_sell = self.crypto_balance * self.trade_percentage
        
        if crypto_to_sell < 0.00000001:  # Minimum crypto amount
            logger.warning(f"Insufficient crypto balance for SELL: {self.crypto_balance}")
            return None
        
        # Calculate USD value
        usd_received = crypto_to_sell * price
        
        # Update balances
        self.crypto_balance -= crypto_to_sell
        self.usd_balance += usd_received
        
        # Create trade record
        trade = Trade(
            timestamp=datetime.utcnow().isoformat(),
            trade_type=TradeType.SELL,
            pair=pair,
            price=round(price, 2),
            amount=round(crypto_to_sell, 8),
            usd_value=round(usd_received, 2),
            reasoning=reasoning
        )
        
        self.trade_history.append(trade)
        
        logger.info(f"SELL executed: {crypto_to_sell:.8f} {self.crypto_symbol} at ${price:.2f} (${usd_received:.2f})")
        
        return trade
    
    def execute_decision(self, decision: TradeDecision, price: float, reasoning: str, pair: str) -> Optional[Trade]:
        """Execute a trading decision.
        
        Args:
            decision: Trading decision (BUY/SELL/HOLD)
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the decision
            pair: Trading pair
            
        Returns:
            Trade object if trade was executed, None for HOLD or failed trades
        """
        if decision == TradeDecision.BUY:
            return self.execute_buy(price, reasoning, pair)
        elif decision == TradeDecision.SELL:
            return self.execute_sell(price, reasoning, pair)
        else:  # HOLD
            logger.info(f"HOLD decision: {reasoning}")
            return None
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        recent_trades = self.trade_history[-limit:] if len(self.trade_history) > limit else self.trade_history
        return [trade.to_dict() for trade in reversed(recent_trades)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics.
        
        Returns:
            Dictionary with trading statistics
        """
        total_trades = len(self.trade_history)
        buy_trades = sum(1 for t in self.trade_history if t.trade_type == TradeType.BUY)
        sell_trades = sum(1 for t in self.trade_history if t.trade_type == TradeType.SELL)
        
        total_bought_usd = sum(t.usd_value for t in self.trade_history if t.trade_type == TradeType.BUY)
        total_sold_usd = sum(t.usd_value for t in self.trade_history if t.trade_type == TradeType.SELL)
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_bought_usd': round(total_bought_usd, 2),
            'total_sold_usd': round(total_sold_usd, 2),
            'net_usd_flow': round(total_sold_usd - total_bought_usd, 2)
        }

