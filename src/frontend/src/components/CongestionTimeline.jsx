import React, { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Cell,
} from 'recharts'

const SEV_COLOR = {
  NORMAL: '#22d3a0',
  LOW:    '#facc15',
  MEDIUM: '#f59e0b',
  HIGH:   '#f43f5e',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: '#0f1e35',
      border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
    }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: '#e8edf5', fontSize: 11 }}>
        {d.label}
      </div>
      <div style={{ color: '#8b95a8', marginBottom: 2 }}>
        Demand: <strong style={{ color: SEV_COLOR[d.severity] }}>{d.demand}</strong> vessels
      </div>
      <div style={{ color: '#8b95a8', marginBottom: 2 }}>
        Capacity: <strong style={{ color: '#e8edf5' }}>{d.capacity}</strong> berths
      </div>
      <div style={{ color: '#8b95a8' }}>
        Utilisation: <strong style={{ color: '#e8edf5' }}>{d.utilization_pct}%</strong>
      </div>
      <div style={{
        marginTop: 6, display: 'inline-block',
        background: `${SEV_COLOR[d.severity]}18`,
        border: `1px solid ${SEV_COLOR[d.severity]}44`,
        color: SEV_COLOR[d.severity],
        borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 700,
      }}>
        {d.severity}
      </div>
    </div>
  )
}

export default function CongestionTimeline({ slots, capacity }) {
  const data = useMemo(() => {
    if (!slots) return []
    return slots
      .filter((_, i) => i % 2 === 0)
      .map(s => ({
        label: new Date(s.slot_start).toLocaleString('en-US', {
          month: 'short', day: 'numeric',
          hour: '2-digit', minute: '2-digit', hour12: false,
        }),
        demand: s.demand,
        capacity: s.capacity,
        utilization_pct: s.utilization_pct,
        severity: s.severity,
      }))
  }, [slots])

  if (!data.length) return <div className="chart-empty">No data</div>

  return (
    <div>
      <div className="legend-row">
        {Object.entries(SEV_COLOR).map(([k, c]) => (
          <div className="legend-item" key={k}>
            <div className="legend-dot" style={{ background: c }} />
            {k}
          </div>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 52, left: -8 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="label"
            angle={-45}
            textAnchor="end"
            tick={{ fontSize: 9, fill: '#5a6478' }}
            interval={2}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#5a6478' }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <ReferenceLine
            y={capacity}
            stroke="#f43f5e"
            strokeDasharray="5 3"
            strokeWidth={1.5}
            label={{ value: `Cap. ${capacity}`, fill: '#f43f5e', fontSize: 10, fontWeight: 600 }}
          />
          <Bar dataKey="demand" radius={[3, 3, 0, 0]} maxBarSize={18}>
            {data.map((entry, i) => (
              <Cell key={i} fill={SEV_COLOR[entry.severity] || '#64748b'} opacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
