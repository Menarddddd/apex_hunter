from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Load values from env file
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: SecretStr
    SECRET_KEY: SecretStr
    EXPIRE_MINUTES: int
    ALGORITHM: str = "HS256"


settings = Settings()  # type: ignore
