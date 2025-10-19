"""Configuration management for the AI Crypto Trading Bot."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # xAI API Configuration
    xai_api_key: str = ""

    # FreeCryptoAPI Configuration
    freecrypto_api_key: str
    freecrypto_base_url: str = "https://api.freecryptoapi.com/v1"

    # Trading Configuration
    crypto_pairs: str = "BTC/USD,DOGE/USD,SOL/USD"  # Comma-separated list of trading pairs
    fetch_interval: int = 60  # seconds
    initial_usd_balance: float = 10000000.0  # $10 million starting balance
    trade_percentage: float = 0.1  # 10% of available balance per trade

    @property
    def trading_pairs(self) -> list[str]:
        """Get list of trading pairs from comma-separated string."""
        return [pair.strip() for pair in self.crypto_pairs.split(',') if pair.strip()]

    # API Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

