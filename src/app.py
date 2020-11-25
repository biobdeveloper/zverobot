from aiogram.utils import executor

from src.tg.dp import dp

from src.tg.handlers.admin_handlers import *
from src.tg.handlers.base_handlers import *

executor.start_polling(dp)
