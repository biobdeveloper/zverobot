"""create_all

Revision ID: 362a7f6f0775
Revises:
Create Date: 2020-11-01 18:34:55.070618

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils
from src.db.models import TextType

# revision identifiers, used by Alembic.
revision = "362a7f6f0775"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("button_text", sa.Text(), nullable=True),
        sa.Column("display_on_keyboard", sa.Boolean(), default=True),
    )

    op.create_table(
        "pet_types",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("name", sa.String()),
        sa.Column("emoji", sa.String(), nullable=True),
        sa.Column("button_text", sa.String(), nullable=True),
        sa.Column("nullable_visible", sa.Boolean(), default=True),
    )

    op.create_table(
        "telegram_users",
        sa.Column("id", sa.Integer, primary_key=True, unique=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("language_code", sa.String(), nullable=True),
        sa.Column(
            "registered_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("funny_photos_subscribed", sa.Boolean(), default=False),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("pet_type_id", sa.Integer()),
        sa.Column("location_id", sa.Integer()),
        sa.Column("visible", sa.Boolean()),
        sa.Column("need_home", sa.Text(), nullable=True),
        sa.Column("need_home_visible", sa.Boolean()),
        sa.Column("need_home_allow_other_location", sa.Boolean()),
        sa.Column("need_temp", sa.Text(), nullable=True),
        sa.Column("need_temp_visible", sa.Boolean()),
        sa.Column("need_money", sa.Text(), nullable=True),
        sa.Column("need_money_visible", sa.Boolean()),
        sa.Column("need_other", sa.Text(), nullable=True),
        sa.Column("need_other_visible", sa.Boolean()),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("notifications_complete", sa.Boolean, default=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["pet_type_id"], ["pet_types.id"]),
    )

    op.create_table(
        "bot_texts",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("name", sa.String()),
        sa.Column("text_type", sa.Enum(TextType), nullable=False),
        sa.Column("value", sa.Text()),
    )

    op.create_table(
        "funny_photos",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("filename", sa_utils.UUIDType, unique=True),
        sa.Column("upload_by_id", sa.Integer, primary_key=True),
        sa.Column(
            "upload_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("approved", sa.Boolean, default=True),
        sa.Column("caption", sa.Text()),
        sa.ForeignKeyConstraint(["upload_by_id"], ["telegram_users.id"]),
    )


def downgrade():
    op.drop_table("telegram_users")
    op.drop_table("funny_photos")
    op.drop_table("posts")
    op.drop_table("pet_types")
    op.drop_table("locations")
