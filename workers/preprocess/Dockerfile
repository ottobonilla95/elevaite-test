FROM python:3.11-alpine

RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN touch README.md

RUN poetry install && rm -rf $POETRY_CACHE_DIR

COPY . .
RUN poetry install && rm -rf $POETRY_CACHE_DIR

CMD ["poetry", "run", "python", "-u", "preprocess_worker.py"]