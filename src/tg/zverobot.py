import asyncio

from aiogram import Bot
from aiogram.types import ParseMode
from aiogram.utils.exceptions import *

from src.config import Config
from src.db.queries import (
    init_database,
    select_all_pet_types,
    select_all_locations,
    select_all_bot_texts,
    select_posts_with_filters,
)
from src.db.models import TextType

DEFAULT_PARSE_MODE = ParseMode.HTML


class ZveroBot(Bot):
    def __init__(self, config: Config, *args, **kwargs):
        kwargs["token"] = config.token
        super().__init__(*args, **kwargs)

        self.easter_egg_enabled = config.easter_egg_enabled
        self.root_id = config.root_id
        self.photo_stock_id = config.photo_stock_id
        self.pet_types = list()
        self.locations = list()
        self.texts = dict(messages={}, buttons={})

        if not kwargs.get("parse_mode"):
            self.parse_mode = DEFAULT_PARSE_MODE

        self.db = asyncio.get_event_loop().run_until_complete(
            init_database(
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_name,
            )
        )

        # TODO implement this
        # asyncio.get_event_loop().create_task(self.notify())
        asyncio.get_event_loop().run_until_complete(self._hello_msg())
        asyncio.get_event_loop().create_task(self._fetch_static_data_from_db())

    async def _hello_msg(self):
        await self.send_message(chat_id=self.root_id, text="Started")

    async def _fetch_static_data_from_db(self):
        async with self.db.acquire() as conn:
            all_pet_types = await select_all_pet_types(conn)
            self.pet_types = []
            for i in all_pet_types:
                if not i.nullable_visible:
                    c = await select_posts_with_filters(conn, pet_type=i.id)
                    if c.rowcount == 0:
                        continue
                self.pet_types.append(i)

            self.locations = await select_all_locations(conn)

            texts = await select_all_bot_texts(conn)
            for t in texts:
                if t.text_type == TextType.MESSAGE:
                    self.texts["messages"][t.name] = t.value
                if t.text_type == TextType.BUTTON:
                    self.texts["buttons"][t.name] = t.value

    async def refresh(self):
        await self._fetch_static_data_from_db()
        return self.locations, self.pet_types

    async def notify(self):
        raise NotImplementedError
        # while True:
        #     async with self.db.acquire() as conn:
        #         pass
        #     await asyncio.sleep(1)

    async def safe_send_message(
        self,
        text=None,
        chat_id=None,
        reply_markup=None,
        parse_mode=ParseMode.HTML,
        **kwargs
    ):
        try:
            msg = await self.send_message(
                text=text,
                chat_id=chat_id,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                **kwargs
            )
            return msg
        except BotBlocked:
            pass
        except UserDeactivated:
            pass
        except ChatNotFound:
            pass
        except Exception as ex:
            pass

    async def safe_delete_message(self, message_id, chat_id=None):
        if not chat_id:
            chat_id = self.root_id
        try:
            await self.delete_message(chat_id=chat_id, message_id=message_id)
        except MessageToDeleteNotFound:
            pass
        except MessageCantBeDeleted:
            pass
        except BotBlocked:
            pass
        except UserDeactivated:
            pass
        except ChatNotFound:
            pass
        except Exception as ex:
            pass

    async def safe_edit_message(
        self,
        message_id,
        text=None,
        chat_id=None,
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    ):
        if not chat_id:
            chat_id = self.root_id
        try:
            if text:
                await self.edit_message_text(
                    message_id=message_id,
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                )
            else:
                await self.edit_message_reply_markup(
                    message_id=message_id, chat_id=chat_id, reply_markup=reply_markup
                )

        except MessageCantBeEdited:
            pass
        except MessageNotModified:
            pass
        except MessageToEditNotFound:
            pass
        except BotBlocked:
            pass
        except UserDeactivated:
            pass
        except ChatNotFound:
            pass
        except Exception as ex:
            pass
