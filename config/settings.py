# ==================== config/settings.py ====================
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Upstox API
    upstox_api_key: str = Field(..., env="UPSTOX_API_KEY")
    upstox_api_secret: str = Field(..., env="UPSTOX_API_SECRET") 
    upstox_redirect_uri: str = Field(..., env="UPSTOX_REDIRECT_URI")
    
    # Trading
    environment: str = Field("development", env="ENVIRONMENT")
    paper_trading: bool = Field(True, env="PAPER_TRADING")
    max_position_size: float = Field(50000, env="MAX_POSITION_SIZE")
    risk_per_trade: float = Field(0.02, env="RISK_PER_TRADE")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")
    enable_notifications: bool = Field(True, env="ENABLE_NOTIFICATIONS")
    
    # Database
    database_url: str = Field("sqlite:///./data/trading_bot.db", env="DATABASE_URL")
    
    # Backtesting
    backtest_start_date: str = Field("2024-01-01", env="BACKTEST_START_DATE")
    backtest_end_date: str = Field("2024-12-31", env="BACKTEST_END_DATE")
    backtest_initial_capital: float = Field(100000, env="BACKTEST_INITIAL_CAPITAL")
    
    # Paths
    @property
    def data_dir(self) -> Path:
        return Path("data")
    
    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"
    
    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"
    
    @property
    def backtest_dir(self) -> Path:
        return self.data_dir / "backtest"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        for dir_path in [self.data_dir, self.logs_dir, self.cache_dir, self.backtest_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()