import React from 'react'

export default function OperationsBrief({ brief }) {
  if (!brief) return <div className="chart-empty">No brief generated</div>

  // Strip markdown bold/italic from Gemini output
  const clean = brief
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')

  const lines = clean.split('\n')
  let sectionNum = 0

  return (
    <div className="brief-wrap">
      {lines.map((line, i) => {
        const trimmed = line.trim()
        if (!trimmed) return <div key={i} className="brief-spacer" />

        // Title line (e.g. "72-HOUR PORT OPERATIONS BRIEF")
        if (i === 0 || /^72-HOUR|^PORT OPERATIONS|^OPERATIONS BRIEF/i.test(trimmed)) {
          return <div key={i} className="brief-title">{trimmed}</div>
        }

        // Numbered sections: "1. BOTTOM LINE" or "1. Bottom Line"
        const sectionMatch = trimmed.match(/^(\d+)\.\s+(.+)$/)
        if (sectionMatch && trimmed.length < 60 && /^[A-Z0-9]/.test(sectionMatch[2])) {
          sectionNum = parseInt(sectionMatch[1])
          return (
            <div key={i} className="brief-section">
              <div className="brief-section-num">{sectionMatch[1]}</div>
              {sectionMatch[2]}
            </div>
          )
        }

        // Bullet / list items
        if (/^[-•*]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed)) {
          return <p key={i} className="brief-bullet">{trimmed.replace(/^[-•*\d.]\s*/, '')}</p>
        }

        // Indented
        if (line.startsWith('   ') || line.startsWith('\t')) {
          return <p key={i} className="brief-indent">{trimmed}</p>
        }

        return <p key={i} className="brief-line">{trimmed}</p>
      })}
    </div>
  )
}
