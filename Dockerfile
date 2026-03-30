FROM python:3.11-slim

WORKDIR /app

# Install only minimal dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/

EXPOSE 8000

CMD ["uvicorn", "api.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
