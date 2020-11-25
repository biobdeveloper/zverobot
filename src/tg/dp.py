from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from src.tg.zverobot import ZveroBot
from src.config import Config

cfg = Config()
cfg.with_env()

storage = RedisStorage2(host="redis-local")
bot = ZveroBot(cfg)
dp = Dispatcher(bot, storage=storage)
