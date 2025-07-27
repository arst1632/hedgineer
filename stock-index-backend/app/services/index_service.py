from datetime import timedelta, datetime
from typing import List, Dict, Any, Tuple
from app.core.database import db_manager
from app.services.data_service import data_service
from app.utils.cache import cache_manager
from app.strategies.weighting import WeightingStrategy, EqualWeightStrategy

class IndexService:
    def __init__(self, weighting_strategy: WeightingStrategy = EqualWeightStrategy()):
        self.base_index_value = 1000.0  # Starting index value
        self.strategy = weighting_strategy
    
    def build_index(self, start_date: str, end_date: str = None) -> Dict[str, Any]:
        """Build index as per given strategy for date range"""
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date is None:
            end = start + timedelta(days=1)
            end_date = end.isoformat()
        
        cache_key = f"index_build_{start_date}_{end_date}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get available dates in range
        available_dates = self._get_dates_in_range(start_date, end_date)
        
        if not available_dates:
            return {"error": "No data available for the specified date range"}
        
        compositions = []
        performance_data = []
        previous_index_value = self.base_index_value
        
        for date in available_dates:
            # Get top 100 stocks for this date
            top_stocks = data_service.get_top_stocks_by_market_cap(date, 100)
            
            if len(top_stocks) < 100:
                continue
            
            # Use the strategy to compute weights
            top_stocks = self.strategy.calculate_weights(top_stocks)
            
            # Store composition
            composition_records = []
            total_market_cap = sum(stock['market_cap'] for stock in top_stocks)
            
            for rank, stock in enumerate(top_stocks, 1):
                composition_record = {
                    'date': date,
                    'symbol': stock['symbol'],
                    'weight': stock['weight'],
                    'market_cap': stock['market_cap'],
                    'rank': rank,
                    'price': stock['close_price']
                }
                compositions.append(composition_record)
                composition_records.append((
                    date, stock['symbol'], stock['weight'], 
                    stock['market_cap'], rank
                ))
            
            # Calculate daily return and index value
            daily_return = self._calculate_daily_return(date, top_stocks)
            current_index_value = previous_index_value * (1 + daily_return)
            
            performance_record = {
                'date': date,
                'daily_return': daily_return,
                'cumulative_return': (current_index_value / self.base_index_value) - 1,
                'index_value': current_index_value
            }
            performance_data.append(performance_record)
            
            # Store in database
            self._store_composition(composition_records)
            self._store_performance(performance_record)
            
            previous_index_value = current_index_value
        
        result = {
            'compositions': compositions,
            'performance': performance_data,
            'summary': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': len(available_dates),
                'final_return': performance_data[-1]['cumulative_return'] if performance_data else 0
            }
        }
        
        cache_manager.set(cache_key, result)
        return result
    
    def get_index_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get index performance for date range"""
        cache_key = f"performance_{start_date}_{end_date}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        query = """
            SELECT date, daily_return, cumulative_return, index_value
            FROM index_performance 
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        
        result = db_manager.execute_query(query, (start_date, end_date))
        cache_manager.set(cache_key, result)
        return result
    
    def get_index_composition(self, date: str) -> List[Dict[str, Any]]:
        """Get index composition for a specific date"""
        cache_key = f"composition_{date}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        query = """
            SELECT ic.symbol, ic.weight, ic.market_cap, ic.rank,
                   dd.close_price as price
            FROM index_compositions ic
            JOIN daily_data dd ON ic.symbol = dd.symbol AND ic.date = dd.date
            WHERE ic.date = ?
            ORDER BY ic.rank
        """
        
        result = db_manager.execute_query(query, (date,))
        cache_manager.set(cache_key, result)
        return result
    
    def get_composition_changes(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get composition changes between dates"""
        cache_key = f"changes_{start_date}_{end_date}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get all compositions in range
        query = """
            SELECT date, symbol
            FROM index_compositions
            WHERE date BETWEEN ? AND ?
            ORDER BY date, symbol
        """
        
        compositions = db_manager.execute_query(query, (start_date, end_date))
        
        # Group by date
        date_compositions = {}
        for comp in compositions:
            date = comp['date']
            if date not in date_compositions:
                date_compositions[date] = set()
            date_compositions[date].add(comp['symbol'])
        
        # Find changes
        changes = []
        dates = sorted(date_compositions.keys())
        
        for i in range(1, len(dates)):
            current_date = dates[i]
            previous_date = dates[i-1]
            
            current_stocks = date_compositions[current_date]
            previous_stocks = date_compositions[previous_date]
            
            entered = current_stocks - previous_stocks
            exited = previous_stocks - current_stocks
            
            if entered or exited:
                changes.append({
                    'date': current_date,
                    'entered': list(entered),
                    'exited': list(exited),
                    'total_changes': len(entered) + len(exited)
                })
        
        cache_manager.set(cache_key, changes)
        return changes
    
    def _get_dates_in_range(self, start_date: str, end_date: str) -> List[str]:
        """Get available trading dates in range"""
        query = """
            SELECT DISTINCT date 
            FROM daily_data 
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        """
        results = db_manager.execute_query(query, (start_date, end_date))
        return [r['date'] for r in results]
    
    def _calculate_daily_return(self, date: str, stocks: List[Dict]) -> float:
        """Calculate daily return for equal-weighted portfolio"""
        # For first day, return 0
        # For subsequent days, calculate based on price changes
        
        # Get previous trading day
        prev_query = """
            SELECT MAX(date) as prev_date
            FROM daily_data 
            WHERE date < ?
        """
        prev_result = db_manager.execute_query(prev_query, (date,))
        
        if not prev_result or not prev_result[0]['prev_date']:
            return 0.0
        
        prev_date = prev_result[0]['prev_date']
        
        # Get previous day prices for same stocks
        symbols = [stock['symbol'] for stock in stocks]
        symbol_list = "', '".join(symbols)
        
        prev_query = f"""
            SELECT symbol, close_price
            FROM daily_data 
            WHERE date = ? AND symbol IN ('{symbol_list}')
        """
        
        prev_prices = {r['symbol']: r['close_price'] 
                      for r in db_manager.execute_query(prev_query, (prev_date,))}
        
        # Calculate weighted return
        total_return = 0.0
        valid_stocks = 0
        
        for stock in stocks:
            symbol = stock['symbol']
            if symbol in prev_prices and prev_prices[symbol] > 0:
                stock_return = (stock['close_price'] - prev_prices[symbol]) / prev_prices[symbol]
                total_return += stock_return * stock['weight']
                valid_stocks += 1
        
        return total_return if valid_stocks > 0 else 0.0
    
    def _store_composition(self, records: List[Tuple]):
        """Store index composition"""
        db_manager.execute_insert("""
            INSERT INTO index_compositions 
            (date, symbol, weight, market_cap, rank) 
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date, symbol) DO UPDATE SET
                weight = excluded.weight,
                market_cap = excluded.market_cap,
                rank = excluded.rank""",
            records
        )
    
    def _store_performance(self, record: Dict[str, Any]):
        """Store index performance"""
        db_manager.execute_insert("""
            INSERT INTO index_performance 
            (date, daily_return, cumulative_return, index_value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                daily_return = excluded.daily_return,
                cumulative_return = excluded.cumulative_return,
                index_value = excluded.index_value""",
        [(record['date'], record['daily_return'], 
        record['cumulative_return'], record['index_value'])]
    )


index_service = IndexService()