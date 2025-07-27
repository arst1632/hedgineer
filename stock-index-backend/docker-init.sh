#!/bin/bash

# Docker initialization script
echo "Initializing Stock Index Backend..."

# Check if database exists and has data
if [ ! -f "/app/data/stocks.db" ] || [ ! -s "/app/data/stocks.db" ]; then
    echo "Database not found or empty. Initializing database..."
    
    # Run data fetch job
    echo "Fetching stock data..."
    python data_job/fetch_data.py
    
    # Check if data fetch was successful
    if [ $? -eq 0 ]; then
        echo "Data fetch completed successfully!"
    else
        echo "Warning: Data fetch failed. Starting API server anyway..."
    fi
else
    echo "Database found. Skipping data initialization."
fi

echo "Starting API server..."
exec "$@"