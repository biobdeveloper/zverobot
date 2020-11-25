FROM python:3.8

RUN pip install pipenv

WORKDIR /zverobot

COPY Pipfile.lock /zverobot

RUN pipenv install --ignore-pipfile --keep-outdated

COPY . /zverobot
