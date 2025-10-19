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
    crypto_balances: Dict[str, float]  # {symbol: balance}
    crypto_values_usd: Dict[str, float]  # {symbol: usd_value}
    total_value_usd: float
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert portfolio to dictionary."""
        return asdict(self)


class TradingSimulator:
    """Simulates cryptocurrency trading with a virtual portfolio."""

    def __init__(self, initial_usd: float = None, crypto_symbols: List[str] = None):
        """Initialize the trading simulator.

        Args:
            initial_usd: Initial USD balance (defaults to settings value)
            crypto_symbols: List of cryptocurrency symbols being traded (e.g., ["BTC", "DOGE", "SOL"])
        """
        self.usd_balance = initial_usd or settings.initial_usd_balance
        self.crypto_balances: Dict[str, float] = {}  # {symbol: balance}

        # Initialize balances for each crypto
        if crypto_symbols:
            for symbol in crypto_symbols:
                self.crypto_balances[symbol] = 0.0

        self.trade_history: List[Trade] = []
        self.trade_percentage = settings.trade_percentage

        logger.info(f"Initialized trading simulator with ${self.usd_balance} USD for {len(self.crypto_balances)} cryptocurrencies")
    
    def get_portfolio(self, current_prices: Dict[str, float]) -> Portfolio:
        """Get current portfolio status.

        Args:
            current_prices: Dictionary of current prices {symbol: price}

        Returns:
            Portfolio object with current state
        """
        crypto_values_usd = {}
        total_crypto_value = 0.0

        for symbol, balance in self.crypto_balances.items():
            price = current_prices.get(symbol, 0.0)
            value = balance * price
            crypto_values_usd[symbol] = round(value, 2)
            total_crypto_value += value

        total_value = self.usd_balance + total_crypto_value

        return Portfolio(
            usd_balance=round(self.usd_balance, 2),
            crypto_balances={k: round(v, 8) for k, v in self.crypto_balances.items()},
            crypto_values_usd=crypto_values_usd,
            total_value_usd=round(total_value, 2),
            last_updated=datetime.utcnow().isoformat()
        )
    
    def execute_buy(self, price: float, reasoning: str, pair: str, trade_percentage: float) -> Optional[Trade]:
        """Execute a BUY trade.

        Args:
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the trade
            pair: Trading pair (e.g., "BTC/USD")
            trade_percentage: Percentage of available balance to trade

        Returns:
            Trade object if successful, None otherwise
        """
        # Extract crypto symbol from pair
        crypto_symbol = pair.split('/')[0] if '/' in pair else pair

        # Calculate amount to buy (percentage of available USD)
        usd_to_spend = self.usd_balance * trade_percentage

        if usd_to_spend < 1.0:  # Minimum $1 trade
            logger.warning(f"Insufficient USD balance for BUY: ${self.usd_balance}")
            return None

        # Calculate crypto amount
        crypto_amount = usd_to_spend / price

        # Update balances
        self.usd_balance -= usd_to_spend
        if crypto_symbol not in self.crypto_balances:
            self.crypto_balances[crypto_symbol] = 0.0
        self.crypto_balances[crypto_symbol] += crypto_amount

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

        logger.info(f"BUY executed: {crypto_amount:.8f} {crypto_symbol} at ${price:.2f} (${usd_to_spend:.2f})")

        return trade
    
    def execute_sell(self, price: float, reasoning: str, pair: str, trade_percentage: float) -> Optional[Trade]:
        """Execute a SELL trade.

        Args:
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the trade
            pair: Trading pair (e.g., "BTC/USD")
            trade_percentage: Percentage of available balance to trade

        Returns:
            Trade object if successful, None otherwise
        """
        # Extract crypto symbol from pair
        crypto_symbol = pair.split('/')[0] if '/' in pair else pair

        # Check if we have this crypto
        if crypto_symbol not in self.crypto_balances:
            logger.warning(f"No {crypto_symbol} balance to sell")
            return None

        # Calculate amount to sell (percentage of available crypto)
        crypto_to_sell = self.crypto_balances[crypto_symbol] * trade_percentage

        if crypto_to_sell < 0.00000001:  # Minimum crypto amount
            logger.warning(f"Insufficient {crypto_symbol} balance for SELL: {self.crypto_balances[crypto_symbol]}")
            return None

        # Calculate USD value
        usd_received = crypto_to_sell * price

        # Update balances
        self.crypto_balances[crypto_symbol] -= crypto_to_sell
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

        logger.info(f"SELL executed: {crypto_to_sell:.8f} {crypto_symbol} at ${price:.2f} (${usd_received:.2f})")

        return trade
    
    def execute_decision(self, decision: TradeDecision, price: float, reasoning: str, pair: str, trade_percentage: float) -> Optional[Trade]:
        """Execute a trading decision.

        Args:
            decision: Trading decision (BUY/SELL/HOLD)
            price: Current price of the cryptocurrency
            reasoning: AI's reasoning for the decision
            pair: Trading pair
            trade_percentage: Percentage of available balance to trade

        Returns:
            Trade object if trade was executed, None for HOLD or failed trades
        """
        if decision == TradeDecision.BUY:
            return self.execute_buy(price, reasoning, pair, trade_percentage)
        elif decision == TradeDecision.SELL:
            return self.execute_sell(price, reasoning, pair, trade_percentage)
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

