FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/

# Railway sets PORT env var; shell form CMD expands it at runtime
CMD exec uvicorn api.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
