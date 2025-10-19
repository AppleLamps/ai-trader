"""Technical analysis indicators for cryptocurrency trading."""
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Calculate technical indicators from price data."""
    
    def __init__(self):
        """Initialize the technical analyzer."""
        pass
    
    def calculate_indicators(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate all technical indicators from historical price data.
        
        Args:
            price_data: List of price data dictionaries with 'timestamp', 'price', 'volume', etc.
            
        Returns:
            Dictionary containing all calculated indicators
        """
        if not price_data or len(price_data) < 20:
            logger.warning(f"Insufficient price data for technical analysis: {len(price_data) if price_data else 0} points")
            return self._get_empty_indicators()
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(price_data)
            
            # Ensure we have required columns
            if 'price' not in df.columns:
                logger.error("Price data missing 'price' column")
                return self._get_empty_indicators()
            
            # Rename columns to match pandas_ta expectations
            df = df.rename(columns={
                'price': 'close',
                'high_24h': 'high',
                'low_24h': 'low',
                'volume': 'volume'
            })
            
            # Fill missing high/low with close price if not available
            if 'high' not in df.columns:
                df['high'] = df['close']
            if 'low' not in df.columns:
                df['low'] = df['close']
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Sort by timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            # Calculate indicators
            indicators = {}
            
            # RSI (Relative Strength Index)
            indicators['rsi'] = self._calculate_rsi(df)
            
            # MACD (Moving Average Convergence Divergence)
            indicators['macd'] = self._calculate_macd(df)
            
            # Bollinger Bands
            indicators['bollinger'] = self._calculate_bollinger_bands(df)
            
            # Moving Averages
            indicators['moving_averages'] = self._calculate_moving_averages(df)
            
            # Trend Analysis
            indicators['trend'] = self._calculate_trend(df)
            
            # Volume Analysis
            indicators['volume_analysis'] = self._calculate_volume_analysis(df)
            
            # Support/Resistance Levels
            indicators['support_resistance'] = self._calculate_support_resistance(df)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}", exc_info=True)
            return self._get_empty_indicators()
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """Calculate RSI indicator."""
        try:
            rsi = ta.rsi(df['close'], length=period)
            current_rsi = float(rsi.iloc[-1]) if not rsi.empty else None
            
            if current_rsi is None:
                return {'value': None, 'signal': 'NEUTRAL', 'description': 'Insufficient data'}
            
            # Determine signal
            if current_rsi > 70:
                signal = 'OVERBOUGHT'
                description = f'RSI at {current_rsi:.1f} indicates overbought conditions'
            elif current_rsi < 30:
                signal = 'OVERSOLD'
                description = f'RSI at {current_rsi:.1f} indicates oversold conditions'
            else:
                signal = 'NEUTRAL'
                description = f'RSI at {current_rsi:.1f} is in neutral range'
            
            return {
                'value': round(current_rsi, 2),
                'signal': signal,
                'description': description,
                'overbought_threshold': 70,
                'oversold_threshold': 30
            }
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return {'value': None, 'signal': 'NEUTRAL', 'description': 'Calculation error'}
    
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MACD indicator."""
        try:
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            
            if macd is None or macd.empty:
                return {'value': None, 'signal': None, 'histogram': None, 'trend': 'NEUTRAL'}
            
            macd_line = float(macd['MACD_12_26_9'].iloc[-1])
            signal_line = float(macd['MACDs_12_26_9'].iloc[-1])
            histogram = float(macd['MACDh_12_26_9'].iloc[-1])
            
            # Determine trend
            if macd_line > signal_line and histogram > 0:
                trend = 'BULLISH'
                description = 'MACD above signal line - bullish momentum'
            elif macd_line < signal_line and histogram < 0:
                trend = 'BEARISH'
                description = 'MACD below signal line - bearish momentum'
            else:
                trend = 'NEUTRAL'
                description = 'MACD near signal line - neutral momentum'
            
            return {
                'value': round(macd_line, 4),
                'signal': round(signal_line, 4),
                'histogram': round(histogram, 4),
                'trend': trend,
                'description': description
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'value': None, 'signal': None, 'histogram': None, 'trend': 'NEUTRAL'}
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: int = 2) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        try:
            bbands = ta.bbands(df['close'], length=period, std=std)

            if bbands is None or bbands.empty:
                return {'upper': None, 'middle': None, 'lower': None, 'position': 'UNKNOWN'}

            # Get column names (they vary by pandas-ta version)
            cols = bbands.columns.tolist()
            upper_col = [c for c in cols if 'BBU' in c][0] if any('BBU' in c for c in cols) else None
            middle_col = [c for c in cols if 'BBM' in c][0] if any('BBM' in c for c in cols) else None
            lower_col = [c for c in cols if 'BBL' in c][0] if any('BBL' in c for c in cols) else None

            if not all([upper_col, middle_col, lower_col]):
                return {'upper': None, 'middle': None, 'lower': None, 'position': 'UNKNOWN'}

            upper = float(bbands[upper_col].iloc[-1])
            middle = float(bbands[middle_col].iloc[-1])
            lower = float(bbands[lower_col].iloc[-1])
            current_price = float(df['close'].iloc[-1])
            
            # Determine position
            band_width = upper - lower
            if current_price > upper:
                position = 'ABOVE_UPPER'
                description = f'Price ${current_price:.2f} above upper band ${upper:.2f} - potential reversal'
            elif current_price < lower:
                position = 'BELOW_LOWER'
                description = f'Price ${current_price:.2f} below lower band ${lower:.2f} - potential bounce'
            elif current_price > middle:
                position = 'UPPER_HALF'
                description = f'Price in upper half of bands - bullish'
            else:
                position = 'LOWER_HALF'
                description = f'Price in lower half of bands - bearish'
            
            return {
                'upper': round(upper, 2),
                'middle': round(middle, 2),
                'lower': round(lower, 2),
                'position': position,
                'band_width': round(band_width, 2),
                'description': description
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'upper': None, 'middle': None, 'lower': None, 'position': 'UNKNOWN'}
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate various moving averages."""
        try:
            current_price = float(df['close'].iloc[-1])
            
            # Calculate EMAs
            ema_7 = ta.ema(df['close'], length=7)
            ema_20 = ta.ema(df['close'], length=20)
            ema_50 = ta.ema(df['close'], length=50) if len(df) >= 50 else None
            
            result = {
                'ema_7': round(float(ema_7.iloc[-1]), 2) if ema_7 is not None and not ema_7.empty else None,
                'ema_20': round(float(ema_20.iloc[-1]), 2) if ema_20 is not None and not ema_20.empty else None,
                'ema_50': round(float(ema_50.iloc[-1]), 2) if ema_50 is not None and not ema_50.empty else None,
                'current_price': round(current_price, 2)
            }
            
            # Calculate price vs MA percentages
            if result['ema_7']:
                result['price_vs_ema7'] = round(((current_price - result['ema_7']) / result['ema_7']) * 100, 2)
            if result['ema_20']:
                result['price_vs_ema20'] = round(((current_price - result['ema_20']) / result['ema_20']) * 100, 2)
            if result['ema_50']:
                result['price_vs_ema50'] = round(((current_price - result['ema_50']) / result['ema_50']) * 100, 2)
            
            return result
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return {}
    
    def _calculate_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend."""
        try:
            current_price = float(df['close'].iloc[-1])
            
            # Calculate price changes over different periods
            changes = {}
            if len(df) >= 7:
                price_7d_ago = float(df['close'].iloc[-7])
                changes['7d'] = round(((current_price - price_7d_ago) / price_7d_ago) * 100, 2)
            
            if len(df) >= 30:
                price_30d_ago = float(df['close'].iloc[-30])
                changes['30d'] = round(((current_price - price_30d_ago) / price_30d_ago) * 100, 2)
            
            # Determine overall trend
            if '7d' in changes:
                if changes['7d'] > 5:
                    trend = 'STRONG_UPTREND'
                elif changes['7d'] > 2:
                    trend = 'UPTREND'
                elif changes['7d'] < -5:
                    trend = 'STRONG_DOWNTREND'
                elif changes['7d'] < -2:
                    trend = 'DOWNTREND'
                else:
                    trend = 'SIDEWAYS'
            else:
                trend = 'UNKNOWN'
            
            return {
                'direction': trend,
                'changes': changes,
                'current_price': round(current_price, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {'direction': 'UNKNOWN', 'changes': {}}
    
    def _calculate_volume_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns."""
        try:
            if 'volume' not in df.columns or df['volume'].sum() == 0:
                return {'current': 0, 'average': 0, 'vs_average': 0, 'signal': 'NO_DATA'}
            
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume'].tail(20).mean())
            
            if avg_volume > 0:
                vs_average = round(((current_volume - avg_volume) / avg_volume) * 100, 2)
            else:
                vs_average = 0
            
            # Determine signal
            if vs_average > 50:
                signal = 'HIGH_VOLUME'
            elif vs_average < -50:
                signal = 'LOW_VOLUME'
            else:
                signal = 'NORMAL_VOLUME'
            
            return {
                'current': round(current_volume, 2),
                'average': round(avg_volume, 2),
                'vs_average': vs_average,
                'signal': signal
            }
        except Exception as e:
            logger.error(f"Error calculating volume analysis: {e}")
            return {'current': 0, 'average': 0, 'vs_average': 0, 'signal': 'ERROR'}
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        try:
            # Use recent highs and lows
            recent_high = float(df['high'].tail(20).max())
            recent_low = float(df['low'].tail(20).min())
            current_price = float(df['close'].iloc[-1])
            
            return {
                'resistance': round(recent_high, 2),
                'support': round(recent_low, 2),
                'current_price': round(current_price, 2),
                'distance_to_resistance': round(((recent_high - current_price) / current_price) * 100, 2),
                'distance_to_support': round(((current_price - recent_low) / current_price) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}
    
    def _get_empty_indicators(self) -> Dict[str, Any]:
        """Return empty indicators structure."""
        return {
            'rsi': {'value': None, 'signal': 'NEUTRAL'},
            'macd': {'value': None, 'signal': None, 'histogram': None, 'trend': 'NEUTRAL'},
            'bollinger': {'upper': None, 'middle': None, 'lower': None, 'position': 'UNKNOWN'},
            'moving_averages': {},
            'trend': {'direction': 'UNKNOWN', 'changes': {}},
            'volume_analysis': {'current': 0, 'average': 0, 'vs_average': 0, 'signal': 'NO_DATA'},
            'support_resistance': {}
        }

