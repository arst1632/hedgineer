from pydantic import BaseModel, Field
from typing import List, Optional

class IndexBuildRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")

class ExportRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

class StockComposition(BaseModel):
    symbol: str
    weight: float
    market_cap: float
    rank: int
    price: float

class IndexPerformance(BaseModel):
    date: str
    daily_return: float
    cumulative_return: float
    index_value: float

class CompositionChange(BaseModel):
    date: str
    entered: List[str]
    exited: List[str]
    total_changes: int

class IndexBuildResponse(BaseModel):
    success: bool
    message: str
    summary: Optional[dict] = None