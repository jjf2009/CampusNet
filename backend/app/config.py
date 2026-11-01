from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./campusnet.db"
    radius_event_log: Path = Path("./data/radius-events.jsonl")
    radius_service_name: str = "radiusd"
    frontend_origin: str = "http://127.0.0.1:3000"
    poll_interval_seconds: float = 1.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

