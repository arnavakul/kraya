
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Groq configuration
    GROQ_API_KEY: SecretStr
    GROQ_MODEL: str

    # Supabase configuration
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
