# QNet Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

ENV PYTHONUNBUFFERED=1
ENV QNET_CONFIG=/app/config/default.yaml

EXPOSE 8000 8001 3000

CMD ["python", "-m", "uvicorn", "qnet.api.rest:app", "--host", "0.0.0.0", "--port", "8000"]
