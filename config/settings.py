from pydantic_settings import BaseSettings, SettingsConfigDict
from config.paths import BASE_DIR

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )