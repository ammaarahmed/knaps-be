from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://ammaar:knaps@127.0.0.1/ammaar"
    node_env: str = "development"
    cors_allow_origins: str = "*"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

settings = Settings()
