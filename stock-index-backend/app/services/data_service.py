import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.database import db_manager
import requests
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.sp500_symbols = self._get_sp500_symbols()
    
    def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols (we'll use top 150 to ensure we can get top 100)"""
        # This is a simplified list - in production, we'll fetch from a reliable source
        symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'XOM',
            'JNJ', 'JPM', 'V', 'PG', 'MA', 'CVX', 'HD', 'PFE', 'ABBV', 'BAC',
            'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'MRK', 'WMT', 'CSCO', 'DHR', 'VZ',
            'ABT', 'ACN', 'LIN', 'ADBE', 'TXN', 'NKE', 'BMY', 'QCOM', 'PM', 'HON',
            'RTX', 'T', 'UPS', 'SBUX', 'LOW', 'AMD', 'INTU', 'IBM', 'CAT', 'GS',
            'SPGI', 'DE', 'BKNG', 'AXP', 'BLK', 'ELV', 'GE', 'MDT', 'ADI', 'TJX',
            'GILD', 'ADP', 'CVS', 'SYK', 'MMC', 'VRTX', 'LRCX', 'C', 'SCHW', 'MO',
            'ZTS', 'FIS', 'CB', 'SO', 'DUK', 'BSX', 'ITW', 'EOG', 'PYPL', 'CL',
            'NOC', 'MMM', 'APD', 'ICE', 'PLD', 'SHW', 'FCX', 'GD', 'WM', 'USB',
            'NSC', 'COP', 'MCO', 'EMR', 'AON', 'CSX', 'KLAC', 'HUM', 'ECL', 'FDX'
        ]
        return symbols[:100]  # Take first 100 for this example
    
    def fetch_historical_data(self, symbols: List[str], period: str = "2mo") -> Dict[str, pd.DataFrame]:
        """Fetch historical data for given symbols"""
        data = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Fetching {symbol}...")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                info = ticker.info
                
                if not hist.empty:
                    hist = hist.reset_index()
                    hist['Symbol'] = symbol
                    hist['MarketCap'] = hist['Close'] * info.get('sharesOutstanding', 0)
                    data[symbol] = hist
                    
                time.sleep(1.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                continue
        
        return data
    
    def store_stock_data(self, data: Dict[str, pd.DataFrame]):
        """Store stock data in database"""
        # Store stock metadata
        stock_records = []
        daily_records = []
        
        for symbol, df in data.items():
            # Add stock metadata
            stock_records.append((symbol, symbol, "Technology"))  # Simplified; tech for all
            
            # Add daily data
            for _, row in df.iterrows():
                daily_records.append((
                    symbol,
                    row['Date'].date(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume']),
                    float(row.get('MarketCap', 0))
                ))
        
        # Insert stock metadata
        if stock_records:
            db_manager.execute_insert(
                "INSERT OR IGNORE INTO stocks (symbol, name, sector) VALUES (?, ?, ?)",
                stock_records
            )
        
        # Insert daily data
        if daily_records:
            db_manager.execute_insert(
                """
                INSERT INTO daily_data 
                (symbol, date, open_price, high_price, low_price, close_price, volume, market_cap) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                daily_records
            )
    
    def get_available_dates(self) -> List[str]:
        """Get available trading dates"""
        query = "SELECT DISTINCT date FROM daily_data ORDER BY date DESC"
        results = db_manager.execute_query(query)
        return [r['date'] for r in results]
    
    def get_top_stocks_by_market_cap(self, date: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top stocks by market cap for a given date"""
        query = """
            SELECT symbol, market_cap, close_price
            FROM daily_data 
            WHERE date = ? AND market_cap > 0
            ORDER BY market_cap DESC 
            LIMIT ?
        """
        return db_manager.execute_query(query, (date, limit))

data_service = DataService()