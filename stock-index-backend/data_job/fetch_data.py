"""
Standalone data fetching job for stock index backend
This script fetches historical stock data and stores it in the database
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.data_service import data_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_historical_data():
    """Fetch historical stock data"""
    logger.info("Starting data fetch job...")
    
    try:
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Get S&P 500 symbols (or our predefined list)
        symbols = data_service.sp500_symbols
        logger.info(f"Fetching data for {len(symbols)} symbols")
        
        # Fetch historical data (last 3 months)
        logger.info("Fetching historical data from Yahoo Finance...")
        historical_data = data_service.fetch_historical_data(symbols, period="3mo")
        
        if not historical_data:
            logger.error("No data fetched from Yahoo Finance")
            return False
        
        logger.info(f"Successfully fetched data for {len(historical_data)} symbols")
        
        # Store data in database
        logger.info("Storing data in database...")
        data_service.store_stock_data(historical_data)
        
        # Verify data was stored
        available_dates = data_service.get_available_dates()
        logger.info(f"Data stored successfully. Available dates: {len(available_dates)}")
        
        if available_dates:
            logger.info(f"Date range: {available_dates[-1]} to {available_dates[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in data fetch job: {e}")
        return False

def check_database_health():
    """Check if database has sufficient data"""
    try:
        available_dates = data_service.get_available_dates()
        
        if len(available_dates) < 5:
            logger.warning(f"Only {len(available_dates)} days of data available")
            return False
        
        # Check if we have recent data (within last 7 days)
        if available_dates:
            latest_date = available_dates[0].date()
            days_old = (datetime.now().date() - latest_date).days
            
            if days_old > 7:
                logger.warning(f"Latest data is {days_old} days old")
            else:
                logger.info(f"Database health check passed. Latest data is {days_old} days old")
        
        # Check data quality for latest date
        if available_dates:
            latest_stocks = data_service.get_top_stocks_by_market_cap(available_dates[0], 100)
            logger.info(f"Latest date has {len(latest_stocks)} stocks with market cap data")
            
            if len(latest_stocks) < 100:
                logger.warning(f"Only {len(latest_stocks)} stocks available for latest date")
        
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("STOCK INDEX DATA FETCHING JOB")
    logger.info("=" * 60)
    
    # Check if we're running in Docker
    in_docker = os.path.exists('/.dockerenv')
    logger.info(f"Running in Docker: {in_docker}")
    
    # Check database health first
    logger.info("Checking database health...")
    if not check_database_health():
        logger.info("Database needs fresh data, proceeding with fetch...")
        
        # Fetch new data
        if not fetch_historical_data():
            logger.error("Data fetch failed!")
            sys.exit(1)
    else:
        logger.info("Database health check passed, skipping data fetch")
    
    # Final health check
    logger.info("Performing final health check...")
    if check_database_health():
        logger.info("Data fetch job completed successfully!")
    else:
        logger.error("Data fetch job completed but health check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()