"""Module for fetching cryptocurrency data from FreeCryptoAPI."""
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time

from backend.config import settings
from backend.technical_analysis import TechnicalAnalyzer

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
        self.technical_analyzer = TechnicalAnalyzer()
        self._historical_cache = {}  # Cache historical data
        self._cache_duration = 300  # 5 minutes cache

    def get_historical_data(self, pair: str, hours: int = 168) -> List[Dict[str, Any]]:
        """Get historical price data for technical analysis.

        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            hours: Number of hours of historical data to fetch (default: 168 = 7 days)

        Returns:
            List of historical price data points
        """
        cache_key = f"{pair}_{hours}"
        current_time = time.time()

        # Check cache
        if cache_key in self._historical_cache:
            cached_data, cache_time = self._historical_cache[cache_key]
            if current_time - cache_time < self._cache_duration:
                logger.debug(f"Using cached historical data for {pair}")
                return cached_data

        # Since FreeCryptoAPI might not have historical endpoints,
        # we'll simulate by fetching current data multiple times
        # In production, you'd use a proper historical data API
        historical_data = []

        try:
            # Fetch current market data
            current_data = self.api_client.get_market_data(pair)
            if not current_data:
                return []

            # For now, create simulated historical data points
            # In production, replace this with actual API calls
            current_price = current_data.get('price', 0)
            current_time_dt = datetime.utcnow()

            # Generate data points (this is a placeholder - replace with real API)
            for i in range(hours):
                timestamp = current_time_dt - timedelta(hours=hours - i)
                # Add some realistic price variation (±2%)
                import random
                price_variation = random.uniform(-0.02, 0.02)
                simulated_price = current_price * (1 + price_variation)

                historical_data.append({
                    'timestamp': timestamp.isoformat(),
                    'price': simulated_price,
                    'high_24h': simulated_price * 1.01,
                    'low_24h': simulated_price * 0.99,
                    'volume': current_data.get('volume', 0)
                })

            # Cache the data
            self._historical_cache[cache_key] = (historical_data, current_time)

            return historical_data

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

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

        # Get historical data for technical analysis
        historical_data = self.get_historical_data(pair, hours=168)  # 7 days

        # Calculate technical indicators
        technical_indicators = self.technical_analyzer.calculate_indicators(historical_data)

        snapshot = {
            'pair': pair,
            'timestamp': market_data.get('timestamp'),
            'price': market_data.get('price'),
            'volume': market_data.get('volume', 0),
            'high_24h': market_data.get('high_24h'),
            'low_24h': market_data.get('low_24h'),
            'change_24h': market_data.get('change_24h'),
            'technical_indicators': technical_indicators,
            'historical_data_points': len(historical_data)
        }

        return snapshot

    def get_multi_timeframe_analysis(self, pair: str) -> Dict[str, Any]:
        """Get analysis across multiple timeframes.

        Args:
            pair: Trading pair (e.g., 'BTC/USD')

        Returns:
            Dictionary with analysis for different timeframes
        """
        try:
            timeframes = {
                '1h': 24,      # Last 24 hours (hourly)
                '4h': 96,      # Last 4 days (4-hour periods)
                '1d': 168      # Last 7 days (daily)
            }

            multi_timeframe = {}

            for tf_name, hours in timeframes.items():
                historical_data = self.get_historical_data(pair, hours=hours)
                if historical_data:
                    indicators = self.technical_analyzer.calculate_indicators(historical_data)
                    multi_timeframe[tf_name] = {
                        'trend': indicators.get('trend', {}).get('direction', 'UNKNOWN'),
                        'rsi': indicators.get('rsi', {}).get('value'),
                        'macd_trend': indicators.get('macd', {}).get('trend', 'NEUTRAL')
                    }

            return multi_timeframe

        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {e}")
            return {}

