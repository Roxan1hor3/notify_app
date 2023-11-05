FROM python:3.11-slim-buster

RUN apt-get update && apt-get install --no-install-recommends -y libmagic1


RUN pip install poetry

WORKDIR /app
COPY ./poetry.lock /app/poetry.lock
COPY ./pyproject.toml /app/pyproject.toml
COPY . /app
RUN poetry install