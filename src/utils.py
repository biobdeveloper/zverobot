import logging


def get_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level=logging.INFO)
    formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


# TODO write marshmallow dataclass?
default_user_data = {
    "reg": True,
    "msg_with_kb_id": 0,
    "location_cache": None,
    "pet_type_cache": None,
    "category_cache": None,
    "input_value_await": None,
    "last_user_upload": 0,
}
