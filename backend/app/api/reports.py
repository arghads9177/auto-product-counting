"""Report generation endpoints."""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def generate_report(
    format: str = Query("csv", regex="^(csv|excel|pdf)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Generate report in requested format."""
    return {"report_id": "report_001", "format": format}
