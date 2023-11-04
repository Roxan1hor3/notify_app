FROM python:3.11-slim-buster

RUN apt-get update && apt-get install --no-install-recommends -y libmagic1 \
    build-essential && rm -rf /var/lib/apt/lists/*


ARG LOG_APP_LABEL=notify_back
ENV LOG_APP_LABEL ${LOG_APP_LABEL}
ENV LOG_LEVEL INFO
ENV WORKERS 1
ENV WORKER_THREADS 1

ARG PROJECT_ENV
ENV PROJECT_ENV=${PROJECT_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.4.2 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY ./poetry.lock /app/poetry.lock
COPY ./pyproject.toml /app/pyproject.toml
RUN echo "$PROJECT_ENV" && poetry version \
  # Install deps:
  && poetry run pip install -U pip \
  && poetry install \
  $(if [ "$PROJECT_ENV" = 'production' ]; then echo '--no-dev'; fi) \
  --no-interaction --no-ansi \
  # Cleaning poetry installation's cache for production:
  && if [ "$PROJECT_ENV" = 'production' ]; then rm -rf "$POETRY_CACHE_DIR"; fi

COPY . /app


CMD exec gunicorn \
  -c .deploy/docker/service/gunicorn.conf.py \
  src.entrypoints.ads_asgi:app
