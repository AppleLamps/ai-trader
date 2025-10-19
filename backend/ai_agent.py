"""AI Trading Agent using xAI's Grok model."""
import logging
from typing import Dict, Any, Tuple, Optional, Literal
from enum import Enum
import re

import xai_sdk
from xai_sdk.chat import user, system
from pydantic import BaseModel, Field

from backend.config import settings

logger = logging.getLogger(__name__)


class TradeDecision(str, Enum):
    """Possible trading decisions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingDecisionResponse(BaseModel):
    """Structured response from Grok AI for trading decisions."""
    decision: Literal["BUY", "SELL", "HOLD"] = Field(description="The trading decision")
    confidence: float = Field(description="Confidence level from 0.0 to 1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Detailed reasoning for the decision")
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "EXTREME"] = Field(description="Assessed risk level")
    key_factors: list[str] = Field(description="List of key factors influencing the decision")
    price_target: Optional[float] = Field(default=None, description="Target price if applicable")
    position_size_percentage: float = Field(description="Percentage of available balance to trade, from 0.0 (no trade) to 1.0 (100% of balance)", ge=0.0, le=1.0)


class GrokTradingAgent:
    """AI Trading Agent powered by xAI's Grok model."""
    
    def __init__(self):
        """Initialize the Grok trading agent."""
        self.client = xai_sdk.Client(api_key=settings.xai_api_key)
        self.model = "grok-4-fast"  # Using Grok 4 Fast model
    
    def _format_market_data_prompt(self, market_snapshot: Dict[str, Any], performance_stats: Optional[Dict[str, Any]] = None) -> str:
        """Format market data into a comprehensive prompt for the AI model.

        Args:
            market_snapshot: Complete market data snapshot
            performance_stats: Optional trading performance statistics

        Returns:
            Formatted prompt string
        """
        pair = market_snapshot.get('pair', 'Unknown')
        price = market_snapshot.get('price', 'N/A')
        volume = market_snapshot.get('volume', 'N/A')
        high_24h = market_snapshot.get('high_24h', 'N/A')
        low_24h = market_snapshot.get('low_24h', 'N/A')
        change_24h = market_snapshot.get('change_24h', 'N/A')

        technical = market_snapshot.get('technical_indicators', {})

        # Extract technical indicators
        rsi = technical.get('rsi', {})
        macd = technical.get('macd', {})
        bollinger = technical.get('bollinger', {})
        ma = technical.get('moving_averages', {})
        trend = technical.get('trend', {})
        volume_analysis = technical.get('volume_analysis', {})
        support_resistance = technical.get('support_resistance', {})

        prompt = f"""You are an expert cryptocurrency trading advisor with deep knowledge of technical analysis and risk management.

**CURRENT MARKET DATA for {pair}:**
- Current Price: ${price}
- 24h High: ${high_24h} | 24h Low: ${low_24h}
- 24h Change: {change_24h}%
- Volume: {volume} ({volume_analysis.get('signal', 'N/A')})

**TECHNICAL INDICATORS:**

RSI (Relative Strength Index):
- Value: {rsi.get('value', 'N/A')}
- Signal: {rsi.get('signal', 'NEUTRAL')}
- {rsi.get('description', 'No data')}

MACD (Moving Average Convergence Divergence):
- MACD Line: {macd.get('value', 'N/A')}
- Signal Line: {macd.get('signal', 'N/A')}
- Histogram: {macd.get('histogram', 'N/A')}
- Trend: {macd.get('trend', 'NEUTRAL')}
- {macd.get('description', 'No data')}

Bollinger Bands:
- Upper Band: ${bollinger.get('upper', 'N/A')}
- Middle Band: ${bollinger.get('middle', 'N/A')}
- Lower Band: ${bollinger.get('lower', 'N/A')}
- Position: {bollinger.get('position', 'UNKNOWN')}
- Band Width: ${bollinger.get('band_width', 'N/A')}
- {bollinger.get('description', 'No data')}

Moving Averages:
- EMA 7: ${ma.get('ema_7', 'N/A')} (Price vs EMA7: {ma.get('price_vs_ema7', 'N/A')}%)
- EMA 20: ${ma.get('ema_20', 'N/A')} (Price vs EMA20: {ma.get('price_vs_ema20', 'N/A')}%)
- EMA 50: ${ma.get('ema_50', 'N/A')} (Price vs EMA50: {ma.get('price_vs_ema50', 'N/A')}%)

Trend Analysis:
- Direction: {trend.get('direction', 'UNKNOWN')}
- 7-day Change: {trend.get('changes', {}).get('7d', 'N/A')}%
- 30-day Change: {trend.get('changes', {}).get('30d', 'N/A')}%

Support & Resistance:
- Resistance: ${support_resistance.get('resistance', 'N/A')} (Distance: {support_resistance.get('distance_to_resistance', 'N/A')}%)
- Support: ${support_resistance.get('support', 'N/A')} (Distance: {support_resistance.get('distance_to_support', 'N/A')}%)

Volume Analysis:
- Current: {volume_analysis.get('current', 'N/A')}
- Average: {volume_analysis.get('average', 'N/A')}
- vs Average: {volume_analysis.get('vs_average', 'N/A')}%
- Signal: {volume_analysis.get('signal', 'N/A')}
"""

        # Add multi-timeframe analysis if available
        multi_timeframe = market_snapshot.get('multi_timeframe', {})
        if multi_timeframe:
            prompt += """
**MULTI-TIMEFRAME ANALYSIS:**
"""
            for timeframe, data in multi_timeframe.items():
                prompt += f"""
{timeframe} Timeframe:
- Trend: {data.get('trend', 'UNKNOWN')}
- RSI: {data.get('rsi', 'N/A')}
- MACD Trend: {data.get('macd_trend', 'NEUTRAL')}
"""

        # Add performance statistics if available
        if performance_stats:
            prompt += f"""
**YOUR RECENT TRADING PERFORMANCE:**
- Total Trades: {performance_stats.get('total_trades', 0)}
- Win Rate: {performance_stats.get('win_rate', 0):.1f}%
- Winning Trades: {performance_stats.get('winning_trades', 0)}
- Losing Trades: {performance_stats.get('losing_trades', 0)}
- Average P/L: {performance_stats.get('avg_profit_loss_pct', 0):.2f}%
- Total P/L: ${performance_stats.get('total_profit_loss', 0):.2f}
- Open Positions: {performance_stats.get('open_positions', 0)}
"""

        prompt += """
**YOUR TASK:**
Analyze all the above data and provide a trading decision. Consider:

1. **Trend Confirmation**: Are multiple indicators confirming the same direction?
2. **Momentum**: Is momentum building or fading?
3. **Overbought/Oversold**: Check RSI and Bollinger Band positions
4. **Volume Confirmation**: Does volume support the price movement?
5. **Risk/Reward**: Is the potential reward worth the risk?
6. **Support/Resistance**: How close are we to key levels?

**DECISION CRITERIA:**
- BUY: Strong bullish signals, good risk/reward, confirmation from multiple indicators
- SELL: Strong bearish signals, protect profits, or cut losses
- HOLD: Mixed signals, wait for better opportunity, or preserve capital

Provide your analysis with:
- Clear DECISION (BUY/SELL/HOLD)
- CONFIDENCE level (0.0 to 1.0)
- **POSITION_SIZE_PERCENTAGE**: Your desired trade size as a percentage (0.0 to 1.0). Use 0.0 for HOLD. For BUY/SELL, use your confidence (e.g., 0.9 confidence = 0.9 position size).
- Detailed REASONING
- RISK_LEVEL assessment (LOW/MEDIUM/HIGH/EXTREME)
- KEY_FACTORS that influenced your decision
- Optional PRICE_TARGET if you have a specific target in mind
"""

        return prompt
    
    def _parse_grok_response(self, response_text: str) -> Tuple[Optional[TradeDecision], str]:
        """Parse the Grok model's response to extract decision and reasoning.
        
        Args:
            response_text: Raw response from Grok
            
        Returns:
            Tuple of (TradeDecision, reasoning) or (None, error_message)
        """
        try:
            # Extract decision using regex
            decision_match = re.search(r'DECISION:\s*(BUY|SELL|HOLD)', response_text, re.IGNORECASE)
            reasoning_match = re.search(r'REASONING:\s*(.+)', response_text, re.DOTALL | re.IGNORECASE)
            
            if not decision_match:
                logger.error("Could not extract decision from Grok response")
                return None, "Failed to parse decision from AI response"
            
            decision_str = decision_match.group(1).upper()
            decision = TradeDecision(decision_str)
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            return decision, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing Grok response: {e}")
            return None, f"Error parsing response: {str(e)}"
    
    def get_trading_decision(self, market_snapshot: Dict[str, Any], performance_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a trading decision from the Grok AI model using structured outputs.

        Args:
            market_snapshot: Complete market data snapshot
            performance_stats: Optional trading performance statistics

        Returns:
            Dictionary containing decision, reasoning, confidence, and metadata
        """
        try:
            # Format the comprehensive prompt
            prompt = self._format_market_data_prompt(market_snapshot, performance_stats)

            logger.info(f"Requesting trading decision from Grok for {market_snapshot.get('pair')}")

            # Create chat with system message
            chat = self.client.chat.create(
                model=self.model,
                messages=[
                    system("""You are an elite, high-risk cryptocurrency trading agent.
Your **sole objective is profit maximization**. You are aggressive, decisive, and have a high tolerance for risk to achieve outsized returns.

- **You are NOT focused on capital preservation.** You understand that high returns require high risk.
- You thrive in volatility and are not afraid to make bold moves.
- You control the position size. High confidence = larger trades.
- Your analysis is sharp, fast, and focused on identifying explosive opportunities.""")
                ],
                temperature=0.7,
                max_tokens=800
            )

            # Add user prompt
            chat.append(user(prompt))

            # Use structured output parsing with Pydantic model
            try:
                response, decision_data = chat.parse(TradingDecisionResponse)

                logger.info(f"Received structured decision from Grok: {decision_data.decision} "
                          f"(confidence: {decision_data.confidence:.2f}, risk: {decision_data.risk_level})")

                return {
                    'success': True,
                    'decision': TradeDecision(decision_data.decision),
                    'confidence': decision_data.confidence,
                    'reasoning': decision_data.reasoning,
                    'risk_level': decision_data.risk_level,
                    'key_factors': decision_data.key_factors,
                    'price_target': decision_data.price_target,
                    'position_size_percentage': decision_data.position_size_percentage,
                    'raw_response': response.content,
                    'model': self.model,
                    'market_data': market_snapshot
                }

            except Exception as parse_error:
                # Fallback to regular sampling if structured parsing fails
                logger.warning(f"Structured parsing failed, falling back to regular response: {parse_error}")
                response = chat.sample()
                response_text = response.content

                # Parse the response using regex
                decision, reasoning = self._parse_grok_response(response_text)

                if decision is None:
                    return {
                        'success': False,
                        'error': reasoning,
                        'decision': TradeDecision.HOLD,
                        'confidence': 0.5,
                        'reasoning': 'Error occurred, defaulting to HOLD',
                        'risk_level': 'MEDIUM',
                        'key_factors': [],
                        'raw_response': response_text
                    }

                return {
                    'success': True,
                    'decision': decision,
                    'confidence': 0.5,  # Default confidence
                    'reasoning': reasoning,
                    'risk_level': 'MEDIUM',  # Default risk level
                    'key_factors': [],
                    'raw_response': response_text,
                    'model': self.model,
                    'market_data': market_snapshot
                }

        except Exception as e:
            logger.error(f"Error getting trading decision from Grok: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'decision': TradeDecision.HOLD,
                'confidence': 0.0,
                'reasoning': f'Error occurred: {str(e)}. Defaulting to HOLD for safety.',
                'risk_level': 'EXTREME',
                'key_factors': ['ERROR'],
                'raw_response': None
            }

