from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io
from datetime import datetime

from app.models.schemas import (
    IndexBuildRequest, ExportRequest, StockComposition, 
    IndexPerformance, CompositionChange, IndexBuildResponse
)
from app.services.index_service import index_service
from app.services.export_service import export_service
import logging


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/build-index", response_model=IndexBuildResponse)
async def build_index(request: IndexBuildRequest):
    """Build index for given date range"""
    try:
        logger.info(f"Received build-index request: start={request.start_date}, end={request.end_date}")
        result = index_service.build_index(
            start_date=request.start_date,
            end_date=request.end_date or request.start_date
        )
        logger.debug(f"build_index result: {result}")

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return IndexBuildResponse(
            success=True,
            message=f"Index built successfully for {request.start_date} to {request.end_date or request.start_date}",
            summary=result.get("summary")
        )
    
    except Exception as e:
        logger.exception("Error building index")
        raise HTTPException(status_code=500, detail=f"Error building index: {str(e)}")

@router.get("/index-performance")
async def get_index_performance(
    start_date: str,
    end_date: str
) -> List[IndexPerformance]:
    """Get index performance for date range"""
    try:
        # Validate date format
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        logger.info(f"Received index performance request: start={start_date}, end={end_date}")
        performance_data = index_service.get_index_performance(start_date, end_date)
        logger.info(f"get_index_performance result: {performance_data}")
        return [
            IndexPerformance(
                date=record['date'].date().isoformat() if hasattr(record['date'], 'date') else str(record['date']),
                daily_return=record['daily_return'],
                cumulative_return=record['cumulative_return'],
                index_value=record['index_value']
            )
            for record in performance_data
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance: {str(e)}")

@router.get("/index-composition")
async def get_index_composition(date: str) -> List[StockComposition]:
    """Get index composition for specific date"""
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        composition_data = index_service.get_index_composition(date)
        
        if not composition_data:
            raise HTTPException(status_code=404, detail=f"No composition data found for {date}")
        
        return [
            StockComposition(
                symbol=record['symbol'],
                weight=record['weight'],
                market_cap=record['market_cap'],
                rank=record['rank'],
                price=record['price']
            )
            for record in composition_data
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving composition: {str(e)}")

@router.get("/composition-changes")
async def get_composition_changes(
    start_date: str,
    end_date: str
) -> List[CompositionChange]:
    """Get composition changes between dates"""
    try:
        # Validate date format
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        changes_data = index_service.get_composition_changes(start_date, end_date)
        
        return [
            CompositionChange(
                date=record['date'].date().isoformat() if hasattr(record['date'], 'date') else str(record['date']),
                entered=record['entered'],
                exited=record['exited'],
                total_changes=record['total_changes']
            )
            for record in changes_data
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving changes: {str(e)}")

@router.post("/export-data")
async def export_data(request: ExportRequest):
    """Export index data to Excel"""
    try:
        # Validate date format
        datetime.strptime(request.start_date, "%Y-%m-%d")
        datetime.strptime(request.end_date, "%Y-%m-%d")
        
        excel_data = export_service.export_to_excel(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Create response
        excel_buffer = io.BytesIO(excel_data)
        
        filename = f"index_data_{request.start_date}_to_{request.end_date}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stock-index-backend"}