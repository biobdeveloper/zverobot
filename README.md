<div align="center">
<h1>ZveroBot</h1>
<img src="https://i.imgur.com/ZUlzhaN.jpeg" width="300" height="300">

[![Telegram]][Telegram join]
[![License]][LICENSE.md]
![pre-commit](https://github.com/biobdeveloper/zverobot/workflows/pre-commit/badge.svg)
[![Code style: black]][black code style]

</div>

[Zverobot][Telegram join] is the telegram bot created to help homeless pets by [DvaPsa (means "Two dogs" on russian)](https://www.instagram.com/dva.psa/) team

Check it out https://t.me/zverobot

Homeless pets always need some money. If you want to support us, you can contact DvaPsa Team at the links above

Currently bot works only for russian-speaking users. But we have big plans :)

Zverobot is fully asynchronous, written on Python 3. Special thanks to the greatest Telegram Bot python library [aiogram](https://github.com/aiogram/aiogram)


# How to deploy
If you want to build some telegram bot based on [Zverobot] experience, here is the instructions how to deploy it on the Linux machine.

We publish source code only for the "bot app" part. So you need some admin backend to control database.
I highly recommend to use [flask-admin](https://github.com/flask-admin/flask-admin) because it is simple, fast, and most importantly - compatible with Sqlalchemy so you don't need to redeclare database models.

Also you can create some command handlers in `zverobot/src/tg/handlers/admin_handlers.py` file to manage the bot directly from Telegram.

## Requirements
* [Docker]
* [Docker Compose]

## Installation in Docker
Install git, Docker, Docker Compose:
```bash
sudo apt install git docker.io docker-compose
```
Clone the repository:
```bash
git clone https://github.com/biobdeveloper/zverobot
cd zverobot/
```
Create configuration files from examples and fill it with your data
```bash
cp .env.example .env
```

If you run it with native docker-compose.yml configuration, create docker network by
```bash
sudo docker network create zverobot-network
```

Start the services by running the command:
```bash
sudo docker-compose up
```

# Contributing
You can help by working on opened issues, fixing bugs, creating new features or
improving documentation.

# License
ZveroBot is released under the MIT License.


[Zverobot]: https://github.com/biobdeveloper/zverobot
[License]: https://img.shields.io/github/license/biobdeveloper/zverobot
[LICENSE.md]: LICENSE.md
[Telegram]: https://img.shields.io/badge/Telegram-zverobot-blue?logo=telegram
[Telegram join]: https://t.me/zverobot
[Code style: black]: https://img.shields.io/badge/code%20style-black-000000.svg
[black code style]: https://github.com/psf/black
[Docker]: https://www.docker.com
[Docker Compose]: https://www.docker.com
