from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from config.settings import Settings


class BotSettings(Settings):
    token: SecretStr = Field(..., description="Токен бота")
    root_id: int = Field(..., description="ID телеграм рут пользователя")

    model_config = SettingsConfigDict(
        env_prefix="BOT_",
    )


bot_settings = BotSettings()
