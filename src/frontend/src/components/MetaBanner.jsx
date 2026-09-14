import React from 'react'

export default function MetaBanner({ meta }) {
  if (!meta) return null
  return (
    <div className="meta-banner">
      <div className="meta-item">
        <span className="meta-label">Port</span>
        <span className="meta-value">{meta.port}</span>
      </div>
      <div className="meta-item">
        <span className="meta-label">Plan Start (UTC)</span>
        <span className="meta-value">
          {new Date(meta.plan_start).toLocaleString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric',
            hour: '2-digit', minute: '2-digit', hour12: false,
          })}
        </span>
      </div>
      <div className="meta-item">
        <span className="meta-label">Horizon</span>
        <span className="meta-value">{meta.horizon_hours}h</span>
      </div>
      <div className="meta-item">
        <span className="meta-label">Avg Daily Calls (real)</span>
        <span className="meta-value">{meta.avg_daily_container_calls_real}</span>
      </div>
      <div className="meta-item meta-source">
        <span className="meta-label">Data Source</span>
        <span className="meta-value meta-small">{meta.data_source}</span>
      </div>
    </div>
  )
}
