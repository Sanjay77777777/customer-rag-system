FROM python:3.12-slim

WORKDIR /app

COPY requirements-api.txt requirements-rag.txt .
RUN pip install --no-cache-dir -r requirements-api.txt -r requirements-rag.txt

COPY api/ api/
COPY rag/ rag/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
