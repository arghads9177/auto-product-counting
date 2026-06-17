"""Report generation endpoints — CSV, Excel, PDF downloads."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def generate_report(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    camera_id: Optional[str] = None,
):
    """Generate and download a report in CSV, Excel, or PDF format."""
    from app.db.mongo import mongo_connection
    from app.services.report_service import ReportService

    db = mongo_connection.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    svc = ReportService(db)

    if format == "csv":
        data = await svc.generate_csv(start_date, end_date, camera_id)
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=report.csv"},
        )
    elif format == "excel":
        data = await svc.generate_excel(start_date, end_date, camera_id)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=report.xlsx"},
        )
    elif format == "pdf":
        data = await svc.generate_pdf(start_date, end_date, camera_id)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"},
        )
