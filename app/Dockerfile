# app/Dockerfile

FROM python:3.12-slim

# Create non-privileged user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /code

# Copy dependency files first for better caching
COPY requirements.txt* ./

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir \
      fastapi \
      uvicorn[standard] \
      sqlmodel \
      alembic \
      psycopg2-binary \
      redis \
      cachetools \
      pybreaker \
      gunicorn

# Copy the rest of the code
COPY . .

# Permissions for the non-privileged user
RUN chown -R appuser:appuser /code
USER appuser

# Expose the application port
EXPOSE 8000

# Healthcheck to verify the app is running
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python seed_polls.py && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"]
