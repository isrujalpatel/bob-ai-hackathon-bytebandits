"""
data_fetcher.py
----------------
Fetches real daily vessel-call data from the IMF PortWatch API.

Port name normalisation:
  The IMF PortWatch API uses specific port name strings that differ from
  common display names (e.g. "Singapore" not "Port of Singapore").
  This module maps UI-friendly names to the exact API strings and also
  bundles static 90-day CSV datasets for every supported port so the app
  works offline and on the first run without waiting for the API.

Data lineage:
  - Daily vessel-call volumes come LIVE from the IMF PortWatch REST API.
  - Per-vessel ETAs and berth/crane assignments are SIMULATED on top of
    those real daily counts (that granularity is not publicly available).
  - See docs/solution-overview.md for full data-lineage disclosure.
"""

import os
import requests
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
import random

IMF_PORTWATCH_ENDPOINT = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services"
    "/Daily_Ports_Data/FeatureServer/0/query"
)

CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Port name mapping: UI display name → exact IMF PortWatch API portname
# ---------------------------------------------------------------------------
PORT_NAME_MAP = {
    # Display name (lowercase key)       → IMF PortWatch exact string
    "los angeles":    "Los Angeles",
    "long beach":     "Long Beach",
    "singapore":      "Singapore",
    "shanghai":       "Shanghai",
    "rotterdam":      "Rotterdam",
    "hamburg":        "Hamburg",
    "antwerp":        "Antwerp",
    "dubai":          "Dubai",
    "busan":          "Busan",
    "hong kong":      "Hong Kong",
    "ningbo":         "Ningbo",
    "shenzhen":       "Shenzhen",
    "guangzhou":      "Guangzhou",
    "tianjin":        "Tianjin",
    "qingdao":        "Qingdao",
    "mumbai":         "Mumbai",
    "nhava sheva":    "Nhava Sheva",
    "jnpt":           "Nhava Sheva",
    "colombo":        "Colombo",
    "port klang":     "Port Klang",
}

# ---------------------------------------------------------------------------
# Per-port static baseline data (avg daily container calls, 90 rows)
# Used when IMF API is unreachable AND no cache exists yet.
# Values sourced from publicly available port throughput reports.
# ---------------------------------------------------------------------------
PORT_BASELINES = {
    "Los Angeles":  {"avg_container": 8.5,  "std": 1.8},
    "Long Beach":   {"avg_container": 8.2,  "std": 1.7},
    "Singapore":    {"avg_container": 35.0, "std": 4.5},
    "Shanghai":     {"avg_container": 42.0, "std": 5.2},
    "Rotterdam":    {"avg_container": 18.0, "std": 2.8},
    "Hamburg":      {"avg_container": 12.0, "std": 2.1},
    "Antwerp":      {"avg_container": 14.0, "std": 2.3},
    "Dubai":        {"avg_container": 16.0, "std": 2.6},
    "Busan":        {"avg_container": 22.0, "std": 3.1},
    "Hong Kong":    {"avg_container": 15.0, "std": 2.4},
    "Ningbo":       {"avg_container": 25.0, "std": 3.8},
    "Shenzhen":     {"avg_container": 28.0, "std": 4.0},
    "Mumbai":       {"avg_container": 7.0,  "std": 1.5},
    "Nhava Sheva":  {"avg_container": 6.5,  "std": 1.4},
    "Colombo":      {"avg_container": 9.0,  "std": 1.8},
    "Port Klang":   {"avg_container": 12.0, "std": 2.0},
}

_DEFAULT_BASELINE = {"avg_container": 10.0, "std": 2.0}


def _normalise_port_name(port_name: str) -> str:
    """Map any UI-friendly port name to the canonical IMF PortWatch string."""
    return PORT_NAME_MAP.get(port_name.lower().strip(), port_name.strip())


def _generate_static_dataset(api_port_name: str, days: int = 90) -> pd.DataFrame:
    """
    Generate a plausible synthetic 90-day dataset when the API is unreachable.
    Calibrated to published throughput figures for each port.
    Clearly labelled as 'generated' — not presented as real API data.
    """
    baseline = PORT_BASELINES.get(api_port_name, _DEFAULT_BASELINE)
    avg = baseline["avg_container"]
    std = baseline["std"]

    rng = random.Random(hash(api_port_name) % (2**31))  # deterministic per port
    base_date = datetime.utcnow().date() - timedelta(days=days)
    rows = []
    for i in range(days):
        d = base_date + timedelta(days=i)
        container = max(1, int(rng.gauss(avg, std)))
        tanker = max(0, int(rng.gauss(avg * 0.3, std * 0.4)))
        dry_bulk = max(0, int(rng.gauss(avg * 0.2, std * 0.3)))
        general = max(0, int(rng.gauss(avg * 0.15, std * 0.2)))
        roro = max(0, int(rng.gauss(avg * 0.1, std * 0.15)))
        total = container + tanker + dry_bulk + general + roro
        rows.append({
            "date": pd.Timestamp(d),
            "portname": api_port_name,
            "portcalls": total,
            "portcalls_container": container,
            "portcalls_tanker": tanker,
            "portcalls_dry_bulk": dry_bulk,
            "portcalls_general_cargo": general,
            "portcalls_roro": roro,
            "portcalls_cargo": container + dry_bulk + general,
            "import_container": int(container * 0.55 * 500),
            "export_container": int(container * 0.45 * 500),
            "import_dry_bulk": int(dry_bulk * 0.6 * 30000),
            "export_dry_bulk": int(dry_bulk * 0.4 * 30000),
            "_source": "static_baseline",
        })
    return pd.DataFrame(rows)


def fetch_portwatch(port_name: str = "Los Angeles", days: int = 90) -> pd.DataFrame:
    """
    Fetch vessel-call data for `port_name`.

    Priority order:
      1. Fresh cache (< 24 h old) — return immediately
      2. Live IMF PortWatch API — fetch, cache, return
      3. Stale cache — use if API fails
      4. Static baseline dataset — generated from published throughput figures
         (labelled with _source='static_baseline' so callers can warn the user)

    Returns a DataFrame sorted by date ascending.
    """
    api_port_name = _normalise_port_name(port_name)
    cache_file = CACHE_DIR / f"portwatch_{api_port_name.replace(' ', '_').lower()}.csv"

    # 1. Fresh cache
    if cache_file.exists():
        age_hours = (datetime.now().timestamp() - cache_file.stat().st_mtime) / 3600
        if age_hours < 24:
            df = pd.read_csv(cache_file, parse_dates=["date"])
            df = df.sort_values("date").reset_index(drop=True)
            print(f"[data_fetcher] Cache hit for '{api_port_name}' ({len(df)} rows)")
            return df

    # 2. Live API
    print(f"[data_fetcher] Fetching IMF PortWatch data for '{api_port_name}'...")
    params = {
        "where": f"portname='{api_port_name}'",
        "outFields": "*",
        "f": "json",
        "orderByFields": "date DESC",
        "resultRecordCount": days,
    }
    try:
        resp = requests.get(IMF_PORTWATCH_ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if "features" not in data or len(data["features"]) == 0:
            raise ValueError(f"No records returned for port '{api_port_name}'")

        rows = [f["attributes"] for f in data["features"]]
        df = pd.DataFrame(rows)
        df.columns = [c.lower() for c in df.columns]

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).dt.tz_localize(None)
            df["date"] = pd.to_datetime(df["date"].dt.date)

        numeric_cols = [c for c in df.columns if c not in ("date", "portname")]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        df["_source"] = "imf_portwatch_api"
        df = df.sort_values("date").reset_index(drop=True)
        df.to_csv(cache_file, index=False)
        print(f"[data_fetcher] Fetched {len(df)} rows from API, cached as {cache_file.name}")
        return df

    except Exception as exc:
        print(f"[data_fetcher] API unavailable ({exc})")

        # 3. Stale cache
        if cache_file.exists():
            print(f"[data_fetcher] Using stale cache for '{api_port_name}'")
            df = pd.read_csv(cache_file, parse_dates=["date"])
            return df.sort_values("date").reset_index(drop=True)

        # 4. Static baseline
        print(f"[data_fetcher] Using static baseline dataset for '{api_port_name}'")
        df = _generate_static_dataset(api_port_name, days)
        df.to_csv(cache_file, index=False)
        return df


def get_recent_avg_container_calls(df: pd.DataFrame, window: int = 14) -> float:
    """Return the rolling average daily container calls over the last `window` days."""
    recent = df.tail(window)
    for col in ("portcalls_container", "portcalls_cargo", "portcalls"):
        if col in recent.columns:
            val = pd.to_numeric(recent[col], errors="coerce").mean()
            if pd.notna(val) and val > 0:
                return float(val)
    return 5.0


def get_data_source_label(df: pd.DataFrame) -> str:
    """Return a human-readable data source label for the UI meta banner."""
    if "_source" not in df.columns:
        return "IMF PortWatch API (real AIS data) + simulated per-vessel schedule"
    src = df["_source"].iloc[-1] if len(df) else "unknown"
    if src == "imf_portwatch_api":
        return "IMF PortWatch API (real AIS data) + simulated per-vessel schedule"
    if src == "static_baseline":
        return "Static baseline dataset (IMF API offline) + simulated per-vessel schedule"
    return "Cached data + simulated per-vessel schedule"
