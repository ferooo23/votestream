FROM python:3.12-slim

WORKDIR /code
COPY . .

RUN pip install --no-cache fastapi uvicorn[standard] sqlmodel alembic psycopg[binary] redis cachetools pybreaker

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]