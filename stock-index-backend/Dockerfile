FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory and set permissions
RUN mkdir -p data && chmod 755 data

# Create a volume mount point for persistent data
VOLUME ["/app/data"]

# Create initialization script
COPY docker-init.sh /docker-init.sh
RUN chmod +x /docker-init.sh

# Expose port
EXPOSE 8000

# Use initialization script as entrypoint
ENTRYPOINT ["/docker-init.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]