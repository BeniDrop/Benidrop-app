from pydantic import BaseModel
import os

class Foo(BaseModel):
    # Bot Configuration
    BOT_TOKEN: str
    WEBAPP_URL: str = "https://t.me/BeniDropBot"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///benidrop.db")
    
    # Project Wallet Configuration
    PROJECT_WALLET: str = os.getenv("PROJECT_WALLET", "")  
    WALLET_TAG: str = os.getenv("WALLET_TAG", "")  
    
    # Social Links
    TELEGRAM_GROUP: str = "https://t.me/benidrop"
    TELEGRAM_CHANNEL: str = "https://t.me/benidrop_announcements"
    TWITTER_PROFILE: str = "https://twitter.com/benidrop"
    DISCORD_SERVER: str = "https://discord.gg/benidrop"
    
    # Reward Configuration
    WELCOME_BONUS: int = 500  # Tokens for joining
    DAILY_CHECK_IN_REWARD: int = 100  # Daily check-in reward
    REFERRAL_REWARD: int = 5000  # Tokens for referrer
    REFERRAL_BONUS: int = 2500  # Tokens for referred user
    
    # Task Configuration
    TASK_VERIFICATION_TIMEOUT: int = 300  # 5 minutes
    MAX_DAILY_TASKS: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
