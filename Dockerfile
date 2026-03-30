FROM python:3.11-slim

WORKDIR /app

# Install only minimal dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/

# Expose port 8000 (Railway will route traffic to this port)
EXPOSE 8000

# Use exec form with env variable expansion
# Railway sets PORT env var, fallback to 8000 if not set
CMD sh -c "exec uvicorn api.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}"
