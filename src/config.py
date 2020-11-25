from os import getenv, path

from dotenv import load_dotenv


project_root_dir = path.abspath("").replace("/src", "")


class Config:
    token: str
    root_id: str

    db_driver: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    redis_port: int

    easter_egg_enabled: bool = False

    photo_stock_id: int

    def __init__(self):
        load_dotenv()

    def with_env(self):

        self.token = getenv("TOKEN")
        self.root_id = getenv("ROOT_ID")

        self.db_driver = getenv("DB_DRIVER")
        self.db_host = getenv("DB_HOST")
        self.db_port = int(getenv("DB_PORT"))
        self.db_user = getenv("DB_USER")
        self.db_password = getenv("DB_PASSWORD")
        self.db_name = getenv("DB_NAME")
        self.easter_egg_enabled = bool(int(getenv("EASTER_EGG_ENABLED")))

        self.photo_stock_id = int(getenv("PHOTO_STOCK_ID"))

    def set_custom_attr(self, attr_name: str, env_param_name: str = None):
        """
        Set your own params (for example, for admin panel).

        Example of usage:
        Config().set_custom_attr('admin_host', 'ADMIN_DOMAIN')
        """

        if not env_param_name:
            env_param_name = attr_name.upper()
        value = getenv(env_param_name)
        setattr(self, attr_name, value)
