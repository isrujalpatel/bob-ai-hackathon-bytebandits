import React from 'react'

export default function HotspotList({ hotspots }) {
  if (!hotspots?.length) {
    return (
      <div style={{ textAlign: 'center', color: 'var(--success)', padding: '32px 0' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
        <div style={{ fontWeight: 600, fontSize: 14 }}>No congestion hotspots predicted</div>
        <div style={{ color: 'var(--text-3)', fontSize: 12, marginTop: 4 }}>All time slots within berth capacity</div>
      </div>
    )
  }

  return (
    <div className="hotspot-list" style={{ maxHeight: 300, overflowY: 'auto' }}>
      {hotspots.map((h, i) => {
        const start = new Date(h.start)
        const end = new Date(h.end)
        const fmtTime = (d) => d.toLocaleString('en-GB', {
          day: '2-digit', month: 'short',
          hour: '2-digit', minute: '2-digit', hour12: false,
        })
        return (
          <div key={i} className="hotspot-item">
            <span className={`sev-badge ${h.severity}`}>{h.severity}</span>
            <div>
              <div className="hotspot-time">{fmtTime(start)}</div>
              <div className="hotspot-time" style={{ opacity: 0.6 }}>→ {fmtTime(end)}</div>
            </div>
            <div className="hotspot-demand">
              {h.demand} <span>vessels</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
