FROM python:3.11-slim

WORKDIR /germinate-ai

RUN pip install pip poetry setuptools wheel -U --no-cache-dir

COPY pyproject.toml poetry.lock ./

RUN poetry install --without-dev --no-cache

COPY germinate-ai /germinate-ai

RUN poetry install --without=dev --no-cache

CMD poetry run germinate-ai coordinator run