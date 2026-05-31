FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for BeautifulSoup/lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY .env.example .env.example

# Create directories that the app writes to at runtime
RUN mkdir -p models logs src

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
