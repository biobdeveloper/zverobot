import asyncio
from os import mkdir
from datetime import datetime, timedelta

from src.config import project_root_dir
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode, hbold

from src import __version__
from src.tg.user_states import UserStates
from src.tg.dp import dp
from src.db.queries import (
    insert_telegram_user,
    select_posts_with_filters,
    select_random_funny_photo,
    update_telegram_user,
    select_telegram_user,
)
from src.utils import default_user_data, get_logger


log = get_logger("handlers")


try:
    mkdir("static")
    mkdir("static/images")
except FileExistsError:
    pass

_UPLOAD_TIME_LIMIT = 60
upload_time_limit = timedelta(seconds=_UPLOAD_TIME_LIMIT)


async def clear_user_view(message, state):
    user_data = await state.get_data()
    last_user_upload = user_data.get("last_user_upload")
    current_msg = user_data.get("msg_with_kb_id")

    if current_msg:
        await dp.bot.safe_delete_message(
            chat_id=message.from_user.id, message_id=current_msg
        )
    await state.set_data(default_user_data)

    if last_user_upload:
        await state.update_data(last_user_upload=last_user_upload)


"""Handlers automatically registered in dispatcher
so placed in the order of registration"""


@dp.message_handler(
    lambda message: message.text == dp.bot.texts["buttons"]["back_to_prev"], state="*"
)
async def back_to_prev_handler(message: types.Message, state: FSMContext):
    await clear_user_view(message, state)
    await UserStates.start.set()
    msg = dp.bot.texts["messages"]["welcome"]
    kb = start_kb()

    await dp.bot.safe_send_message(chat_id=message.chat.id, text=msg, reply_markup=kb)


@dp.message_handler(commands=["start", "restart"], state="*")
async def start_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    if not user_data:
        async with dp.bot.db.acquire() as conn:
            telegram_user = dict(message.from_user)
            telegram_user.pop("is_bot")
            telegram_user["version"] = __version__
            await insert_telegram_user(conn, **telegram_user)

    await clear_user_view(message, state)

    await UserStates.start.set()
    await dp.bot.safe_send_message(
        text=dp.bot.texts["messages"]["welcome"],
        chat_id=message.chat.id,
        reply_markup=start_kb(),
    )


@dp.message_handler(state=UserStates.start)
async def main_menu_handler(message: types.Message):
    if message.text == dp.bot.texts["buttons"]["need_home"]:
        kb = select_pet_type_kb(dp.bot.pet_types)
        msg = dp.bot.texts["messages"]["need_home"]
        await UserStates.post_view.set()

    elif message.text == dp.bot.texts["buttons"]["help"]:
        await UserStates.post_view.set()
        msg = dp.bot.texts["messages"]["help"]
        kb = help_kb()

    elif message.text == dp.bot.texts["buttons"]["volunteers"]:
        msg = dp.bot.texts["messages"]["volunteers"]
        kb = None

    elif message.text == dp.bot.texts["buttons"]["about"]:
        await UserStates.about.set()
        msg = dp.bot.texts["messages"]["about"]
        kb = about_kb()

    elif message.text == dp.bot.texts["buttons"]["easter_egg"]:
        if dp.bot.easter_egg_enabled:
            await UserStates.easter_egg.set()
            msg = dp.bot.texts["messages"]["easter_egg"]
            kb = easter_egg_kb()
        else:
            msg = dp.bot.texts["messages"]["easter_egg_disabled"]
            kb = start_kb()

    else:
        msg = dp.bot.texts["messages"]["unknown_command"]
        kb = None

    if msg:
        await dp.bot.safe_send_message(
            chat_id=message.chat.id, text=msg, reply_markup=kb
        )


@dp.message_handler(state=UserStates.about)
async def about_handler(message: types.Message):
    if message.text == dp.bot.texts["buttons"]["partners"]:
        msg = dp.bot.texts["messages"]["partners"]
        kb = None
    elif message.text == dp.bot.texts["buttons"]["project_history"]:
        msg = dp.bot.texts["messages"]["project_history"]
        kb = None
    elif message.text == dp.bot.texts["buttons"]["useful_articles"]:
        msg = dp.bot.texts["messages"]["useful_articles"]
        kb = None
    else:
        msg = dp.bot.texts["messages"]["unknown_command"]
        kb = None
    await dp.bot.safe_send_message(chat_id=message.chat.id, text=msg, reply_markup=kb)


@dp.message_handler(state=[UserStates.post_view])
async def help_choose_handler(message: types.Message, state: FSMContext):
    if message.text == dp.bot.texts["buttons"]["support_us"]:
        await dp.bot.safe_send_message(
            chat_id=message.chat.id,
            text=dp.bot.texts["messages"]["support_us"],
            reply_markup=None,
        )

    elif (
        message.text
        in [
            dp.bot.texts["buttons"]["need_money"],
            dp.bot.texts["buttons"]["need_temp"],
            dp.bot.texts["buttons"]["need_other"],
        ]
    ) or (message.text in [f"{i.emoji}{i.button_text}" for i in dp.bot.pet_types]):

        await clear_user_view(message, state)

        category = None
        pet_type = None

        if message.text == dp.bot.texts["buttons"]["need_money"]:
            category = "need_money"
        elif message.text == dp.bot.texts["buttons"]["need_temp"]:
            category = "need_temp"
        elif message.text == dp.bot.texts["buttons"]["need_other"]:
            category = "need_other"
        else:
            for _pet_type in dp.bot.pet_types:
                if _pet_type.emoji in message.text:
                    category = "need_home"
                    pet_type = _pet_type.id

        await state.update_data({"category_cache": category})
        await state.update_data({"pet_type_cache": pet_type})

        await post_view_build(message, state, category=category, pet_type=pet_type)

    else:
        await dp.bot.safe_send_message(
            chat_id=message.chat.id,
            text=dp.bot.texts["messages"]["unknown_command"],
            reply_markup=None,
        )


@dp.message_handler(state=[UserStates.filter])
async def filter_message_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    param = user_data.get("input_value_await")

    no_such_text = ""
    value = None

    if param == "location_cache":
        for i in dp.bot.locations:
            if i.button_text == message.text:
                value = i.id
                break
            if not value:
                no_such_text = dp.bot.texts["messages"]["no_such_location"].format(
                    hcode(message.text)
                )

    await dp.bot.safe_delete_message(
        chat_id=message.chat.id, message_id=message.message_id
    )

    if not value:
        msg = await dp.bot.safe_send_message(chat_id=message.chat.id, text=no_such_text)
        if msg:
            await asyncio.sleep(3)
            await dp.bot.safe_delete_message(
                chat_id=msg.chat.id, message_id=msg.message_id
            )
    else:
        await apply_filter(message, state, param, value)


@dp.callback_query_handler(
    lambda callback: callback.data in ["sub_pic", "unsub_pic"], state="*"
)
async def funny_photo_subscription_handler(callback_query: types.CallbackQuery):
    if callback_query.data == "unsub_pic":
        is_sub = False
        answer_text = dp.bot.texts["messages"]["unsubscribe_from_funny_photos"]
    elif callback_query.data == "sub_pic":
        is_sub = True
        answer_text = dp.bot.texts["messages"]["subscribe_to_funny_photos"]
    else:
        raise
    async with dp.bot.db.acquire() as conn:
        await update_telegram_user(
            conn, callback_query.from_user.id, funny_photos_subscribed=is_sub
        )
        await dp.bot.safe_edit_message(
            message_id=callback_query.message.message_id,
            chat_id=callback_query.from_user.id,
            reply_markup=funny_photo_kb(is_sub),
        )
        await dp.bot.answer_callback_query(
            callback_query_id=callback_query.id, text=answer_text, show_alert=True
        )


@dp.callback_query_handler(
    lambda callback: "_cache" in callback.data, state=[UserStates.filter]
)
async def filter_callback_handler(
    callback_query: types.CallbackQuery, state: FSMContext
):
    value_to_view = dp.bot.texts["messages"]["any"]
    param, value = callback_query.data.split(",")

    if value.isdigit():
        value = int(value)
    elif value == "any":
        value = None

    if param == "location_cache":
        if value:
            for i in dp.bot.locations:
                if i.id == value:
                    value_to_view = i.button_text
                    break
        answer_text = dp.bot.texts["messages"]["location_filter_applied"]

    elif param == "pet_type_cache":
        if value:
            for i in dp.bot.pet_types:
                if i.id == value:
                    value_to_view = i.button_text
                    break

        answer_text = dp.bot.texts["messages"]["pet_type_filter_applied"]

    else:
        raise

    await dp.bot.answer_callback_query(
        callback_query_id=callback_query.id, text=answer_text.format(value_to_view)
    )

    await apply_filter(callback_query, state, param, value)


@dp.callback_query_handler(state=UserStates.post_view)
async def post_view_callback_query_handler(
    callback_query: types.CallbackQuery, state: FSMContext
):
    try:
        # log.info(callback_query.data)
        if callback_query.data == "location_cache":
            msg = dp.bot.texts["messages"]["locations_list_header"]
            locations_by_alphavite = sorted(
                dp.bot.locations, key=lambda _location: _location.button_text
            )
            for i in locations_by_alphavite:
                msg += f"{hcode(i.button_text)}\n"
            msg += dp.bot.texts["messages"]["location_filter"]
            await state.update_data({"input_value_await": callback_query.data})

            kb = location_filter_kb(dp.bot.locations)
            await UserStates.filter.set()
            await dp.bot.safe_edit_message(
                message_id=callback_query.message.message_id,
                chat_id=callback_query.from_user.id,
                text=msg,
                reply_markup=kb,
            )

        elif callback_query.data == "pet_type_cache":
            msg = dp.bot.texts["messages"]["pet_type_filter"]
            await state.update_data({"input_value_await": callback_query.data})

            kb = pet_type_filter_kb(dp.bot.pet_types)
            await UserStates.filter.set()
            await dp.bot.safe_edit_message(
                message_id=callback_query.message.message_id,
                chat_id=callback_query.from_user.id,
                text=msg,
                reply_markup=kb,
            )
        else:
            query_data = callback_query.data.split(",")

            direction = query_data[0]
            category = query_data[1]
            location = query_data[2]
            pet_type = query_data[3]
            post_id = int(query_data[4])

            if location == "None":
                location = None
            if pet_type == "None":
                pet_type = None

            await post_view_build(
                callback_query, state, direction, category, location, pet_type, post_id
            )
    except Exception as ex:
        # Old Zverobot views processing
        await dp.bot.safe_delete_message(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
        )
        await clear_user_view(callback_query, state)
        await UserStates.start.set()
        await dp.bot.safe_send_message(
            text=dp.bot.texts["messages"]["error_on_callback"],
            chat_id=callback_query.from_user.id,
            reply_markup=start_kb(),
        )


async def apply_filter(
    user_activity: types.Message or types.CallbackQuery, state: FSMContext, param, value
):
    await state.update_data({param: value})

    user_data = await state.get_data()
    location = user_data.get("location_cache")
    pet_type = user_data.get("pet_type_cache")
    category = user_data.get("category_cache")

    await post_view_build(
        user_activity, state, category=category, location=location, pet_type=pet_type
    )
    await UserStates.post_view.set()


async def post_view_build(
    user_activity: types.Message or types.CallbackQuery,
    state: FSMContext,
    direction=None,
    category=None,
    location=None,
    pet_type=None,
    post_id=None,
):
    async def _get_neighbors():
        pagination_bts = []
        for _direction in ("<", ">"):
            user_filters["direction"] = _direction
            cursor = await select_posts_with_filters(conn, **user_filters)
            pagination_bts.append(False if cursor.rowcount == 0 else True)
        return pagination_bts

    user_filters = {"category": category}

    if post_id:
        user_filters["post_id"] = post_id

    if direction:
        user_filters["direction"] = direction

    if pet_type:
        for i in dp.bot.pet_types:
            if i.id == int(pet_type):
                pet_type_text = i.button_text
                break
    else:
        pet_type_text = dp.bot.texts["messages"]["any"]

    if location:
        for i in dp.bot.locations:
            if i.id == int(location):
                location_text = i.button_text
                break
    else:
        location_text = dp.bot.texts["messages"]["any"]

    user_filters["pet_type"] = pet_type
    user_filters["location"] = location

    async with dp.bot.db.acquire() as conn:

        post_cursor = await select_posts_with_filters(conn, **user_filters)

        if post_cursor.rowcount == 0:

            if not direction:

                if category == "need_home":
                    if location:
                        msg = dp.bot.texts["messages"][
                            "all_pets_from_location_are_at_home"
                        ].format(pet_type_text.lower(), hbold(location_text))
                    else:
                        msg = dp.bot.texts["messages"]["all_pets_are_at_home"].format(
                            pet_type_text.lower()
                        )

                else:
                    if not (location or pet_type):
                        msg = dp.bot.texts["messages"]["no_this_category"]
                    else:
                        msg = dp.bot.texts["messages"][
                            "no_this_category_filters"
                        ].format(
                            hbold(dp.bot.texts["buttons"][category]),
                            hbold(location_text),
                            hbold(pet_type_text),
                        )

                has_prev, has_next = False, False

            else:
                user_filters.pop("direction")

                # Some recursive code. Maybe change this?
                await post_view_build(user_activity, state, **user_filters)
                return

        else:
            post = await post_cursor.fetchone()
            user_filters["post_id"] = post_id = post.id
            if category == "need_home":
                if post.need_home_allow_other_location:
                    allow_other_locations = dp.bot.texts["messages"]["yes"]
                else:
                    allow_other_locations = dp.bot.texts["messages"]["no"]
                msg = dp.bot.texts["messages"]["user_post_view_need_home"].format(
                    post.pet_type_emoji,
                    post.title,
                    post.location_button_text,
                    allow_other_locations,
                    post[category],
                )
            else:
                msg = dp.bot.texts["messages"]["user_post_view"].format(
                    post.pet_type_emoji,
                    post.title,
                    post.location_button_text,
                    post[category],
                )
            has_prev, has_next = await _get_neighbors()

        kb = post_view_kb(
            category=category,
            location=location,
            pet_type=pet_type,
            post_id=post_id,
            has_prev=has_prev,
            has_next=has_next,
        )

        user_data = await state.get_data()
        current_msg = user_data.get("msg_with_kb_id")

        if current_msg:
            await dp.bot.safe_edit_message(
                message_id=current_msg,
                chat_id=user_activity.from_user.id,
                text=msg,
                reply_markup=kb,
            )

        else:
            send = await dp.bot.safe_send_message(
                chat_id=user_activity.chat.id, text=msg, reply_markup=kb
            )

            await state.update_data({"msg_with_kb_id": send.message_id})


def easter_egg_kb():
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    get_pic = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["get_pic"]
    )
    kb.row(get_pic)
    kb.row(
        types.reply_keyboard.KeyboardButton(
            text=dp.bot.texts["buttons"]["back_to_prev"]
        )
    )
    return kb


def start_kb():
    need_home_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["need_home"]
    )
    help_button = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["help"]
    )
    volunteers_button = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["volunteers"]
    )
    about_button = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["about"]
    )
    easter_egg_button = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["easter_egg"]
    )
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(need_home_bt)
    kb.row(help_button, volunteers_button)
    if dp.bot.easter_egg_enabled:
        kb.row(about_button, easter_egg_button)
    else:
        kb.row(about_button)
    return kb


def about_kb():
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    about_project_history_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["project_history"]
    )
    about_partners_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["partners"]
    )
    about_useful_articles_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["useful_articles"]
    )
    kb.row(about_project_history_bt, about_partners_bt)
    kb.row(about_useful_articles_bt)
    kb.row(
        types.reply_keyboard.KeyboardButton(
            text=dp.bot.texts["buttons"]["back_to_prev"]
        )
    )
    return kb


def help_kb():
    need_money_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["need_money"]
    )
    need_temp_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["need_temp"]
    )
    need_other_bt = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["need_other"]
    )
    support_us = types.reply_keyboard.KeyboardButton(
        text=dp.bot.texts["buttons"]["support_us"]
    )

    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(need_money_bt, need_temp_bt)
    kb.row(need_other_bt, support_us)
    kb.row(
        types.reply_keyboard.KeyboardButton(
            text=dp.bot.texts["buttons"]["back_to_prev"]
        )
    )
    return kb


def select_pet_type_kb(pet_types):
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        *[
            types.reply_keyboard.KeyboardButton(text=f"{p.emoji}{p.button_text}")
            for p in pet_types
        ]
    )
    kb.row(
        types.reply_keyboard.KeyboardButton(
            text=dp.bot.texts["buttons"]["back_to_prev"]
        )
    )
    return kb


def location_filter_kb(locations):
    kb = types.inline_keyboard.InlineKeyboardMarkup(resize_keyboard=True)
    kb.row(
        types.inline_keyboard.InlineKeyboardButton(
            text=dp.bot.texts["buttons"]["any_location"],
            callback_data="location_cache,any",
        )
    )
    for loc in locations:
        if loc.display_on_keyboard:
            kb.add(
                types.inline_keyboard.InlineKeyboardButton(
                    text=loc.button_text, callback_data=f"location_cache,{loc.id}"
                )
            )

    return kb


def pet_type_filter_kb(pet_types):
    kb = types.inline_keyboard.InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row(
        types.inline_keyboard.InlineKeyboardButton(
            text=dp.bot.texts["buttons"]["any_pet_type"],
            callback_data="pet_type_cache,any",
        )
    )

    kb.add(
        *[
            types.inline_keyboard.InlineKeyboardButton(
                text=f"{p.emoji}{p.button_text}", callback_data=f"pet_type_cache,{p.id}"
            )
            for p in pet_types
        ]
    )
    return kb


def post_view_kb(category, location, pet_type, post_id, has_prev=False, has_next=False):
    """
    Typical look of the button's callback data: <,need_home,1,1,15
    """
    kb = types.inline_keyboard.InlineKeyboardMarkup()
    if has_prev or has_next:
        prev_callback_data = f"<,{category},{location},{pet_type},{post_id}"
        next_callback_data = f">,{category},{location},{pet_type},{post_id}"

        # log.info(f"{prev_callback_data}   {next_callback_data}")

        previous_bt = types.inline_keyboard.InlineKeyboardButton(
            text=dp.bot.texts["buttons"]["previous"], callback_data=prev_callback_data
        )
        next_bt = types.inline_keyboard.InlineKeyboardButton(
            text=dp.bot.texts["buttons"]["next"], callback_data=next_callback_data
        )

        if has_prev and has_next:
            kb.row(previous_bt, next_bt)
        elif has_prev:
            kb.row(previous_bt)
        elif has_next:
            kb.row(next_bt)

    filter_by_location_bt = types.inline_keyboard.InlineKeyboardButton(
        text=dp.bot.texts["buttons"]["location_filter"], callback_data="location_cache"
    )
    filter_by_pet_type_bt = types.inline_keyboard.InlineKeyboardButton(
        text=dp.bot.texts["buttons"]["pet_type_filter"], callback_data="pet_type_cache"
    )

    if category == "need_home":
        kb.row(filter_by_location_bt)
    else:
        kb.row(filter_by_location_bt, filter_by_pet_type_bt)

    return kb


@dp.message_handler(content_types=["photo"], state=UserStates.easter_egg)
async def funny_photo_handler(message: types.Message, state: FSMContext):
    # TODO work this!!!
    last_user_upload = (await state.get_data()).get("last_user_upload")

    user_delta = datetime.utcnow() - datetime.fromtimestamp(last_user_upload)

    if user_delta < upload_time_limit:
        msg = dp.bot.texts["messages"]["upload_time_limit"].format(_UPLOAD_TIME_LIMIT)
    else:
        await state.update_data(
            {"last_user_upload": int(datetime.utcnow().timestamp())}
        )
        await message.forward(dp.bot.photo_stock_id)
        msg = dp.bot.texts["messages"]["photo_received"]
        await state.update_data(
            {"last_user_upload": int(datetime.utcnow().timestamp())}
        )

    await dp.bot.safe_send_message(chat_id=message.chat.id, text=msg)


@dp.message_handler(state=UserStates.easter_egg)
async def get_funny_photo_handler(message: types.Message):
    if message.text == dp.bot.texts["buttons"]["get_pic"]:
        async with dp.bot.db.acquire() as conn:
            photo = await select_random_funny_photo(conn)
            if photo:
                user_db_data = await select_telegram_user(conn, message.from_user.id)

                await dp.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=open(
                        f"{project_root_dir}/static/images/{photo.filename}.png", "rb"
                    ),
                    caption=photo.caption,
                    reply_markup=funny_photo_kb(user_db_data.funny_photos_subscribed),
                )
                return
            msg = dp.bot.texts["messages"]["no_funny_photo"]
    else:
        msg = dp.bot.texts["messages"]["unknown_command"]

    await dp.bot.safe_send_message(chat_id=message.chat.id, text=msg)


def funny_photo_kb(is_sub):
    kb = types.inline_keyboard.InlineKeyboardMarkup()
    if not is_sub:
        kb.row(
            types.inline_keyboard.InlineKeyboardButton(
                text=dp.bot.texts["buttons"]["sub_pic"], callback_data="sub_pic"
            )
        )
    else:
        kb.row(
            types.inline_keyboard.InlineKeyboardButton(
                text=dp.bot.texts["buttons"]["unsub_pic"], callback_data="unsub_pic"
            )
        )
    return kb
