"""
main.py — FastAPI backend for the Container Congestion Predictor
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Load .env from src/ directory (one level up from backend/)
load_dotenv(Path(__file__).parent.parent / ".env")

from .data_fetcher import (
    fetch_portwatch,
    get_recent_avg_container_calls,
    get_data_source_label,
    _normalise_port_name,
)
from .simulator import generate_vessel_schedule, get_berths_for_port
from .congestion import detect_congestion, get_hotspot_summary
from .optimizer import assign_berths, get_optimizer_summary
from .brief_generator import generate_operations_brief

app = FastAPI(
    title="Container Congestion Predictor API",
    description=(
        "Port congestion prediction, berth assignment optimisation, and "
        "AI-generated 72-hour operations briefs for port shift supervisors."
    ),
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the Vercel frontend + local dev
origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tightened to origins list in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _df_to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to JSON-serialisable list of dicts."""
    return df.where(df.notna(), None).astype(object).to_dict(orient="records")


def _serialize_row(row: dict) -> dict:
    """Convert datetime / Timestamp values to ISO strings."""
    out = {}
    for k, v in row.items():
        if isinstance(v, (datetime, pd.Timestamp)):
            out[k] = v.isoformat() if pd.notna(v) else None
        elif v is None or (isinstance(v, float) and pd.isna(v)):
            out[k] = None
        else:
            out[k] = v
    return out


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "container-congestion-predictor"}


@app.get("/api/portwatch")
def portwatch_data(
    port: str = Query("Los Angeles", description="Port name (IMF PortWatch format)"),
    days: int = Query(90, ge=7, le=365),
):
    """
    Return raw IMF PortWatch data for the specified port.
    Data is real AIS-based daily vessel-call counts from the IMF.
    """
    try:
        df = fetch_portwatch(port_name=port, days=days)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    records = []
    for _, row in df.iterrows():
        r = row.to_dict()
        r = _serialize_row(r)
        records.append(r)

    return {"port": port, "days": days, "records": records}


@app.get("/api/plan")
def get_72h_plan(
    port: str = Query("Los Angeles"),
    horizon_hours: int = Query(72, ge=24, le=168),
):
    """
    Main endpoint: fetches real PortWatch data, generates simulated vessel
    schedule calibrated to real daily averages, runs congestion detection
    and berth assignment optimiser, returns full plan.
    """
    # Normalise port name to canonical IMF form
    api_port = _normalise_port_name(port)

    # 1. Real PortWatch data (or static baseline fallback)
    pw_df = fetch_portwatch(port_name=api_port)
    avg_daily = get_recent_avg_container_calls(pw_df)
    data_source = get_data_source_label(pw_df)

    # 2. Simulated vessel schedule calibrated to real daily volumes
    start_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    vessel_df = generate_vessel_schedule(
        horizon_hours=horizon_hours,
        avg_daily_calls=avg_daily,
        start_dt=start_dt,
        port_name=api_port,
    )

    # 3. Congestion detection (uses per-port berth count)
    congestion_df = detect_congestion(vessel_df, start_dt, horizon_hours, port_name=api_port)
    hotspot_summary = get_hotspot_summary(congestion_df)

    # 4. Berth assignment optimiser (uses per-port berth config)
    assignments_df, routing_advice = assign_berths(vessel_df, start_dt, port_name=api_port)
    opt_summary = get_optimizer_summary(assignments_df, routing_advice)

    # 5. Gemini-generated operations brief
    brief = generate_operations_brief(
        port_name=api_port,
        plan_start=start_dt.strftime("%Y-%m-%d %H:%M UTC"),
        hotspot_summary=hotspot_summary,
        optimizer_summary=opt_summary,
        avg_daily_calls=avg_daily,
    )

    # Berth config for frontend reference
    berths_info = [
        {"id": b["id"], "name": b["name"], "max_loa_m": b["max_loa_m"], "cranes": b["cranes"]}
        for b in get_berths_for_port(api_port)
    ]

    vessels_out = [_serialize_row(r) for r in vessel_df.to_dict(orient="records")]
    congestion_out = [_serialize_row(r) for r in congestion_df.to_dict(orient="records")]
    assignments_out = [_serialize_row(r) for r in assignments_df.to_dict(orient="records")]

    return {
        "meta": {
            "port": api_port,
            "plan_start": start_dt.isoformat(),
            "horizon_hours": horizon_hours,
            "avg_daily_container_calls_real": round(avg_daily, 2),
            "data_source": data_source,
            "berth_count": len(berths_info),
        },
        "vessels": vessels_out,
        "congestion_timeline": congestion_out,
        "hotspot_summary": hotspot_summary,
        "assignments": assignments_out,
        "optimizer_summary": opt_summary,
        "operations_brief": brief,
        "berths": berths_info,
    }


@app.get("/api/historical")
def historical_trend(
    port: str = Query("Los Angeles"),
    days: int = Query(90, ge=14, le=365),
):
    """
    Return historical daily vessel-call trend (real IMF PortWatch data).
    Used by the frontend to draw the trend chart behind the hotspot timeline.
    """
    api_port = _normalise_port_name(port)
    df = fetch_portwatch(port_name=api_port, days=days)
    cols = ["date", "portcalls_container", "portcalls", "portcalls_cargo"]
    available = [c for c in cols if c in df.columns]
    df_out = df[available].copy()
    records = [_serialize_row(r) for r in df_out.to_dict(orient="records")]
    return {
        "port": api_port,
        "days": days,
        "trend": records,
        "data_source": get_data_source_label(df),
    }
