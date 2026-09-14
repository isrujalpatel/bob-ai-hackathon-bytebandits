import React, { useState, useCallback } from 'react'
import axios from 'axios'
import CongestionTimeline from './components/CongestionTimeline.jsx'
import AssignmentTable from './components/AssignmentTable.jsx'
import OperationsBrief from './components/OperationsBrief.jsx'
import BerthUtilisation from './components/BerthUtilisation.jsx'
import HotspotList from './components/HotspotList.jsx'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

const PORTS = [
  { value: 'Los Angeles', label: 'Port of Los Angeles, USA' },
  { value: 'Long Beach',  label: 'Port of Long Beach, USA' },
  { value: 'Singapore',   label: 'Port of Singapore' },
  { value: 'Shanghai',    label: 'Port of Shanghai, China' },
  { value: 'Rotterdam',   label: 'Port of Rotterdam, Netherlands' },
  { value: 'Hamburg',     label: 'Port of Hamburg, Germany' },
  { value: 'Dubai',       label: 'Jebel Ali / Dubai, UAE' },
  { value: 'Busan',       label: 'Port of Busan, South Korea' },
]

function RiskBadge({ summary }) {
  if (!summary) return null
  const risk = summary.high_severity_count > 0 ? 'HIGH'
    : summary.medium_severity_count > 0 ? 'MEDIUM' : 'LOW'
  const colors = { HIGH: '#f43f5e', MEDIUM: '#f59e0b', LOW: '#22d3a0' }
  return (
    <span style={{
      background: `${colors[risk]}18`,
      border: `1px solid ${colors[risk]}44`,
      color: colors[risk],
      borderRadius: 6, padding: '2px 10px',
      fontSize: 11, fontWeight: 800, letterSpacing: '0.08em',
    }}>
      {risk} RISK
    </span>
  )
}

export default function App() {
  const [port, setPort] = useState('Los Angeles')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [plan, setPlan] = useState(null)

  const fetchPlan = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/api/plan`, {
        params: { port, horizon_hours: 72 },
      })
      setPlan(res.data)
    } catch (err) {
      setError(
        err?.response?.data?.detail || err?.message || 'Failed to fetch plan.'
      )
    } finally {
      setLoading(false)
    }
  }, [port])

  const isOfflineData = plan?.meta?.data_source?.includes('Static baseline') ||
                        plan?.meta?.data_source?.includes('static_baseline')

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="header-logo">⚓</div>
            <div>
              <h1>Container Congestion Predictor</h1>
              <p>Port Operations Optimiser — 72-Hour Planning Dashboard</p>
            </div>
          </div>
          <div className="header-right">
            {plan && <RiskBadge summary={plan.hotspot_summary} />}
            <select
              className="port-select"
              value={port}
              onChange={e => setPort(e.target.value)}
            >
              {PORTS.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <button className="run-btn" onClick={fetchPlan} disabled={loading}>
              {loading
                ? <><span className="spinner-sm" /> Analysing…</>
                : <>▶ Run 72h Plan</>
              }
            </button>
          </div>
        </div>
      </header>

      <main className="app-main" style={{ flex: 1 }}>
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠</span>
            <div><strong>Error:</strong> {error}</div>
          </div>
        )}

        {/* ── Empty state ── */}
        {!plan && !loading && (
          <div className="empty-state">
            <div className="empty-lottie">🚢</div>
            <h2>Select a port and run the 72-hour plan</h2>
            <p>
              Live IMF PortWatch AIS data anchors a calibrated vessel simulation.
              The congestion model flags over-capacity windows before they occur.
            </p>
            <div className="feature-pills">
              {[
                { color: '#4f8ef7', text: 'Live IMF PortWatch API' },
                { color: '#22d3a0', text: 'Congestion Detection' },
                { color: '#a78bfa', text: 'Berth Optimiser' },
                { color: '#f59e0b', text: 'Gemini AI Brief' },
              ].map(f => (
                <div className="feature-pill" key={f.text}>
                  <div className="dot" style={{ background: f.color }} />
                  {f.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Loading ── */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-ring" />
            <p>Fetching IMF PortWatch data & running analysis…</p>
            <small>Calling live AIS API → congestion model → berth optimiser → AI brief</small>
          </div>
        )}

        {/* ── Results ── */}
        {plan && !loading && (
          <div className="fade-in">
            {/* Data source bar */}
            <div className="data-source-bar">
              <div className={`ds-dot ${isOfflineData ? 'offline' : ''}`} />
              <span className="ds-label">Data source:</span>
              <span className="ds-value">{plan.meta.data_source}</span>
              <span style={{ marginLeft: 'auto', color: 'var(--text-3)', fontSize: 11 }}>
                Plan start: {new Date(plan.meta.plan_start).toLocaleString('en-GB', {
                  day: '2-digit', month: 'short', year: 'numeric',
                  hour: '2-digit', minute: '2-digit', hour12: false
                })} UTC
              </span>
            </div>

            {/* Stats row */}
            <div className="stats-row">
              <div className={`stat-card fade-in stagger-1 ${plan.hotspot_summary.high_severity_count > 0 ? 'danger' : plan.hotspot_summary.medium_severity_count > 0 ? 'warn' : 'success'}`}>
                <div className="stat-label">Hotspot Windows</div>
                <div className="stat-value">{plan.hotspot_summary.hotspot_slots}</div>
                <div className="stat-sub">of {plan.hotspot_summary.total_slots} time slots</div>
              </div>
              <div className="stat-card fade-in stagger-2 accent">
                <div className="stat-label">Peak Demand</div>
                <div className="stat-value">{plan.hotspot_summary.max_demand}</div>
                <div className="stat-sub">vessels vs {plan.hotspot_summary.capacity} berths</div>
              </div>
              <div className="stat-card fade-in stagger-3 success">
                <div className="stat-label">Vessels Assigned</div>
                <div className="stat-value">{plan.optimizer_summary.assigned}</div>
                <div className="stat-sub">of {plan.optimizer_summary.total_vessels} total</div>
              </div>
              <div className="stat-card fade-in stagger-4 warn">
                <div className="stat-label">Avg Wait Time</div>
                <div className="stat-value">{plan.optimizer_summary.avg_wait_hours.toFixed(1)}h</div>
                <div className="stat-sub">max {plan.optimizer_summary.max_wait_hours.toFixed(1)}h</div>
              </div>
              <div className="stat-card fade-in stagger-5 purple">
                <div className="stat-label">Daily Calls (real)</div>
                <div className="stat-value">{plan.meta.avg_daily_container_calls_real}</div>
                <div className="stat-sub">14-day avg · IMF AIS</div>
              </div>
            </div>

            {/* Row 1: Congestion chart + Hotspot list */}
            <div className="grid-2col">
              <div className="card fade-in stagger-1">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon blue">📊</div>
                    72-Hour Congestion Forecast
                  </div>
                  <span className="card-badge">{plan.meta.port}</span>
                </div>
                <div className="card-body">
                  <CongestionTimeline
                    slots={plan.congestion_timeline}
                    capacity={plan.hotspot_summary.capacity}
                  />
                </div>
              </div>

              <div className="card fade-in stagger-2">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon orange">🔥</div>
                    Congestion Hotspots
                  </div>
                  <span className="card-badge">{plan.hotspot_summary.hotspot_slots} windows</span>
                </div>
                <div className="card-body">
                  <HotspotList hotspots={plan.hotspot_summary.hotspot_windows} />
                </div>
              </div>
            </div>

            {/* Row 2: Operations brief + Berth utilisation */}
            <div className="grid-2col">
              <div className="card fade-in stagger-3">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon purple">🤖</div>
                    AI Operations Brief
                  </div>
                  <span className="card-badge">Gemini 2.0 Flash</span>
                </div>
                <div className="card-body">
                  <OperationsBrief brief={plan.operations_brief} />
                </div>
              </div>

              <div className="card fade-in stagger-4">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon green">🏗️</div>
                    Berth Utilisation
                  </div>
                  <span className="card-badge">{plan.berths?.length ?? plan.meta.berth_count} berths</span>
                </div>
                <div className="card-body">
                  <BerthUtilisation
                    berths={plan.berths}
                    assignments={plan.assignments}
                    utilization={plan.optimizer_summary.berth_utilization}
                  />
                </div>
              </div>
            </div>

            {/* Row 3: Full assignment table */}
            <div className="card fade-in stagger-5">
              <div className="card-header">
                <div className="card-title">
                  <div className="card-icon blue">⚓</div>
                  Berth &amp; Crane Assignment Schedule
                </div>
                <span className="card-badge">{plan.assignments?.length} vessels</span>
              </div>
              <div className="card-body" style={{ padding: '16px 22px' }}>
                <AssignmentTable assignments={plan.assignments} />
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          IBM BoB AI Innovation Hackathon 2026 · Team ByteBandits ·
          Data: <a href="https://portwatch.imf.org" target="_blank" rel="noreferrer">IMF PortWatch</a>
          &nbsp;· AI: Google Gemini 2.0 Flash · Built with IBM Bob
        </p>
      </footer>
    </div>
  )
}
