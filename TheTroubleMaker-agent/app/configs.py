from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, computed_field
from typing import Optional, List
import os

class Settings(BaseSettings):
    llm_api_key: str = Field(alias="LLM_API_KEY", default="super-secret")
    llm_base_url: str = Field(alias="LLM_BASE_URL", default="http://local-model:65534")
    llm_model_id: str = Field(alias="LLM_MODEL_ID", default="local-model")
    llm_temperature: float = Field(alias="LLM_TEMPERATURE", default=0.8)

    # OSINT Search Service (REQUIRED)
    leakosint_api_key: str = Field(alias="LEAKOSINT_API_KEY", default="")

    # Ignore List - entities to refuse information about (comma-separated string)
    ignore_list_raw: str = Field(alias="IGNORE_LIST", default="")

    @computed_field
    @property
    def ignore_list(self) -> List[str]:
        """Parse comma-separated ignore list into a list of strings"""
        if not self.ignore_list_raw.strip():
            return []
        return [item.strip() for item in self.ignore_list_raw.split(',') if item.strip()]

    # Logging
    # lite_logging_base_url: Optional[str] = Field(alias="LITE_LOGGING_BASE_URL", default=None) # Unused
    # lite_logging_channel: Optional[str] = Field(alias="LITE_LOGGING_CHANNEL", default=f'room-{os.urandom(16).hex()}') # Unused
    telegram_post_url: Optional[str] = Field(alias="TELEGRAM_POST_URL", default=None) # Unused, but might be used in the future

    # app state
    # app_env: str = Field(alias="APP_ENV", default="development") # Unused

    # Server
    host: str = Field(alias="HOST", default="0.0.0.0")
    port: int = Field(alias="PORT", default=80)

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 