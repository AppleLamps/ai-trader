"""Module for fetching cryptocurrency data from FreeCryptoAPI."""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class FreeCryptoAPIClient:
    """Client for interacting with FreeCryptoAPI."""
    
    def __init__(self):
        self.base_url = settings.freecrypto_base_url
        self.api_key = settings.freecrypto_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'accept': '*/*',
            'Authorization': f'Bearer {self.api_key}'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the FreeCryptoAPI.

        Args:
            endpoint: API endpoint (e.g., '/getData')
            params: Query parameters

        Returns:
            Response data as dictionary or None on error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None
    
    def get_crypto_list(self) -> Optional[List[str]]:
        """Fetch the list of available cryptocurrencies.
        
        Returns:
            List of cryptocurrency symbols or None on error
        """
        data = self._make_request('/getCryptoList')
        if data and 'data' in data:
            return data['data']
        return None
    
    def get_market_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetch current market data for a cryptocurrency pair.

        Args:
            pair: Trading pair (e.g., 'BTC/USD')

        Returns:
            Market data dictionary with price, volume, etc. or None on error
        """
        # Extract symbol from pair (e.g., 'BTC/USD' -> 'BTC')
        symbol = pair.split('/')[0] if '/' in pair else pair
        params = {'symbol': symbol}
        data = self._make_request('/getData', params=params)

        if data and data.get('status') == 'success' and 'symbols' in data:
            symbols = data['symbols']
            if symbols and len(symbols) > 0:
                market_data = symbols[0]
                # Normalize field names
                normalized_data = {
                    'symbol': market_data.get('symbol'),
                    'price': float(market_data.get('last', 0)),
                    'high_24h': float(market_data.get('highest', 0)),
                    'low_24h': float(market_data.get('lowest', 0)),
                    'change_24h': float(market_data.get('daily_change_percentage', 0)),
                    'timestamp': market_data.get('date', datetime.utcnow().isoformat()),
                    'source': market_data.get('source_exchange', 'unknown')
                }
                return normalized_data
        return None
    
    def get_technical_analysis(self, pair: str, indicators: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Fetch technical analysis indicators for a cryptocurrency pair.

        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            indicators: List of indicators to fetch (e.g., ['MACD', 'RSI'])
                       If None, fetches all available indicators

        Returns:
            Technical analysis data or None on error
        """
        # Extract symbol from pair (e.g., 'BTC/USD' -> 'BTC')
        symbol = pair.split('/')[0] if '/' in pair else pair
        params = {'symbol': symbol}
        if indicators:
            params['indicators'] = ','.join(indicators)

        data = self._make_request('/getTechnicalAnalysis', params=params)

        if data and 'data' in data:
            return data['data']
        return None
    
    def get_history(self, pair: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Fetch historical data for a cryptocurrency pair.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            limit: Number of historical records to fetch
            
        Returns:
            List of historical data points or None on error
        """
        params = {
            'pair': pair,
            'limit': limit
        }
        data = self._make_request('/getHistory', params=params)
        
        if data and 'data' in data:
            return data['data']
        return None
    
    def get_timeframe_data(self, pair: str, timeframe: str = '1h', limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Fetch data for a specific timeframe.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            limit: Number of records to fetch
            
        Returns:
            List of timeframe data points or None on error
        """
        params = {
            'pair': pair,
            'timeframe': timeframe,
            'limit': limit
        }
        data = self._make_request('/getTimeframe', params=params)
        
        if data and 'data' in data:
            return data['data']
        return None


class MarketDataAggregator:
    """Aggregates market data and technical indicators for AI analysis."""
    
    def __init__(self):
        self.api_client = FreeCryptoAPIClient()
    
    def get_complete_market_snapshot(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get a complete market snapshot including price and technical indicators.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Complete market snapshot or None on error
        """
        market_data = self.api_client.get_market_data(pair)
        if not market_data:
            logger.error(f"Failed to fetch market data for {pair}")
            return None
        
        # Fetch technical indicators (MACD, RSI)
        technical_data = self.api_client.get_technical_analysis(pair, indicators=['MACD', 'RSI'])
        
        snapshot = {
            'pair': pair,
            'timestamp': market_data.get('timestamp'),
            'price': market_data.get('price'),
            'volume': market_data.get('volume'),
            'high_24h': market_data.get('high_24h'),
            'low_24h': market_data.get('low_24h'),
            'change_24h': market_data.get('change_24h'),
            'technical_indicators': technical_data if technical_data else {}
        }
        
        return snapshot

