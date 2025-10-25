FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
EXPOSE 8000

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]