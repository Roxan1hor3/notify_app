FROM python:3.11-slim-buster

RUN apt-get update && apt-get install --no-install-recommends -y libmagic1


RUN pip install poetry

WORKDIR /app
COPY ./poetry.lock /app/poetry.lock
COPY ./pyproject.toml /app/pyproject.toml
COPY . /app
RUN poetry install
RUN pip install --ignore-installed uvicorn==0.20.0
CMD python3 -m src.entrypoints.notify_asgi
