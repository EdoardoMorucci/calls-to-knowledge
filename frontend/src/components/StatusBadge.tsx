const CONFIG: Record<string, { label: string; dot: string; text: string }> = {
  done:       { label: 'DONE',        dot: '#3A9B66', text: 'rgba(58,155,102,0.7)' },
  recording:  { label: 'REC',         dot: '#D94F35', text: 'rgba(217,79,53,0.8)' },
  processing: { label: 'PROCESSING',  dot: '#C8963E', text: 'rgba(200,150,62,0.8)' },
  error:      { label: 'ERROR',       dot: '#7A3F3F', text: 'rgba(122,63,63,0.7)' },
}

export function StatusBadge({ status }: { status: string }) {
  const cfg = CONFIG[status] ?? CONFIG.error
  const isRec = status === 'recording'

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="relative flex h-1.5 w-1.5 shrink-0">
        {isRec && (
          <span
            className="absolute inline-flex h-full w-full rounded-full animate-ping opacity-60"
            style={{ backgroundColor: cfg.dot }}
          />
        )}
        <span
          className="relative inline-flex h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: cfg.dot }}
        />
      </span>
      <span className="font-mono text-xs tracking-widest" style={{ color: cfg.text }}>
        {cfg.label}
      </span>
    </span>
  )
}
