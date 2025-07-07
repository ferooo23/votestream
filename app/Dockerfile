# app/Dockerfile

FROM python:3.12-slim

# Crear usuario no privilegiado
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /code

# Copiar archivos de dependencias primero para mejor caché
COPY requirements.txt* ./ 

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlmodel \
    alembic \
    psycopg2-binary \
    redis \
    cachetools \
    pybreaker

# Copiar el resto del código
COPY . .

# Permisos para el usuario no privilegiado
RUN chown -R appuser:appuser /code
USER appuser

# Exponer el puerto de la aplicación
EXPOSE 8000

# Healthcheck para comprobar que la app está funcionando
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "python seed_polls.py && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4"]
