import duckdb
from typing import Any, Dict, List
import pandas as pd
from app.core.config import settings

class DatabaseManager:
    def __init__(self):
        self.db_path = settings.DATABASE_URL
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema"""
        conn = duckdb.connect(self.db_path)
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol VARCHAR PRIMARY KEY,
                name VARCHAR,
                sector VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_data (
                symbol VARCHAR,
                date DATE,
                open_price DOUBLE,
                high_price DOUBLE,
                low_price DOUBLE,
                close_price DOUBLE,
                volume BIGINT,
                market_cap DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_compositions (
                date DATE,
                symbol VARCHAR,
                weight DOUBLE,
                market_cap DOUBLE,
                rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (date, symbol)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_performance (
                date DATE PRIMARY KEY,
                daily_return DOUBLE,
                cumulative_return DOUBLE,
                index_value DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        conn = duckdb.connect(self.db_path)
        try:
            if params:
                result = conn.execute(query, params).fetchdf()
            else:
                result = conn.execute(query).fetchdf()
            return result.to_dict('records') if not result.empty else []
        finally:
            conn.close()
    
    def execute_insert(self, query: str, data: List[tuple]):
        """Execute bulk insert"""
        conn = duckdb.connect(self.db_path)
        try:
            conn.executemany(query, data)
        finally:
            conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return duckdb.connect(self.db_path)

db_manager = DatabaseManager()