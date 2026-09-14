# Solution Overview

## Core Mechanism

The system operates as a four-stage pipeline run on demand for any supported port:

```
Real IMF PortWatch data → Calibrated vessel schedule → Congestion detector → Berth optimiser → Gemini brief
```

**Stage 1 — Real data anchor.**
The pipeline fetches the last 90 days of daily vessel-call counts from the IMF PortWatch REST API (no login required, AIS-satellite-based, updated weekly). The 14-day rolling average of `portcalls_container` becomes the calibration parameter for stage 2. This is the only free, publicly available, globally consistent dataset at this granularity — it is genuinely real.

**Stage 2 — Simulated vessel schedule.**
Individual per-vessel ETAs are not available in any free public dataset (even private AIS feeds behind $50k+/year enterprise licenses don't provide forward ETAs for unpublished voyages). So we generate them: given the real daily average *N* vessels/day, we sample *N × 3* arrivals across the 72-hour window using a bimodal distribution (vessels cluster on morning and afternoon tides), assign each vessel a class (ULCS → feeder), LOA, handling time, and shipping line, all from calibrated probability weights. The result is a realistic synthetic schedule with real volume.

**Stage 3 — Congestion detection.**
A 72-hour planning window is split into 1-hour slots. For each slot, we count the number of vessels whose occupancy interval `[eta, eta + handling_hours)` overlaps it. Compare against berth capacity (6 berths). Slots where demand > capacity are flagged as hotspots; severity is LOW / MEDIUM / HIGH based on how far over capacity. This is deliberate rule-based queueing math — not a black box — so a supervisor or judge can verify any flagged window by inspection.

**Stage 4 — Berth/crane assignment.**
Vessels are sorted by ETA and assigned greedily to the earliest available *compatible* berth (compatibility = vessel LOA ≤ berth max LOA). For each vessel: among compatible berths, pick the one with the earliest `next_free_time`; scheduled start = max(ETA, next_free_time). Wait time = scheduled start − ETA. Vessels waiting > 12 hours are flagged RESCHEDULE_ADVISED; vessels too large for any berth are flagged REROUTE_RECOMMENDED with a suggested alternate port.

**Stage 5 — AI operations brief.**
The hotspot summary and assignment summary are serialised into a structured prompt fed to Google Gemini 2.0 Flash, which returns a BLUF-style 72-hour operations plan formatted for shift supervisors: bottom line up front, bulleted hotspot windows, assignment summary, numbered recommended actions, watch items.

---

## What Makes This Different From a Naive Approach

A naive approach would either (a) present fully synthetic data as if it were real AIS, or (b) show a blank/placeholder when real data is missing. We do neither:
- We use **real data exactly where it exists** (daily aggregate volumes) and **transparently label the simulated layer** on top.
- The congestion detector is **explainable by design** — a supervisor doesn't need to trust a score; they can see demand = 8 vessels, capacity = 6 berths, therefore MEDIUM.
- The assignment optimiser is **O(V × B)**, deterministic, and reproducible — the same input always produces the same output.

---

## Data Lineage (Explicit)

| Data | Source | Real or Simulated |
|---|---|---|
| Daily vessel-call counts | IMF PortWatch API (AIS satellite tracking, ~90k ships) | **REAL** |
| Per-vessel ETAs | Sampled from real daily volume | **SIMULATED** |
| Berth configuration (6 berths, LA/LB terminals) | Publicly known terminal names and approximate specs | **APPROXIMATE** (simplified) |
| Crane counts per berth | Industry-typical values | **SIMULATED** |
| Operations brief text | Google Gemini 2.0 Flash LLM | **AI-GENERATED** |

---

## User Experience

1. Operator opens the dashboard and selects a port (default: Los Angeles).
2. Clicks "Run 72h Plan" — backend fetches live PortWatch data, runs all four stages, returns JSON.
3. Dashboard shows:
   - A colour-coded bar chart: 72 hours on x-axis, vessel demand on y-axis, red line = capacity, bars coloured GREEN / YELLOW / ORANGE / RED by severity.
   - A filterable table: every vessel with its berth, crane count, scheduled start/end, wait time, and status.
   - A formatted AI operations brief on the right: bottom line, hotspots, recommended actions.
4. Total latency from click to results: ~3–5 seconds on warm backend (add ~45 s on first cold-start for Render free tier).

---

## IBM Bob Integration

The entire project — all Python backend modules, all React components, all documentation — was authored inside IBM Bob (the AI coding agent). Bob wrote the IMF API client, the congestion algorithm, the optimizer, the Gemini wrapper, the React components, and every doc file. This is the primary "IBM Bob Integration" story: Bob as the development platform, not a runtime dependency.

---

## Known Limitations

- Per-vessel ETAs are simulated. Production use would require a live AIS stream (e.g., exactEarth, Spire) or a port TOS API — neither is free or public.
- The berth optimiser is greedy FCFS. For a real port, Mixed Integer Programming (e.g., OR-Tools, Gurobi) would give globally optimal assignments at the cost of solve time.
- The Gemini brief is only as accurate as the congestion/assignment data fed to it. Hallucination risk is mitigated by giving Gemini a structured data block and instructing it not to invent numbers.
- Single-port at a time. A production version would run multi-port, multi-horizon in parallel.
