import random
from aiopg.sa import SAConnection as SAConn, create_engine as create_pg_engine
from sqlalchemy.sql import insert, delete, update, select, join
import sqlalchemy as sa


from src.db.models import TelegramUser, Post, FunnyPhoto, PetType, Location, BotText
from src.utils import get_logger

log = get_logger("PostgresClient")


async def init_database(**pg_config):
    # Async engine to execute clients requests
    engine = await create_pg_engine(**pg_config)
    return engine


async def select_posts_with_filters(
    conn: SAConn,
    category=None,
    pet_type=None,
    location=None,
    post_id=None,
    direction=None,
):

    pet_type_alias = sa.alias(PetType, name="pet_type")
    location_alias = sa.alias(Location, name="location")
    j = join(Post, pet_type_alias, Post.pet_type_id == pet_type_alias.c.id).join(
        location_alias, Post.location_id == location_alias.c.id
    )

    where_clauses = Post.visible == True

    columns_to_select = [
        Post.id,
        Post.title,
        pet_type_alias.c.name.label("pet_type_name"),
        pet_type_alias.c.emoji.label("pet_type_emoji"),
        location_alias.c.name.label("location_name"),
        location_alias.c.button_text.label("location_button_text"),
    ]

    if pet_type:
        where_clauses &= pet_type_alias.c.id == pet_type

    if location:
        where_clauses &= location_alias.c.id == location

    if category == "need_home":
        columns_to_select.append(Post.need_home)
        columns_to_select.append(Post.need_home_allow_other_location)

        where_clauses &= Post.need_home != None
        where_clauses &= Post.need_home != ""
        where_clauses &= Post.need_home_visible == True

    elif category == "need_temp":
        columns_to_select.append(Post.need_temp)
        where_clauses &= Post.need_temp != None
        where_clauses &= Post.need_temp != ""
        where_clauses &= Post.need_temp_visible == True

    elif category == "need_money":
        columns_to_select.append(Post.need_money)
        where_clauses &= Post.need_money != None
        where_clauses &= Post.need_money != ""
        where_clauses &= Post.need_money_visible == True

    elif category == "need_other":
        columns_to_select.append(Post.need_other)
        where_clauses &= Post.need_other != None
        where_clauses &= Post.need_other != ""
        where_clauses &= Post.need_other_visible == True
    else:
        columns_to_select += [
            Post.need_home,
            Post.need_temp,
            Post.need_money,
            Post.need_other,
        ]

    order_by = None

    if post_id:
        if direction:
            if direction == "<":
                where_clauses &= Post.id < post_id
                order_by = Post.id.desc()
            elif direction == ">":
                where_clauses &= Post.id > post_id
                order_by = Post.id.asc()
    else:
        order_by = Post.id.asc()

    q = select(columns_to_select).select_from(j).where(where_clauses)
    q = q.order_by(order_by)

    cursor = await conn.execute(q)
    return cursor


async def insert_telegram_user(conn: SAConn, **user_data):
    try:
        await conn.execute(insert(TelegramUser).values(**user_data))
        cursor = await conn.execute(
            select([TelegramUser.id]).where(TelegramUser.id == user_data["id"])
        )
        result = await cursor.fetchone()
        return result[0]
    except Exception as ex:
        log.debug(ex)


async def select_random_funny_photo(conn: SAConn):
    try:
        cursor = await conn.execute(
            select([FunnyPhoto]).where(FunnyPhoto.approved == True).as_scalar()
        )
        if cursor.rowcount == 0:
            return
        result = await cursor.fetchall()
        return random.choice(result)
    except Exception as ex:
        log.debug(ex)


async def insert_photo(conn: SAConn, filename, user_id, caption=None):
    try:
        await conn.execute(
            insert(FunnyPhoto).values(
                {"filename": filename, "upload_by_id": user_id, "caption": caption}
            )
        )

    except Exception as ex:
        log.debug(ex)


async def select_all_locations(conn: SAConn):
    try:
        cursor = await conn.execute(select([Location]))
        result = await cursor.fetchall()
        return result
    except Exception as ex:
        log.debug(ex)


async def select_all_pet_types(conn: SAConn):
    try:
        cursor = await conn.execute(select([PetType]))
        result = await cursor.fetchall()
        return result
    except Exception as ex:
        log.debug(ex)


async def select_all_bot_texts(conn: SAConn):
    try:
        cursor = await conn.execute(select([BotText]))
        result = await cursor.fetchall()
        return result
    except Exception as ex:
        log.debug(ex)


async def select_all_telegram_users(conn: SAConn):
    try:
        cursor = await conn.execute(select([TelegramUser]))
        return cursor
    except Exception as ex:
        log.debug(ex)


async def select_telegram_user(conn: SAConn, user_id):
    try:
        cursor = await conn.execute(
            select([TelegramUser]).where(TelegramUser.id == user_id)
        )
        result = await cursor.fetchone()
        return result
    except Exception as ex:
        log.debug(ex)


async def update_telegram_user(conn, user_id, **values):
    await conn.execute(
        update(TelegramUser).values(**values).where(TelegramUser.id == user_id)
    )
