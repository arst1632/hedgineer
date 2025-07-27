from typing import List, Dict, Any

class WeightingStrategy:
    def calculate_weights(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return list of stocks with 'weight' key added"""
        raise NotImplementedError
    
class EqualWeightStrategy(WeightingStrategy):
    def calculate_weights(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not stocks:
            return []

        weight = 1.0 / len(stocks)
        for stock in stocks:
            stock["weight"] = weight
        return stocks