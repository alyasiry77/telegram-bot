import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Bot
    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    channel_username: str = Field(default="@your_channel", alias="CHANNEL_USERNAME")
    support_username: str = Field(default="@support", alias="SUPPORT_USERNAME")
    bot_username: str = Field(default="@your_bot", alias="BOT_USERNAME")

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./bot.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Business defaults
    daily_reward: int = Field(default=5, alias="DAILY_REWARD")
    daily_task_points: int = Field(default=10, alias="DAILY_TASK_POINTS")
    points_to_cash: float = Field(default=0.01, alias="POINTS_TO_CASH")
    min_withdrawal_balance: int = Field(default=100, alias="MIN_WITHDRAWAL_BALANCE")
    min_withdrawal_amount: float = Field(default=1.0, alias="MIN_WITHDRAWAL_AMOUNT")
    min_withdrawal_referrals: int = Field(default=3, alias="MIN_WITHDRAWAL_REFERRALS")
    referral_reward: int = Field(default=5, alias="REFERRAL_REWARD")
    campaign_profit_percent: int = Field(default=30, alias="CAMPAIGN_PROFIT_PERCENT")
    withdrawal_fee_percent: float = Field(default=0, alias="WITHDRAWAL_FEE_PERCENT")
    maintenance_mode: bool = Field(default=False, alias="MAINTENANCE_MODE")
    secret_key: str = Field(default="change_me", alias="SECRET_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @property
    def admins(self) -> List[int]:
        if not self.admin_ids:
            return []
        ids = []
        for x in self.admin_ids.replace(";", ",").split(","):
            x = x.strip()
            if x.isdigit():
                ids.append(int(x))
        return ids

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins


settings = Settings()  # type: ignore
