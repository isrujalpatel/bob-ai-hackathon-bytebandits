"""
brief_generator.py
-------------------
Generates a natural-language 72-hour port operations brief using the
Google Gemini API (free tier — Gemini 2.5 Flash).

Why Gemini instead of watsonx.ai:
  The project is built end-to-end inside IBM Bob (our AI coding agent).
  For the generative-language runtime feature, we use Google Gemini's free
  tier because provisioning a watsonx.ai instance with usable capacity
  requires a paid IBM Cloud account we did not have time to set up during
  the hackathon.  This substitution is documented in docs/architecture.md.
"""

from __future__ import annotations

import os
import json
from typing import Dict, List
import httpx

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def _build_prompt(
    port_name: str,
    plan_start: str,
    hotspot_summary: Dict,
    optimizer_summary: Dict,
    avg_daily_calls: float,
) -> str:
    routing_text = ""
    for item in optimizer_summary.get("routing_advice", []):
        routing_text += (
            f"  - {item['vessel_name']}: {item['reason']} → {item['recommendation']}\n"
        )
    if not routing_text:
        routing_text = "  (No routing interventions required.)\n"

    hotspot_windows = ""
    for w in hotspot_summary.get("hotspot_windows", []):
        hotspot_windows += (
            f"  - {w['start']} → {w['end']}  "
            f"demand={w['demand']} berths, severity={w['severity']}\n"
        )
    if not hotspot_windows:
        hotspot_windows = "  (No congestion hotspots predicted.)\n"

    prompt = f"""You are a port operations AI assistant. Write a concise BLUF-style
(Bottom Line Up Front) 72-hour port operations plan for shift supervisors at
{port_name}.  The plan must be actionable, clear, and no longer than 500 words.

Use the following computed data as your source of truth — do not invent numbers.

=== PLANNING HORIZON ===
Start: {plan_start}
Duration: 72 hours
Port: {port_name}
Recent average daily container vessel calls (from IMF PortWatch API): {avg_daily_calls:.1f}

=== CONGESTION FORECAST ===
Total 1-hour slots analysed: {hotspot_summary['total_slots']}
Slots with projected overcapacity: {hotspot_summary['hotspot_slots']}
Berth capacity: {hotspot_summary['capacity']} berths
Peak demand: {hotspot_summary['max_demand']} vessels simultaneously at {hotspot_summary['max_demand_time']}
HIGH-severity windows: {hotspot_summary['high_severity_count']}
MEDIUM-severity windows: {hotspot_summary['medium_severity_count']}

Hotspot windows:
{hotspot_windows}

=== ASSIGNMENT OPTIMIZER RESULTS ===
Total vessels in schedule: {optimizer_summary['total_vessels']}
Successfully assigned: {optimizer_summary['assigned']}
Reroute recommended: {optimizer_summary['reroute_recommended']}
Reschedule advised: {optimizer_summary['reschedule_advised']}
Average wait time: {optimizer_summary['avg_wait_hours']:.1f} hours
Maximum wait time: {optimizer_summary['max_wait_hours']:.1f} hours

Routing/rescheduling advice:
{routing_text}

=== OUTPUT FORMAT ===
Structure your brief EXACTLY as follows:
1. BOTTOM LINE (2-3 sentences: overall congestion risk level and key action required)
2. CONGESTION HOTSPOTS (bullet points: when, how bad, which berths affected)
3. BERTH & CRANE ASSIGNMENTS (summary of allocation decisions, any berths under/over-utilised)
4. RECOMMENDED ACTIONS (numbered list: specific actions for shift supervisors, e.g. call-in extra crane operators, notify shipping lines, activate overflow protocol)
5. WATCH ITEMS FOR NEXT 72 HOURS (2-3 bullets: things to monitor)

Write plainly. Avoid jargon. A supervisor who has never used this tool should understand it immediately."""

    return prompt


def generate_operations_brief(
    port_name: str,
    plan_start: str,
    hotspot_summary: Dict,
    optimizer_summary: Dict,
    avg_daily_calls: float,
) -> str:
    """
    Call the Gemini API and return the generated operations brief as a string.

    Requires GEMINI_API_KEY environment variable to be set.
    Falls back to a structured plain-text brief if the API is unavailable.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_brief(port_name, plan_start, hotspot_summary, optimizer_summary)

    prompt = _build_prompt(
        port_name, plan_start, hotspot_summary, optimizer_summary, avg_daily_calls
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
    except Exception as exc:
        print(f"[brief_generator] Gemini API error: {exc}. Using fallback brief.")
        return _fallback_brief(port_name, plan_start, hotspot_summary, optimizer_summary)


def _fallback_brief(
    port_name: str,
    plan_start: str,
    hotspot_summary: Dict,
    optimizer_summary: Dict,
) -> str:
    """
    Rule-based plain-text brief used when Gemini API is unavailable.
    Ensures the app still produces a useful output without LLM access.
    """
    risk = "HIGH" if hotspot_summary["high_severity_count"] > 0 else (
        "MEDIUM" if hotspot_summary["medium_severity_count"] > 0 else "LOW"
    )
    lines = [
        f"72-HOUR PORT OPERATIONS BRIEF — {port_name}",
        f"Planning horizon starts: {plan_start}",
        f"Generated by: Congestion Predictor (fallback mode — Gemini API unavailable)",
        "",
        "1. BOTTOM LINE",
        f"   Overall congestion risk: {risk}.",
        f"   {hotspot_summary['hotspot_slots']} of {hotspot_summary['total_slots']} time slots "
        f"exceed berth capacity (peak demand: {hotspot_summary['max_demand']} vessels at "
        f"{hotspot_summary['max_demand_time']}).",
        "",
        "2. CONGESTION HOTSPOTS",
    ]
    for w in hotspot_summary["hotspot_windows"]:
        lines.append(f"   • {w['start']} – {w['end']}: {w['demand']} vessels ({w['severity']})")

    lines += [
        "",
        "3. BERTH & CRANE ASSIGNMENTS",
        f"   {optimizer_summary['assigned']} vessels assigned | "
        f"{optimizer_summary['reroute_recommended']} rerouted | "
        f"{optimizer_summary['reschedule_advised']} rescheduled.",
        f"   Average wait: {optimizer_summary['avg_wait_hours']:.1f} h  "
        f"Max wait: {optimizer_summary['max_wait_hours']:.1f} h",
        "",
        "4. RECOMMENDED ACTIONS",
        "   1. Alert crane operators to peak windows listed above.",
        "   2. Notify shipping lines of vessels flagged RESCHEDULE_ADVISED.",
        "   3. Confirm overflow capacity at Long Beach if risk = HIGH.",
        "",
        "5. WATCH ITEMS",
        "   • Re-run model every 6 hours as ETAs update.",
        "   • Monitor weather (Santa Ana winds affect crane operations).",
        "   • Track inbound vessel stack for next 24 h beyond this window.",
    ]
    return "\n".join(lines)
