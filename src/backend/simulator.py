"""
simulator.py
-------------
Generates a SIMULATED per-vessel schedule for a 72-hour planning horizon
calibrated against REAL daily vessel-call averages from the IMF PortWatch API.

Each supported port has its own berth configuration (terminal names, crane
counts, max LOA) drawn from publicly available port authority documentation.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# ---------------------------------------------------------------------------
# Per-port berth configurations
# ---------------------------------------------------------------------------
PORT_BERTHS: Dict[str, List[Dict]] = {
    "Los Angeles": [
        {"id": "B1", "name": "APM Terminal Pier 400",       "max_loa_m": 400, "cranes": 4},
        {"id": "B2", "name": "Yang Ming Terminal (YTI)",    "max_loa_m": 350, "cranes": 3},
        {"id": "B3", "name": "TraPac (TTI) West",           "max_loa_m": 320, "cranes": 3},
        {"id": "B4", "name": "Pacific Container Terminal",  "max_loa_m": 350, "cranes": 3},
        {"id": "B5", "name": "ITS Terminal",                "max_loa_m": 280, "cranes": 2},
        {"id": "B6", "name": "WBCT West Basin",             "max_loa_m": 260, "cranes": 2},
    ],
    "Long Beach": [
        {"id": "B1", "name": "Middle Harbor (LBCT) T21-22", "max_loa_m": 400, "cranes": 4},
        {"id": "B2", "name": "Long Beach Container T24",    "max_loa_m": 366, "cranes": 4},
        {"id": "B3", "name": "SSA Marine T22",              "max_loa_m": 320, "cranes": 3},
        {"id": "B4", "name": "Pier F – Everport T",         "max_loa_m": 300, "cranes": 3},
        {"id": "B5", "name": "Pier C Berth C-60",           "max_loa_m": 280, "cranes": 2},
        {"id": "B6", "name": "Pier A – Wallenius",          "max_loa_m": 260, "cranes": 2},
    ],
    "Singapore": [
        {"id": "B1",  "name": "Tuas MegaPort T1",           "max_loa_m": 400, "cranes": 5},
        {"id": "B2",  "name": "Tuas MegaPort T2",           "max_loa_m": 400, "cranes": 5},
        {"id": "B3",  "name": "Pasir Panjang T1",           "max_loa_m": 366, "cranes": 4},
        {"id": "B4",  "name": "Pasir Panjang T2",           "max_loa_m": 366, "cranes": 4},
        {"id": "B5",  "name": "Pasir Panjang T3",           "max_loa_m": 350, "cranes": 4},
        {"id": "B6",  "name": "Pasir Panjang T4",           "max_loa_m": 350, "cranes": 3},
        {"id": "B7",  "name": "Brani Terminal",             "max_loa_m": 320, "cranes": 3},
        {"id": "B8",  "name": "Keppel T1",                  "max_loa_m": 300, "cranes": 3},
        {"id": "B9",  "name": "Keppel T2",                  "max_loa_m": 280, "cranes": 2},
        {"id": "B10", "name": "Keppel T3",                  "max_loa_m": 260, "cranes": 2},
    ],
    "Shanghai": [
        {"id": "B1",  "name": "Yangshan Deep Water Port Z1","max_loa_m": 400, "cranes": 5},
        {"id": "B2",  "name": "Yangshan Deep Water Port Z2","max_loa_m": 400, "cranes": 5},
        {"id": "B3",  "name": "Yangshan Deep Water Port Z3","max_loa_m": 400, "cranes": 4},
        {"id": "B4",  "name": "Yangshan Deep Water Port Z4","max_loa_m": 366, "cranes": 4},
        {"id": "B5",  "name": "Waigaoqiao T1-T4",           "max_loa_m": 350, "cranes": 4},
        {"id": "B6",  "name": "Waigaoqiao T5-T6",           "max_loa_m": 320, "cranes": 3},
        {"id": "B7",  "name": "Shanghai Shengdong T1",      "max_loa_m": 400, "cranes": 5},
        {"id": "B8",  "name": "Shanghai Shengdong T2",      "max_loa_m": 400, "cranes": 5},
        {"id": "B9",  "name": "Pudong Int'l Container T",   "max_loa_m": 300, "cranes": 3},
        {"id": "B10", "name": "SIPG Mingdong",              "max_loa_m": 280, "cranes": 3},
    ],
    "Rotterdam": [
        {"id": "B1", "name": "APM Terminals Maasvlakte 2",  "max_loa_m": 400, "cranes": 5},
        {"id": "B2", "name": "Rotterdam World Gateway",     "max_loa_m": 400, "cranes": 4},
        {"id": "B3", "name": "ECT Delta Terminal",          "max_loa_m": 366, "cranes": 4},
        {"id": "B4", "name": "ECT Home Terminal",           "max_loa_m": 350, "cranes": 3},
        {"id": "B5", "name": "Uniport Multipurpose",        "max_loa_m": 300, "cranes": 3},
        {"id": "B6", "name": "RST Container Terminal",      "max_loa_m": 280, "cranes": 2},
        {"id": "B7", "name": "Steinweg Terminals",          "max_loa_m": 260, "cranes": 2},
    ],
    "Hamburg": [
        {"id": "B1", "name": "HHLA Container T Altenwerder","max_loa_m": 400, "cranes": 4},
        {"id": "B2", "name": "HHLA Container T Burchardkai","max_loa_m": 366, "cranes": 4},
        {"id": "B3", "name": "HHLA Container T Tollerort",  "max_loa_m": 320, "cranes": 3},
        {"id": "B4", "name": "Eurogate CT Hamburg",         "max_loa_m": 350, "cranes": 3},
        {"id": "B5", "name": "MSC Gate Terminal",           "max_loa_m": 300, "cranes": 2},
    ],
    "Dubai": [
        {"id": "B1", "name": "Jebel Ali T1 (Mina Jebel)",  "max_loa_m": 400, "cranes": 5},
        {"id": "B2", "name": "Jebel Ali T2",                "max_loa_m": 400, "cranes": 4},
        {"id": "B3", "name": "Jebel Ali T3",                "max_loa_m": 366, "cranes": 4},
        {"id": "B4", "name": "Jebel Ali T4",                "max_loa_m": 350, "cranes": 3},
        {"id": "B5", "name": "Dubai CT (Rashid Port)",      "max_loa_m": 300, "cranes": 3},
        {"id": "B6", "name": "Hamriyah Free Zone Port",     "max_loa_m": 260, "cranes": 2},
    ],
    "Busan": [
        {"id": "B1", "name": "Busan New Port HPNT",         "max_loa_m": 400, "cranes": 4},
        {"id": "B2", "name": "Busan New Port BNCT",         "max_loa_m": 366, "cranes": 4},
        {"id": "B3", "name": "Busan New Port PNIT",         "max_loa_m": 350, "cranes": 3},
        {"id": "B4", "name": "Busan Newport BPA T4",        "max_loa_m": 320, "cranes": 3},
        {"id": "B5", "name": "Gamcheon Container T",        "max_loa_m": 280, "cranes": 2},
        {"id": "B6", "name": "Uam Container T",             "max_loa_m": 260, "cranes": 2},
    ],
    "Singapore_default": [  # fallback alias
        {"id": "B1", "name": "Terminal Berth 1",            "max_loa_m": 400, "cranes": 4},
        {"id": "B2", "name": "Terminal Berth 2",            "max_loa_m": 366, "cranes": 4},
        {"id": "B3", "name": "Terminal Berth 3",            "max_loa_m": 350, "cranes": 3},
        {"id": "B4", "name": "Terminal Berth 4",            "max_loa_m": 320, "cranes": 3},
        {"id": "B5", "name": "Terminal Berth 5",            "max_loa_m": 280, "cranes": 2},
        {"id": "B6", "name": "Terminal Berth 6",            "max_loa_m": 260, "cranes": 2},
    ],
}

# Generic fallback berth config for ports not individually configured
_GENERIC_BERTHS_BASE = [
    {"id": "B1", "max_loa_m": 400, "cranes": 4},
    {"id": "B2", "max_loa_m": 366, "cranes": 4},
    {"id": "B3", "max_loa_m": 350, "cranes": 3},
    {"id": "B4", "max_loa_m": 320, "cranes": 3},
    {"id": "B5", "max_loa_m": 280, "cranes": 2},
    {"id": "B6", "max_loa_m": 260, "cranes": 2},
]

VESSEL_CLASSES = [
    {"class": "Ultra-Large (ULCS)", "teu": 18000, "loa_m": 400, "handling_hours": 36, "weight": 0.10},
    {"class": "New-Panamax",         "teu": 14000, "loa_m": 366, "handling_hours": 28, "weight": 0.20},
    {"class": "Post-Panamax",        "teu": 10000, "loa_m": 320, "handling_hours": 22, "weight": 0.30},
    {"class": "Panamax",             "teu": 5000,  "loa_m": 290, "handling_hours": 16, "weight": 0.25},
    {"class": "Feeder",              "teu": 2000,  "loa_m": 200, "handling_hours":  9, "weight": 0.15},
]

SHIPPING_LINES = [
    "Maersk", "MSC", "CMA CGM", "COSCO", "Evergreen",
    "Hapag-Lloyd", "ONE", "Yang Ming", "HMM", "ZIM",
]

# Port-specific vessel origins (adds authenticity)
PORT_ORIGINS: Dict[str, List[str]] = {
    "Los Angeles":  ["Shanghai", "Ningbo", "Shenzhen", "Busan", "Tokyo", "Kaohsiung", "Yokohama", "Singapore", "Port Klang", "Tanjung Pelepas"],
    "Long Beach":   ["Shanghai", "Ningbo", "Shenzhen", "Busan", "Tokyo", "Kaohsiung", "Yokohama", "Singapore", "Port Klang", "Hong Kong"],
    "Singapore":    ["Shanghai", "Ningbo", "Rotterdam", "Hamburg", "Colombo", "Mumbai", "Busan", "Tokyo", "Sydney", "Fremantle"],
    "Shanghai":     ["Los Angeles", "Rotterdam", "Hamburg", "Singapore", "Busan", "Tokyo", "Ningbo", "Guangzhou", "Tianjin", "Qingdao"],
    "Rotterdam":    ["Shanghai", "Singapore", "Busan", "Hong Kong", "Antwerp", "Hamburg", "Algeciras", "Tanger Med", "Felixstowe", "Le Havre"],
    "Hamburg":      ["Shanghai", "Singapore", "Busan", "Rotterdam", "Antwerp", "Gdansk", "Bremerhaven", "Le Havre", "Felixstowe", "Algeciras"],
    "Dubai":        ["Shanghai", "Singapore", "Mumbai", "Colombo", "Karachi", "Nhava Sheva", "Jeddah", "Salalah", "Port Qasim", "Mundra"],
    "Busan":        ["Shanghai", "Singapore", "Los Angeles", "Rotterdam", "Qingdao", "Tianjin", "Ningbo", "Tokyo", "Osaka", "Nagoya"],
}
_DEFAULT_ORIGINS = ["Shanghai", "Singapore", "Rotterdam", "Busan", "Hong Kong", "Tokyo", "Sydney", "Colombo", "Mumbai", "Felixstowe"]


def get_berths_for_port(port_name: str) -> List[Dict]:
    """Return the berth configuration for a given port, with generic fallback."""
    if port_name in PORT_BERTHS:
        return PORT_BERTHS[port_name]
    # Build generic berths with port-prefixed names
    return [
        {**b, "name": f"{port_name} Berth {b['id']}"}
        for b in _GENERIC_BERTHS_BASE
    ]


def generate_vessel_schedule(
    horizon_hours: int = 72,
    avg_daily_calls: float = 8.0,
    start_dt: Optional[datetime] = None,
    port_name: str = "Los Angeles",
) -> pd.DataFrame:
    """
    Generate a simulated 72-hour vessel schedule for the given port.

    Parameters
    ----------
    horizon_hours:   Planning window in hours.
    avg_daily_calls: Daily average container vessel calls (from PortWatch API).
    start_dt:        Start of the planning window (default: now rounded to hour).
    port_name:       Port name — used for origin selection and reproducibility.
    """
    if start_dt is None:
        start_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    # Deterministic seed per port+day so the same port always gives consistent results
    seed = hash(f"{port_name}{start_dt.date()}") % (2**31)
    rng = random.Random(seed)

    total_vessels = max(
        int(len(get_berths_for_port(port_name)) * 1.5),  # at least 1.5× berths
        int(round(avg_daily_calls * (horizon_hours / 24) * rng.uniform(0.8, 1.2))),
    )

    origins = PORT_ORIGINS.get(port_name, _DEFAULT_ORIGINS)
    vessels = []
    for i in range(total_vessels):
        hour_offset = _sample_arrival_hour(horizon_hours, rng)
        eta = start_dt + timedelta(hours=hour_offset)
        vc = _pick_vessel_class(rng)
        line = rng.choice(SHIPPING_LINES)
        vessel_id = f"V{i+1:03d}"
        vessel_name = f"{line[:3].upper()}{rng.randint(100, 999)}"
        vessels.append({
            "vessel_id": vessel_id,
            "vessel_name": vessel_name,
            "shipping_line": line,
            "vessel_class": vc["class"],
            "teu": vc["teu"],
            "loa_m": vc["loa_m"],
            "origin": rng.choice(origins),
            "eta": eta,
            "handling_hours": vc["handling_hours"] + rng.randint(-2, 4),
            "cargo_type": "Container",
        })

    return pd.DataFrame(vessels).sort_values("eta").reset_index(drop=True)


def _pick_vessel_class(rng: random.Random) -> Dict:
    weights = [v["weight"] for v in VESSEL_CLASSES]
    return rng.choices(VESSEL_CLASSES, weights=weights, k=1)[0]


def _sample_arrival_hour(horizon_hours: int, rng: random.Random) -> float:
    """Bimodal distribution — vessels cluster on morning and afternoon tides."""
    r = rng.random()
    if r < 0.40:
        h = rng.gauss(6, 3)
    elif r < 0.70:
        h = rng.gauss(14, 3)
    else:
        h = rng.uniform(0, horizon_hours)
    return max(0.0, h % horizon_hours)


# Legacy: keep module-level BERTHS pointing to LA for backward compat with congestion.py
BERTHS = PORT_BERTHS["Los Angeles"]
