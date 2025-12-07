FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (libpq-dev needed for psycopg2 compilation if not using binary, 
# but we use psycopg2-binary so usually fine. Clean cache.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
