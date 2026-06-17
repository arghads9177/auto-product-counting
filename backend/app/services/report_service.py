"""Report generation service — CSV, Excel, PDF."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class ReportService:
    """Generates count/session reports in CSV, Excel, and PDF."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def _fetch_data(
        self,
        start_date: str | None,
        end_date: str | None,
        camera_id: str | None,
    ) -> tuple[list[dict], list[dict]]:
        sess_q: dict[str, Any] = {}
        ev_q: dict[str, Any] = {}

        if camera_id:
            sess_q["camera_id"] = camera_id
            ev_q["camera_id"] = camera_id

        if start_date or end_date:
            ts_filter: dict[str, str] = {}
            if start_date:
                ts_filter["$gte"] = start_date
            if end_date:
                ts_filter["$lte"] = end_date
            sess_q["start_time"] = ts_filter
            ev_q["timestamp"] = ts_filter

        sessions = await (
            self.db["sessions"]
            .find(sess_q, {"_id": 0})
            .sort("start_time", -1)
            .to_list(length=5000)
        )
        events = await (
            self.db["count_events"]
            .find(ev_q, {"_id": 0})
            .sort("timestamp", -1)
            .to_list(length=50000)
        )
        return sessions, events

    async def generate_csv(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        camera_id: str | None = None,
    ) -> bytes:
        sessions, events = await self._fetch_data(start_date, end_date, camera_id)

        buf = io.StringIO()
        writer = csv.writer(buf)

        writer.writerow(["=== Sessions ==="])
        writer.writerow(["session_id", "camera_id", "type", "status", "start_time", "end_time", "count"])
        for s in sessions:
            writer.writerow([
                s.get("session_id"), s.get("camera_id"), s.get("type"),
                s.get("status"), s.get("start_time"), s.get("end_time"),
                s.get("count", 0),
            ])

        writer.writerow([])
        writer.writerow(["=== Count Events ==="])
        writer.writerow(["event_id", "camera_id", "session_id", "track_id", "direction", "timestamp"])
        for e in events:
            writer.writerow([
                e.get("event_id"), e.get("camera_id"), e.get("session_id"),
                e.get("track_id"), e.get("direction"), e.get("timestamp"),
            ])

        return buf.getvalue().encode("utf-8")

    async def generate_excel(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        camera_id: str | None = None,
    ) -> bytes:
        from openpyxl import Workbook

        sessions, events = await self._fetch_data(start_date, end_date, camera_id)

        wb = Workbook()

        ws_sess = wb.active
        ws_sess.title = "Sessions"
        ws_sess.append(["session_id", "camera_id", "type", "status", "start_time", "end_time", "count"])
        for s in sessions:
            ws_sess.append([
                s.get("session_id"), s.get("camera_id"), s.get("type"),
                s.get("status"), s.get("start_time"), s.get("end_time"),
                s.get("count", 0),
            ])

        ws_ev = wb.create_sheet("Count Events")
        ws_ev.append(["event_id", "camera_id", "session_id", "track_id", "direction", "timestamp"])
        for e in events:
            ws_ev.append([
                e.get("event_id"), e.get("camera_id"), e.get("session_id"),
                e.get("track_id"), e.get("direction"), e.get("timestamp"),
            ])

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    async def generate_pdf(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        camera_id: str | None = None,
    ) -> bytes:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        sessions, events = await self._fetch_data(start_date, end_date, camera_id)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Auto Product Counting — Report", styles["Title"]))
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        elements.append(Paragraph(f"Generated: {ts}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Summary
        total_loading = sum(1 for e in events if e.get("direction") == "LOADING")
        total_unloading = sum(1 for e in events if e.get("direction") == "UNLOADING")
        elements.append(Paragraph(
            f"Sessions: {len(sessions)} | "
            f"Count events: {len(events)} | "
            f"Loading: {total_loading} | "
            f"Unloading: {total_unloading}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 12))

        # Sessions table
        if sessions:
            elements.append(Paragraph("Sessions", styles["Heading2"]))
            hdr = ["Session ID", "Camera", "Type", "Status", "Start", "End", "Count"]
            data = [hdr]
            for s in sessions[:200]:
                data.append([
                    str(s.get("session_id", ""))[:20],
                    str(s.get("camera_id", "")),
                    str(s.get("type", "")),
                    str(s.get("status", "")),
                    str(s.get("start_time", ""))[:19],
                    str(s.get("end_time", ""))[:19],
                    str(s.get("count", 0)),
                ])
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))

        doc.build(elements)
        return buf.getvalue()
