# Demo Artifacts

## Demo Video

Record a 3–5 minute walkthrough video showing the app running end-to-end:

1. Start the backend and frontend (show the terminal)
2. Open the dashboard in a browser
3. Select "Port of Los Angeles" and click "Run 72h Plan"
4. Walk through the congestion timeline — point out a HIGH-severity window
5. Show the assignment table — filter by RESCHEDULE_ADVISED
6. Show the AI operations brief — read the bottom line aloud
7. Briefly show the `/api/plan` JSON response in the browser or Postman

Upload to YouTube (unlisted) or Loom, then paste the URL in `demo-video-link.txt`.

## Live Demo

After deploying to Render + Vercel, paste the Vercel URL in `demo/live-demo-url.txt`.
If not deployed, leave `demo/live-demo-url.txt` as `NOT DEPLOYED`.

**Remember**: warm up the Render backend by hitting `/health` 60 seconds before recording or sharing the link.

## Screenshots

Name screenshots as `01-...`, `02-...`, `03-...` etc. At minimum capture:

1. `01-dashboard-empty.png` — the landing page before running a plan
2. `02-congestion-timeline.png` — the 72-hour congestion chart with coloured bars
3. `03-assignment-table.png` — the vessel assignment table with status filters
4. `04-operations-brief.png` — the AI-generated operations brief panel
