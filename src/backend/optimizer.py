"""
optimizer.py — Greedy berth/crane assignment optimiser (per-port aware)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd

from .simulator import get_berths_for_port

ALTERNATE_PORTS = {
    "Los Angeles":  ["Port of Long Beach", "Port of Oakland", "Port of Seattle"],
    "Long Beach":   ["Port of Los Angeles", "Port of Oakland", "Port of Ensenada"],
    "Singapore":    ["Port of Tanjung Pelepas", "Port of Batam", "Port Klang"],
    "Shanghai":     ["Port of Ningbo", "Port of Qingdao", "Port of Tianjin"],
    "Rotterdam":    ["Port of Antwerp", "Port of Hamburg", "Port of Felixstowe"],
    "Hamburg":      ["Port of Rotterdam", "Port of Antwerp", "Port of Bremerhaven"],
    "Dubai":        ["Port of Jeddah", "Port of Salalah", "Port of Abu Dhabi"],
    "Busan":        ["Port of Incheon", "Port of Gwangyang", "Port of Ulsan"],
}
_DEFAULT_ALTERNATES = ["Nearest Regional Port", "Anchor Bay", "Alternative Terminal"]


def _get_alternates(port_name: str) -> List[str]:
    return ALTERNATE_PORTS.get(port_name, _DEFAULT_ALTERNATES)


def assign_berths(
    vessel_df: pd.DataFrame,
    start_dt: datetime,
    port_name: str = "Los Angeles",
) -> tuple[pd.DataFrame, List[Dict]]:
    """
    Produce a berth+crane assignment for every vessel in vessel_df.

    Returns
    -------
    assignments_df : vessel schedule with berth, crane, timing, wait, status
    routing_advice : list of dicts for vessels that were rerouted/rescheduled
    """
    berths = get_berths_for_port(port_name)
    alternates = _get_alternates(port_name)

    berth_state = {b["id"]: start_dt for b in berths}
    berth_lookup = {b["id"]: b for b in berths}

    assignments = []
    routing_advice = []

    for _, vessel in vessel_df.sort_values("eta").iterrows():
        compatible = [b for b in berths if b["max_loa_m"] >= vessel["loa_m"]]

        if not compatible:
            routing_advice.append({
                "vessel_id": vessel["vessel_id"],
                "vessel_name": vessel["vessel_name"],
                "reason": "No compatible berth (vessel too large)",
                "recommendation": f"Divert to {alternates[0]}",
                "eta": vessel["eta"].isoformat(),
            })
            assignments.append({
                **_base_row(vessel),
                "berth_id": "N/A",
                "berth_name": "REROUTED",
                "cranes_assigned": 0,
                "scheduled_start": None,
                "scheduled_end": None,
                "wait_hours": None,
                "status": "REROUTE_RECOMMENDED",
            })
            continue

        best_berth_id = min(
            [b["id"] for b in compatible],
            key=lambda bid: berth_state[bid],
        )
        berth = berth_lookup[best_berth_id]

        sched_start = max(vessel["eta"], berth_state[best_berth_id])
        sched_end = sched_start + timedelta(hours=float(vessel["handling_hours"]))
        wait_hours = max(0.0, (sched_start - vessel["eta"]).total_seconds() / 3600)

        if wait_hours > 12:
            routing_advice.append({
                "vessel_id": vessel["vessel_id"],
                "vessel_name": vessel["vessel_name"],
                "reason": f"Wait time {wait_hours:.1f}h exceeds 12h threshold",
                "recommendation": (
                    f"Reschedule ETA to {sched_start.strftime('%Y-%m-%d %H:%M UTC')} "
                    f"or divert to {alternates[1]}"
                ),
                "eta": vessel["eta"].isoformat(),
            })
            status = "RESCHEDULE_ADVISED"
        else:
            status = "ASSIGNED"

        berth_state[best_berth_id] = sched_end

        assignments.append({
            **_base_row(vessel),
            "berth_id": best_berth_id,
            "berth_name": berth["name"],
            "cranes_assigned": berth["cranes"],
            "scheduled_start": sched_start,
            "scheduled_end": sched_end,
            "wait_hours": round(wait_hours, 2),
            "status": status,
        })

    return pd.DataFrame(assignments), routing_advice


def _base_row(vessel) -> Dict:
    return {
        "vessel_id": vessel["vessel_id"],
        "vessel_name": vessel["vessel_name"],
        "shipping_line": vessel["shipping_line"],
        "vessel_class": vessel["vessel_class"],
        "teu": vessel["teu"],
        "origin": vessel["origin"],
        "eta": vessel["eta"],
    }


def get_optimizer_summary(assignments_df: pd.DataFrame, routing_advice: List[Dict]) -> Dict:
    assigned = assignments_df[assignments_df["status"] == "ASSIGNED"]
    rerouted = assignments_df[assignments_df["status"] == "REROUTE_RECOMMENDED"]
    reschedule = assignments_df[assignments_df["status"] == "RESCHEDULE_ADVISED"]

    avg_wait = assigned["wait_hours"].mean() if len(assigned) else 0.0
    max_wait = assigned["wait_hours"].max() if len(assigned) else 0.0

    berth_utilization = {}
    for bid in assignments_df["berth_id"].unique():
        if bid != "N/A":
            berth_utilization[bid] = int((assignments_df["berth_id"] == bid).sum())

    return {
        "total_vessels": len(assignments_df),
        "assigned": len(assigned),
        "reroute_recommended": len(rerouted),
        "reschedule_advised": len(reschedule),
        "avg_wait_hours": round(float(avg_wait), 2),
        "max_wait_hours": round(float(max_wait), 2),
        "berth_utilization": berth_utilization,
        "routing_advice": routing_advice[:10],
    }
