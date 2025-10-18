"""AI Trading Agent using xAI's Grok model."""
import logging
from typing import Dict, Any, Tuple, Optional
from enum import Enum
import re

from xai_sdk import Client

from backend.config import settings

logger = logging.getLogger(__name__)


class TradeDecision(str, Enum):
    """Possible trading decisions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class GrokTradingAgent:
    """AI Trading Agent powered by xAI's Grok model."""
    
    def __init__(self):
        """Initialize the Grok trading agent."""
        self.client = Client(api_key=settings.xai_api_key)
        self.model = "grok-4-fast"  # Using Grok 4 Fast model
    
    def _format_market_data_prompt(self, market_snapshot: Dict[str, Any]) -> str:
        """Format market data into a prompt for the AI model.
        
        Args:
            market_snapshot: Complete market data snapshot
            
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
        macd = technical.get('MACD', {})
        rsi = technical.get('RSI', {})
        
        prompt = f"""You are an expert cryptocurrency trading advisor. Analyze the following market data and technical indicators for {pair} and provide a trading decision.

**Market Data:**
- Current Price: ${price}
- 24h Volume: {volume}
- 24h High: ${high_24h}
- 24h Low: ${low_24h}
- 24h Change: {change_24h}%

**Technical Indicators:**
- MACD: {macd.get('value', 'N/A')}
- MACD Signal: {macd.get('signal', 'N/A')}
- MACD Histogram: {macd.get('histogram', 'N/A')}
- RSI: {rsi.get('value', 'N/A')}

**Instructions:**
Based on this data, decide whether to BUY, SELL, or HOLD {pair}.

Your response MUST follow this exact format:
DECISION: [BUY/SELL/HOLD]
REASONING: [Your detailed reasoning for this decision, considering the technical indicators and market conditions]

Be concise but thorough in your reasoning. Consider:
- RSI levels (oversold <30, overbought >70)
- MACD crossovers and momentum
- Price trends and volatility
- Risk management principles
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
    
    def get_trading_decision(self, market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Get a trading decision from the Grok AI model.
        
        Args:
            market_snapshot: Complete market data snapshot
            
        Returns:
            Dictionary containing decision, reasoning, and metadata
        """
        try:
            # Format the prompt
            prompt = self._format_market_data_prompt(market_snapshot)
            
            logger.info(f"Sending prompt to Grok for {market_snapshot.get('pair')}")
            
            # Call Grok API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency trading advisor. Provide clear, actionable trading decisions based on market data and technical analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            logger.info(f"Received response from Grok: {response_text[:100]}...")
            
            # Parse the response
            decision, reasoning = self._parse_grok_response(response_text)
            
            if decision is None:
                return {
                    'success': False,
                    'error': reasoning,
                    'decision': TradeDecision.HOLD,
                    'reasoning': 'Error occurred, defaulting to HOLD',
                    'raw_response': response_text
                }
            
            return {
                'success': True,
                'decision': decision,
                'reasoning': reasoning,
                'raw_response': response_text,
                'model': self.model,
                'market_data': market_snapshot
            }
            
        except Exception as e:
            logger.error(f"Error getting trading decision from Grok: {e}")
            return {
                'success': False,
                'error': str(e),
                'decision': TradeDecision.HOLD,
                'reasoning': f'Error occurred: {str(e)}. Defaulting to HOLD for safety.',
                'raw_response': None
            }

