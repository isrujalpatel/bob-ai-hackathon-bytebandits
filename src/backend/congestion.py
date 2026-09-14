"""
congestion.py — Rule-based congestion hotspot detector (per-port capacity aware)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd

from .simulator import get_berths_for_port

SLOT_HOURS = 1


def detect_congestion(
    vessel_df: pd.DataFrame,
    start_dt: datetime,
    horizon_hours: int = 72,
    port_name: str = "Los Angeles",
) -> pd.DataFrame:
    """
    Compute slot-by-slot berth demand and flag congestion hotspots.

    Returns a DataFrame with columns:
        slot_start, slot_end, demand, capacity, utilization_pct, severity
    """
    berths = get_berths_for_port(port_name)
    total_berths = len(berths)

    slots = []
    for h in range(0, horizon_hours, SLOT_HOURS):
        slot_start = start_dt + timedelta(hours=h)
        slot_end = slot_start + timedelta(hours=SLOT_HOURS)

        demand = 0
        for _, v in vessel_df.iterrows():
            v_start = v["eta"]
            v_end = v_start + timedelta(hours=float(v["handling_hours"]))
            if v_start < slot_end and v_end > slot_start:
                demand += 1

        util_pct = round((demand / total_berths) * 100, 1) if total_berths else 0

        if demand > total_berths * 2:
            severity = "HIGH"
        elif demand > total_berths:
            severity = "MEDIUM"
        elif demand == total_berths:
            severity = "LOW"
        else:
            severity = "NORMAL"

        slots.append({
            "slot_start": slot_start,
            "slot_end": slot_end,
            "demand": demand,
            "capacity": total_berths,
            "utilization_pct": util_pct,
            "severity": severity,
        })

    return pd.DataFrame(slots)


def get_hotspot_summary(congestion_df: pd.DataFrame) -> Dict:
    """Return a high-level summary dict for the Gemini prompt and API response."""
    hotspots = congestion_df[congestion_df["severity"].isin(["MEDIUM", "HIGH"])]
    peak_row = congestion_df.loc[congestion_df["demand"].idxmax()]

    return {
        "total_slots": len(congestion_df),
        "hotspot_slots": len(hotspots),
        "max_demand": int(peak_row["demand"]),
        "max_demand_time": peak_row["slot_start"].strftime("%Y-%m-%d %H:%M UTC"),
        "capacity": int(peak_row["capacity"]),
        "high_severity_count": int((congestion_df["severity"] == "HIGH").sum()),
        "medium_severity_count": int((congestion_df["severity"] == "MEDIUM").sum()),
        "hotspot_windows": [
            {
                "start": row["slot_start"].strftime("%Y-%m-%d %H:%M UTC"),
                "end": row["slot_end"].strftime("%Y-%m-%d %H:%M UTC"),
                "demand": int(row["demand"]),
                "severity": row["severity"],
            }
            for _, row in hotspots.head(10).iterrows()
        ],
    }
