from tortoise import Tortoise

from core.config import Config

config = Config()
await Tortoise.init(
    db_url=str(config.DATABASE_URL()),
    modules={'models': ['models_tortoise.NotCheckedHuman', 'models_tortoise.FSSPHuman']}
)

