import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Text,
    Enum as saEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy_utils as sa_utils

Base = declarative_base()


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    # Don't use autoincrement
    # because telegram_id is unique and works good
    id = Column(Integer, primary_key=True, unique=True)

    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language_code = Column(String)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow())
    version = Column(String)

    funny_photos_subscribed = Column(Boolean, default=False)

    def __unicode__(self):
        return str(self.id)

    def __repr__(self):
        return str(self.id)


class PetType(Base):
    __tablename__ = "pet_types"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String)
    emoji = Column(Text)
    button_text = Column(Text)
    nullable_visible = Column(Boolean, default=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)

    name = Column(String)
    button_text = Column(Text)

    display_on_keyboard = Column(Boolean, default=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)

    title = Column(String)

    pet_type_id = Column(Integer, ForeignKey(PetType.id), primary_key=True)
    pet_type = relationship(PetType, remote_side=pet_type_id)

    location_id = Column(Integer, ForeignKey(Location.id), primary_key=True)
    location = relationship(Location, remote_side=location_id)

    visible = Column(Boolean, default=False)

    need_home = Column(Text)
    need_home_visible = Column(Boolean, default=False)
    need_home_allow_other_location = Column(Boolean, default=False)

    need_temp = Column(Text)
    need_temp_visible = Column(Boolean, default=False)

    need_money = Column(Text)
    need_money_visible = Column(Boolean, default=False)

    need_other = Column(Text)
    need_other_visible = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow())

    notifications_complete = Column(Boolean, default=False)


class FunnyPhoto(Base):
    __tablename__ = "funny_photos"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    filename = Column(sa_utils.UUIDType, unique=True)

    upload_by_id = Column(Integer, ForeignKey(TelegramUser.id), primary_key=True)
    upload_by = relationship("TelegramUser", foreign_keys="FunnyPhoto.upload_by_id")

    upload_at = Column(DateTime, default=datetime.datetime.utcnow())
    approved = Column(Boolean, default=True)

    caption = Column(Text, nullable=True)


class TextType(Enum):
    MESSAGE = 0
    BUTTON = 1


class BotText(Base):
    __tablename__ = "bot_texts"
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String)
    text_type = Column(saEnum(TextType))
    value = Column(Text)
