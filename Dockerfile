FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/

# Railway will set PORT env var, we expose 8000 for internal routing
EXPOSE 8000

# Simple entry point - let uvicorn handle port configuration
CMD ["python", "-m", "uvicorn", "api.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
