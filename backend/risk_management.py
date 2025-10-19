"""Risk management module for trading bot."""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for trades."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass
class Position:
    """Represents an open trading position."""
    entry_price: float
    amount: float
    timestamp: str
    pair: str
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


class RiskManager:
    """Manages trading risk and position limits."""
    
    def __init__(self,
                 max_position_size: float = 0.1,  # Max 10% per trade
                 stop_loss_percentage: float = 0.30,  # 30% catastrophic stop loss
                 take_profit_percentage: float = 10.0,  # 1000% take profit (effectively disabled)
                 max_daily_trades: int = 500,
                 cooldown_minutes: int = 0):
        """Initialize risk manager.
        
        Args:
            max_position_size: Maximum position size as fraction of portfolio (0.1 = 10%)
            stop_loss_percentage: Stop loss percentage (0.05 = 5%)
            take_profit_percentage: Take profit percentage (0.10 = 10%)
            max_daily_trades: Maximum number of trades per day
            cooldown_minutes: Minimum minutes between trades
        """
        self.max_position_size = max_position_size
        self.stop_loss_percentage = stop_loss_percentage
        self.take_profit_percentage = take_profit_percentage
        self.max_daily_trades = max_daily_trades
        self.cooldown_minutes = cooldown_minutes
        
        self.open_positions: Dict[str, Position] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.last_trade_time: Optional[datetime] = None
        
        logger.info(f"Risk manager initialized: max_position={max_position_size*100}%, "
                   f"stop_loss={stop_loss_percentage*100}%, take_profit={take_profit_percentage*100}%")
    
    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed based on risk rules.
        
        Returns:
            Tuple of (can_trade: bool, reason: str)
        """
        # Check cooldown period
        if self.last_trade_time:
            time_since_last_trade = datetime.utcnow() - self.last_trade_time
            if time_since_last_trade < timedelta(minutes=self.cooldown_minutes):
                remaining = self.cooldown_minutes - (time_since_last_trade.seconds // 60)
                return False, f"Cooldown period: {remaining} minutes remaining"
        
        # Check daily trade limit
        today = datetime.utcnow().date()
        today_trades = [t for t in self.trade_history 
                       if datetime.fromisoformat(t['timestamp']).date() == today]
        
        if len(today_trades) >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades} trades)"
        
        return True, "Trading allowed"
    
    def calculate_position_size(self, 
                                available_balance: float, 
                                current_price: float,
                                confidence: float = 0.5) -> float:
        """Calculate appropriate position size based on risk parameters.
        
        Args:
            available_balance: Available USD balance
            current_price: Current asset price
            confidence: AI confidence level (0.0 to 1.0)
            
        Returns:
            Position size in USD
        """
        # Base position size
        base_size = available_balance * self.max_position_size
        
        # Adjust based on confidence (50% to 100% of base size)
        confidence_multiplier = 0.5 + (confidence * 0.5)
        adjusted_size = base_size * confidence_multiplier
        
        return min(adjusted_size, available_balance)
    
    def calculate_stop_loss(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate stop loss price.
        
        Args:
            entry_price: Entry price of the position
            is_long: True for long position, False for short
            
        Returns:
            Stop loss price
        """
        if is_long:
            return entry_price * (1 - self.stop_loss_percentage)
        else:
            return entry_price * (1 + self.stop_loss_percentage)
    
    def calculate_take_profit(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate take profit price.
        
        Args:
            entry_price: Entry price of the position
            is_long: True for long position, False for short
            
        Returns:
            Take profit price
        """
        if is_long:
            return entry_price * (1 + self.take_profit_percentage)
        else:
            return entry_price * (1 - self.take_profit_percentage)
    
    def should_stop_loss(self, pair: str, current_price: float) -> bool:
        """Check if stop loss should be triggered.
        
        Args:
            pair: Trading pair
            current_price: Current market price
            
        Returns:
            True if stop loss should be triggered
        """
        if pair not in self.open_positions:
            return False
        
        position = self.open_positions[pair]
        if position.stop_loss_price is None:
            return False
        
        # Trigger stop loss if price drops below stop loss level
        if current_price <= position.stop_loss_price:
            logger.warning(f"Stop loss triggered for {pair}: "
                         f"current=${current_price:.2f}, stop_loss=${position.stop_loss_price:.2f}")
            return True
        
        return False
    
    def should_take_profit(self, pair: str, current_price: float) -> bool:
        """Check if take profit should be triggered.
        
        Args:
            pair: Trading pair
            current_price: Current market price
            
        Returns:
            True if take profit should be triggered
        """
        if pair not in self.open_positions:
            return False
        
        position = self.open_positions[pair]
        if position.take_profit_price is None:
            return False
        
        # Trigger take profit if price rises above take profit level
        if current_price >= position.take_profit_price:
            logger.info(f"Take profit triggered for {pair}: "
                       f"current=${current_price:.2f}, take_profit=${position.take_profit_price:.2f}")
            return True
        
        return False
    
    def open_position(self, pair: str, entry_price: float, amount: float):
        """Record opening a new position.
        
        Args:
            pair: Trading pair
            entry_price: Entry price
            amount: Amount of crypto purchased
        """
        stop_loss = self.calculate_stop_loss(entry_price, is_long=True)
        take_profit = self.calculate_take_profit(entry_price, is_long=True)
        
        position = Position(
            entry_price=entry_price,
            amount=amount,
            timestamp=datetime.utcnow().isoformat(),
            pair=pair,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit
        )
        
        self.open_positions[pair] = position
        self.last_trade_time = datetime.utcnow()
        
        logger.info(f"Opened position for {pair}: entry=${entry_price:.2f}, "
                   f"stop_loss=${stop_loss:.2f}, take_profit=${take_profit:.2f}")
    
    def close_position(self, pair: str, exit_price: float, reason: str = "Manual"):
        """Record closing a position.
        
        Args:
            pair: Trading pair
            exit_price: Exit price
            reason: Reason for closing (e.g., "Stop Loss", "Take Profit", "Manual")
        """
        if pair not in self.open_positions:
            logger.warning(f"Attempted to close non-existent position for {pair}")
            return
        
        position = self.open_positions[pair]
        profit_loss = (exit_price - position.entry_price) * position.amount
        profit_loss_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
        
        trade_record = {
            'pair': pair,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'amount': position.amount,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'duration': (datetime.utcnow() - datetime.fromisoformat(position.timestamp)).total_seconds()
        }
        
        self.trade_history.append(trade_record)
        del self.open_positions[pair]
        self.last_trade_time = datetime.utcnow()
        
        logger.info(f"Closed position for {pair}: exit=${exit_price:.2f}, "
                   f"P/L={profit_loss_pct:.2f}%, reason={reason}")
    
    def assess_risk_level(self, 
                         volatility: float,
                         rsi: Optional[float],
                         trend_strength: str) -> RiskLevel:
        """Assess the risk level of a potential trade.
        
        Args:
            volatility: Market volatility (e.g., Bollinger Band width)
            rsi: RSI value
            trend_strength: Trend strength (e.g., "STRONG_UPTREND", "SIDEWAYS")
            
        Returns:
            Risk level assessment
        """
        risk_score = 0
        
        # Volatility risk
        if volatility > 1000:
            risk_score += 3
        elif volatility > 500:
            risk_score += 2
        elif volatility > 200:
            risk_score += 1
        
        # RSI risk (extreme values are risky)
        if rsi is not None:
            if rsi > 80 or rsi < 20:
                risk_score += 3
            elif rsi > 70 or rsi < 30:
                risk_score += 2
        
        # Trend risk (sideways is riskier)
        if trend_strength in ['SIDEWAYS', 'UNKNOWN']:
            risk_score += 2
        elif trend_strength in ['STRONG_DOWNTREND']:
            risk_score += 3
        
        # Determine risk level
        if risk_score >= 6:
            return RiskLevel.EXTREME
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get risk management statistics.
        
        Returns:
            Dictionary with risk statistics
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit_loss_pct': 0,
                'total_profit_loss': 0
            }
        
        winning_trades = [t for t in self.trade_history if t['profit_loss'] > 0]
        losing_trades = [t for t in self.trade_history if t['profit_loss'] < 0]
        
        return {
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.trade_history)) * 100 if self.trade_history else 0,
            'avg_profit_loss_pct': sum(t['profit_loss_pct'] for t in self.trade_history) / len(self.trade_history),
            'total_profit_loss': sum(t['profit_loss'] for t in self.trade_history),
            'open_positions': len(self.open_positions)
        }

