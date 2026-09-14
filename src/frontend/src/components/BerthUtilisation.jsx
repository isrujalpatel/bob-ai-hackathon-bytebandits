import React from 'react'

export default function BerthUtilisation({ berths, assignments, utilization }) {
  if (!berths?.length) {
    return <div className="chart-empty">No berth data</div>
  }

  const maxCount = Math.max(...Object.values(utilization || {}), 1)

  return (
    <div className="berth-grid">
      {berths.map(b => {
        const count = utilization?.[b.id] || 0
        const pct = Math.round((count / maxCount) * 100)
        const busy = pct > 60

        return (
          <div key={b.id} className="berth-row">
            <div className="berth-name" title={b.name}>
              <span style={{ color: 'var(--text-3)', marginRight: 4 }}>{b.id}</span>
              {b.name}
            </div>
            <div className="berth-bar-track">
              <div
                className={`berth-bar-fill ${busy ? 'busy' : ''}`}
                style={{ width: `${Math.max(pct, 4)}%` }}
              />
            </div>
            <div className="berth-count">
              {count} <span style={{ color: 'var(--text-3)', fontSize: 10 }}>calls</span>
            </div>
          </div>
        )
      })}
      <div style={{ marginTop: 12, padding: '10px 0', borderTop: '1px solid var(--border)', display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ fontSize: 11, color: 'var(--text-2)' }}>
          Max LOA range: <strong style={{ color: 'var(--text)' }}>
            {Math.min(...berths.map(b => b.max_loa_m))}m – {Math.max(...berths.map(b => b.max_loa_m))}m
          </strong>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-2)' }}>
          Total cranes: <strong style={{ color: 'var(--text)' }}>
            {berths.reduce((s, b) => s + b.cranes, 0)}
          </strong>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-2)' }}>
          Berths: <strong style={{ color: 'var(--text)' }}>{berths.length}</strong>
        </div>
      </div>
    </div>
  )
}
