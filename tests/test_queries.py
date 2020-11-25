import pytest
from src.config import Config
from src.db.queries import *

config = Config()
config.with_env()


@pytest.mark.asyncio
async def test_engine():
    engine = await init_database(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_password,
        database=config.db_name,
    )

    assert not engine.closed


@pytest.mark.asyncio
async def test_telegram_user():
    engine = await init_database(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_password,
        database=config.db_name,
    )

    async with engine.acquire() as conn:
        test_user_data = {
            "id": 666,
            "username": "user",
            "first_name": "first name",
            "last_name": "last name",
            "language_code": "en",
        }
        await conn.execute(
            delete(TelegramUser).where(TelegramUser.id == test_user_data["id"])
        )
        insert_result = await insert_telegram_user(conn, **test_user_data)
        fail_insert_result = await insert_telegram_user(conn, **test_user_data)
        await conn.execute(
            delete(TelegramUser).where(TelegramUser.id == test_user_data["id"])
        )

        assert isinstance(insert_result, int)
        assert insert_result == 666
        assert fail_insert_result is None


@pytest.mark.asyncio
async def test_post():
    engine = await init_database(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_password,
        database=config.db_name,
    )

    async with engine.acquire() as conn:

        async def _clear():
            await conn.execute(delete(Post).where(Post.title == "Cooper"))
            await conn.execute(delete(Post).where(Post.title == "Garm"))

            await conn.execute(delete(Post).where(Post.title == "Doshik"))
            await conn.execute(delete(Post).where(Post.title == "Barsik"))

            await conn.execute(delete(Post).where(Post.title == "Alert"))

            await conn.execute(delete(Location).where(Location.name == "TestCity1"))
            await conn.execute(delete(Location).where(Location.name == "TestCity2"))

            await conn.execute(delete(PetType).where(PetType.name == "TestType1"))
            await conn.execute(delete(PetType).where(PetType.name == "TestType2"))

        await _clear()

        await conn.execute(insert(Location).values({Location.name: "TestCity1"}))
        cursor = await conn.execute(
            select([Location]).where(Location.name == "TestCity1")
        )
        location_1 = await cursor.fetchone()

        await conn.execute(insert(Location).values({Location.name: "TestCity2"}))
        cursor = await conn.execute(
            select([Location]).where(Location.name == "TestCity2")
        )
        location_2 = await cursor.fetchone()

        await conn.execute(
            insert(PetType).values(
                {
                    PetType.name: "TestType1",
                    PetType.emoji: ":)",
                    PetType.button_text: "test type 1",
                }
            )
        )
        await conn.execute(
            insert(PetType).values(
                {
                    PetType.name: "TestType2",
                    PetType.emoji: "^^",
                    PetType.button_text: "test type 2",
                }
            )
        )

        cursor = await conn.execute(
            select([PetType]).where(PetType.name == "TestType1")
        )
        pet_type_1 = await cursor.fetchone()

        cursor = await conn.execute(
            select([PetType]).where(PetType.name == "TestType2")
        )
        pet_type_2 = await cursor.fetchone()

        await conn.execute(
            insert(Post).values(
                {
                    Post.title: "Cooper",
                    Post.location_id: location_1.id,
                    Post.pet_type_id: pet_type_1.id,
                    Post.need_home: "Need_home_text_for_Cooper",
                    Post.need_home_visible: True,
                    Post.visible: True,
                }
            )
        )

        await conn.execute(
            insert(Post).values(
                {
                    Post.title: "Garm",
                    Post.location_id: location_2.id,
                    Post.pet_type_id: pet_type_1.id,
                    Post.need_home: "Need_home_text_for_Garm",
                    Post.need_home_visible: True,
                    Post.visible: True,
                }
            )
        )

        await conn.execute(
            insert(Post).values(
                {
                    Post.title: "Doshik",
                    Post.location_id: location_1.id,
                    Post.pet_type_id: pet_type_2.id,
                    Post.need_home: "Need_home_text_for_Doshik",
                    Post.need_home_visible: True,
                    Post.visible: True,
                }
            )
        )

        await conn.execute(
            insert(Post).values(
                {
                    Post.title: "Barsik",
                    Post.location_id: location_2.id,
                    Post.pet_type_id: pet_type_2.id,
                    Post.need_home: "Need_home_text_for_Barsik",
                    Post.need_home_visible: True,
                    Post.visible: True,
                }
            )
        )

        await conn.execute(
            insert(Post).values(
                {
                    Post.title: "Alert",
                    Post.location_id: location_2.id,
                    Post.pet_type_id: pet_type_2.id,
                    Post.need_money: "Need_some_money",
                    Post.visible: True,
                }
            )
        )

        posts = await select_posts_with_filters(
            conn, category="need_home", location=location_1.id, pet_type=pet_type_1.id
        )
        assert posts.rowcount == 1

        posts = await select_posts_with_filters(
            conn, category="need_home", location=location_1.id
        )
        assert posts.rowcount == 2

        posts = await select_posts_with_filters(
            conn, category="need_home", pet_type=pet_type_1.id
        )
        assert posts.rowcount == 2

        posts = await select_posts_with_filters(conn, pet_type=pet_type_2.id)
        assert posts.rowcount == 3
        posts = await select_posts_with_filters(conn, pet_type=pet_type_2.id)
        assert posts.rowcount == 3

        posts = await select_posts_with_filters(conn, category="need_temp")
        assert posts.rowcount == 0

        posts = await select_posts_with_filters(conn, category="need_home")
        assert posts.rowcount == 4
        #
        posts = await select_posts_with_filters(conn)
        assert posts.rowcount == 5
        posts = await posts.fetchall()
        central_post_id = posts[2].id
        last_post_id = posts[4].id
        first_post = posts[0].id

        first_posts_cursor = await select_posts_with_filters(
            conn, direction="<", post_id=first_post
        )
        assert first_posts_cursor.rowcount == 0
        first_posts = await first_posts_cursor.fetchmany(size=2)
        assert len(first_posts) == 0

        prev_posts_cursor = await select_posts_with_filters(
            conn, direction="<", post_id=central_post_id
        )
        prev_posts = await prev_posts_cursor.fetchmany(size=2)
        assert len(prev_posts) == 2
        assert central_post_id > prev_posts[0].id

        next_posts_cursor = await select_posts_with_filters(
            conn, direction=">", post_id=central_post_id
        )
        next_posts = await next_posts_cursor.fetchmany(size=2)
        assert len(next_posts) == 2
        assert central_post_id < next_posts[0].id

        assert prev_posts[0].id < central_post_id < next_posts[0].id

        new_post_cursor = await select_posts_with_filters(
            conn, direction=">", post_id=last_post_id
        )
        assert new_post_cursor.rowcount == 0

        new_post = await new_post_cursor.fetchmany(size=2)
        assert len(new_post) == 0

        await _clear()
