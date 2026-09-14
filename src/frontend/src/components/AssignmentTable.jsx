import React, { useState } from 'react'

const fmt = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit', hour12: false,
  })
}

const STATUS_MAP = {
  ASSIGNED:           { cls: 'assigned',   label: 'Assigned' },
  RESCHEDULE_ADVISED: { cls: 'reschedule', label: 'Reschedule' },
  REROUTE_RECOMMENDED:{ cls: 'reroute',    label: 'Reroute' },
}

const COLS = [
  { key: 'vessel_id',       label: 'ID' },
  { key: 'vessel_name',     label: 'Vessel' },
  { key: 'shipping_line',   label: 'Line' },
  { key: 'vessel_class',    label: 'Class' },
  { key: 'teu',             label: 'TEU' },
  { key: 'origin',          label: 'Origin' },
  { key: 'eta',             label: 'ETA' },
  { key: 'berth_name',      label: 'Berth' },
  { key: 'cranes_assigned', label: 'Cranes' },
  { key: 'scheduled_start', label: 'Start' },
  { key: 'scheduled_end',   label: 'End' },
  { key: 'wait_hours',      label: 'Wait' },
  { key: 'status',          label: 'Status' },
]

export default function AssignmentTable({ assignments }) {
  const [sortKey, setSortKey] = useState('scheduled_start')
  const [sortDir, setSortDir] = useState(1)
  const [filter, setFilter] = useState('ALL')

  if (!assignments?.length) return <div className="chart-empty">No assignments</div>

  const setSort = (key) => {
    if (sortKey === key) setSortDir(d => -d)
    else { setSortKey(key); setSortDir(1) }
  }

  const filtered = filter === 'ALL' ? assignments
    : assignments.filter(a => a.status === filter)

  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey]
    if (av == null) return 1
    if (bv == null) return -1
    return av < bv ? -sortDir : av > bv ? sortDir : 0
  })

  const counts = {
    ALL: assignments.length,
    ASSIGNED: assignments.filter(a => a.status === 'ASSIGNED').length,
    RESCHEDULE_ADVISED: assignments.filter(a => a.status === 'RESCHEDULE_ADVISED').length,
    REROUTE_RECOMMENDED: assignments.filter(a => a.status === 'REROUTE_RECOMMENDED').length,
  }

  return (
    <div>
      <div className="table-controls">
        <div className="filter-tabs">
          {[
            { key: 'ALL',                val: 'All', cls: 'all' },
            { key: 'ASSIGNED',           val: 'Assigned', cls: 'ok' },
            { key: 'RESCHEDULE_ADVISED', val: 'Reschedule', cls: 'warn' },
            { key: 'REROUTE_RECOMMENDED',val: 'Reroute', cls: 'danger' },
          ].map(f => (
            <button
              key={f.key}
              className={`filter-tab ${filter === f.key ? `active ${f.cls}` : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.val} <span style={{ opacity: 0.7 }}>({counts[f.key]})</span>
            </button>
          ))}
        </div>
        <span className="table-count">{sorted.length} vessels shown</span>
      </div>

      <div className="table-scroll">
        <table className="vessel-table">
          <thead>
            <tr>
              {COLS.map(col => (
                <th
                  key={col.key}
                  className={sortKey === col.key ? 'sorted' : ''}
                  onClick={() => setSort(col.key)}
                >
                  {col.label}
                  {sortKey === col.key && (
                    <span className="sort-arrow">{sortDir > 0 ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(row => {
              const st = STATUS_MAP[row.status] || { cls: '', label: row.status }
              return (
                <tr key={row.vessel_id}>
                  <td className="cell-id">{row.vessel_id}</td>
                  <td className="cell-name">{row.vessel_name}</td>
                  <td style={{ color: 'var(--text-2)' }}>{row.shipping_line}</td>
                  <td><span className="vessel-class-pill">{row.vessel_class}</span></td>
                  <td className="cell-num">{row.teu?.toLocaleString()}</td>
                  <td style={{ color: 'var(--text-2)' }}>{row.origin}</td>
                  <td className="cell-time">{fmt(row.eta)}</td>
                  <td style={{ color: 'var(--text)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {row.berth_name}
                  </td>
                  <td className="cell-num">{row.cranes_assigned || '—'}</td>
                  <td className="cell-time">{fmt(row.scheduled_start)}</td>
                  <td className="cell-time">{fmt(row.scheduled_end)}</td>
                  <td className="cell-num">
                    {row.wait_hours != null ? `${row.wait_hours.toFixed(1)}h` : '—'}
                  </td>
                  <td>
                    <span className={`status-chip ${st.cls}`}>{st.label}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
