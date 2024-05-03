from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    
    app_name: str = "Germinate AI"
    summary: str = "Germinate - Platform for Distributed LLM based Multi-Agent Systems"

    api_prefix: str = "/api/v1"

    database_url: str
    nats_url: str

    nats_jetstream_name: str = "germinate"

    google_ai_api_key: str


settings = Settings()
