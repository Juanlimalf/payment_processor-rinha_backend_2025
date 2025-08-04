FROM python:3.13-alpine

WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV POETRY_VIRTUALENVS_CREATE=false

COPY . .

RUN pip install poetry 
RUN poetry install --no-interaction --no-ansi --only main --no-root

CMD [ "uvicorn" , "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop","--http", "httptools", "--no-access-log"]
