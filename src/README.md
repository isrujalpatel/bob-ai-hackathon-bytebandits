# Source Code

## Layout

```
src/
├── backend/           ← Python FastAPI service
│   ├── main.py        ← FastAPI app + all API routes
│   ├── data_fetcher.py← IMF PortWatch API client + CSV cache
│   ├── simulator.py   ← Simulated per-vessel schedule generator
│   ├── congestion.py  ← Rule-based congestion hotspot detector
│   ├── optimizer.py   ← Greedy berth/crane assignment optimiser
│   ├── brief_generator.py ← Google Gemini API wrapper
│   └── requirements.txt
├── frontend/          ← React/Vite dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   ├── styles.css
│   │   └── components/
│   │       ├── CongestionTimeline.jsx
│   │       ├── AssignmentTable.jsx
│   │       ├── OperationsBrief.jsx
│   │       └── MetaBanner.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/              ← Auto-created at runtime; holds CSV cache from PortWatch API
└── .env.example       ← Template for environment variables
```

## Quick start

See [`docs/setup-guide.md`](../docs/setup-guide.md) for full instructions.

```bash
# Backend
cd src/backend
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in GEMINI_API_KEY
uvicorn backend.main:app --app-dir .. --reload --port 8000

# Frontend (new terminal)
cd src/frontend
npm install
npm run dev          # opens http://localhost:3000
```

## Data lineage

- **Real data**: daily vessel-call volumes are fetched live from the
  [IMF PortWatch API](https://portwatch.imf.org) (AIS-based satellite tracking).
  Responses are cached as CSV in `src/data/` for offline/demo resilience.
- **Simulated data**: per-vessel ETAs, berth assignments, and crane counts are
  generated synthetically, calibrated to the real daily volumes.
  This granularity is not available in any free public dataset.
