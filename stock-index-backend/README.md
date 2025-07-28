# Stock Index Backend Service

A FastAPI-based backend service that tracks and manages a custom equal-weighted stock index comprising the top 100 US stocks by daily market capitalization.

## Features

- **Dynamic Index Construction**: Build equal-weighted indices for any date range using a strategy-based design, allowing easy extension to other weighting methods.
- **Historical Performance Tracking**: Retrieve daily and cumulative returns
- **Composition Management**: Track composition changes over time
- **Data Export**: Export all data to well-formatted Excel files
- **Caching**: Redis-based caching for improved performance
- **Containerized**: Full Docker support with docker-compose

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: DuckDB
- **Cache**: Redis
- **Data Processing**: Pandas
- **Data Source**: Yahoo Finance API
- **Containerization**: Docker & Docker Compose

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   git clone https://github.com/arst1632/hedgineer.git
   cd stock-index-backend
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Run data acquisition ( OPTIONAL Docker shell auto runs it in start )**:
   ```bash
   docker-compose exec stock-index-api python data_job/fetch_data.py
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis**:
   ```bash
   redis-server
   ```

3. **Run data acquisition**:
   ```bash
   python data_job/fetch_data.py
   ```

4. **Start the API**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### 1. Build Index

```bash
curl -X POST "http://localhost:8000/api/v1/build-index" \\
  -H "Content-Type: application/json" \\
  -d '{
    "start_date": "2024-01-15",
    "end_date": "2024-01-20"
  }'
```

### 2. Get Index Performance

```bash
curl "http://localhost:8000/api/v1/index-performance?start_date=2024-01-15&end_date=2024-01-20"
```

### 3. Get Index Composition

```bash
curl "http://localhost:8000/api/v1/index-composition?date=2024-01-15"
```

### 4. Get Composition Changes

```bash
curl "http://localhost:8000/api/v1/composition-changes?start_date=2024-01-15&end_date=2024-01-20"
```

### 5. Export Data to Excel

```bash
curl -X POST "http://localhost:8000/api/v1/export-data" \\
  -H "Content-Type: application/json" \\
  -d '{
    "start_date": "2024-01-15",
    "end_date": "2024-01-20"
  }' \\
  --output index_data.xlsx
```

## Database Schema

### Tables

1. **stocks**: Stock metadata
   - `symbol` (VARCHAR, PRIMARY KEY)
   - `name` (VARCHAR)
   - `sector` (VARCHAR)

2. **daily_data**: Daily stock prices and market cap
   - `symbol` (VARCHAR)
   - `date` (DATE)
   - `open_price`, `high_price`, `low_price`, `close_price` (DOUBLE)
   - `volume` (BIGINT)
   - `market_cap` (DOUBLE)

3. **index_compositions**: Daily index compositions
   - `date` (DATE)
   - `symbol` (VARCHAR)
   - `weight` (DOUBLE)
   - `market_cap` (DOUBLE)
   - `rank` (INTEGER)

4. **index_performance**: Daily index performance
   - `date` (DATE)
   - `daily_return` (DOUBLE)
   - `cumulative_return` (DOUBLE)
   - `index_value` (DOUBLE)

## Equal-Weighted Index Logic

The index construction follows these principles:

1. **Daily Selection**: Each day, select top 100 stocks by market capitalization
2. **Equal Weighting**: Assign 1% weight (1/100) to each stock
3. **Daily Rebalancing**: Recalculate weights daily based on new market caps
4. **Return Calculation**: Calculate daily returns based on equal-weighted portfolio performance
5. **Index Value**: Track cumulative performance starting from base value of 1000

## Caching Strategy

- **Redis Keys**:
  - `index_build_{start_date}_{end_date}`: Full index build results
  - `performance_{start_date}_{end_date}`: Performance data
  - `composition_{date}`: Daily compositions
  - `changes_{start_date}_{end_date}`: Composition changes

- **TTL**: 1 hour default, configurable via `CACHE_TTL`

## Production Considerations

### Scaling Improvements

1. **Database**:
   - Move to PostgreSQL for better concurrent access
   - Implement database connection pooling
   - Add database indexes for better query performance

2. **Caching**:
   - Implement cache warming strategies
   - Use Redis Cluster for high availability
   - Add cache invalidation strategies

3. **API**:
   - Add rate limiting
   - Implement API authentication/authorization
   - Add request/response compression
   - Implement async database operations

4. **Data Pipeline**:
   - Use Apache Airflow for job orchestration
   - Implement data quality checks
   - Add retry mechanisms and error handling
   - Use multiple data sources for redundancy

5. **Infrastructure**:
   - Use Kubernetes for container orchestration
   - Implement horizontal pod autoscaling
   - Add monitoring and alerting (Prometheus, Grafana)
   - Use CDN for static assets

6. **Monitoring**:
   - Add application metrics
   - Implement health checks
   - Add distributed tracing
   - Log aggregation and analysis

### Security Enhancements

- API authentication (JWT tokens)
- Input validation and sanitization
- SQL injection prevention
- Rate limiting per user/IP
- HTTPS enforcement

## Testing

To run tests (if implemented):

```bash
pytest tests/ -v
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=data/stocks.db
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
ALPHA_VANTAGE_API_KEY=6PJVILAR0HQRSNRL
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
