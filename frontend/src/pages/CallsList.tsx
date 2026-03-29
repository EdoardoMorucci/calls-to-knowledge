import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getCalls, getProjects } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { RecordingBadge } from '../components/RecordingBadge'
import { StatusBadge } from '../components/StatusBadge'
import type { WsEvent } from '../types'

function fmtDuration(sec: number | null): string {
  if (sec == null) return '—'
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}′${s.toString().padStart(2, '0')}″`
}

function fmtDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}

export function CallsList() {
  const queryClient = useQueryClient()
  const [projectFilter, setProjectFilter] = useState<number | undefined>()

  const { data: calls = [], isLoading } = useQuery({
    queryKey: ['calls', projectFilter],
    queryFn: () => getCalls(projectFilter),
  })

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  const handleWsEvent = useCallback((event: WsEvent) => {
    if (event.type === 'call_ready') {
      queryClient.invalidateQueries({ queryKey: ['calls'] })
    }
  }, [queryClient])

  const wsState = useWebSocket(handleWsEvent)

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      {/* Topbar */}
      <header
        className="sticky top-0 z-10 flex items-center justify-between px-8 py-4"
        style={{
          background: 'rgba(10,10,11,0.9)',
          borderBottom: '1px solid var(--border)',
          backdropFilter: 'blur(8px)',
        }}
      >
        <div className="flex items-center gap-6">
          <h1 className="font-display text-xl" style={{ color: 'var(--text)' }}>
            Calls to Knowledge
          </h1>
          <span
            className="font-mono text-xs px-2 py-0.5 rounded-sm"
            style={{
              color: 'var(--accent)',
              background: 'rgba(200,150,62,0.1)',
              border: '1px solid rgba(200,150,62,0.2)',
            }}
          >
            {calls.length} RECORD{calls.length !== 1 ? 'S' : ''}
          </span>
        </div>
        <RecordingBadge {...wsState} />
      </header>

      <main className="max-w-6xl mx-auto px-8 py-8">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <select
            className="font-mono text-xs px-3 py-1.5 rounded-sm outline-none appearance-none"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--text-dim)',
            }}
            value={projectFilter ?? ''}
            onChange={(e) => setProjectFilter(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">ALL PROJECTS</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name.toUpperCase()}</option>
            ))}
          </select>
        </div>

        {isLoading ? (
          <p className="font-mono text-xs" style={{ color: 'var(--text-dim)' }}>
            LOADING...
          </p>
        ) : calls.length === 0 ? (
          <div className="text-center py-24">
            <p className="font-display text-2xl italic mb-2" style={{ color: 'var(--text-dim)' }}>
              No recordings yet
            </p>
            <p className="font-mono text-xs" style={{ color: 'rgba(155,154,164,0.4)' }}>
              Start a call to see it appear here
            </p>
          </div>
        ) : (
          <div
            className="rounded-sm overflow-hidden"
            style={{ border: '1px solid var(--border)' }}
          >
            {/* Table header */}
            <div
              className="grid px-5 py-3"
              style={{
                gridTemplateColumns: '1fr 160px 120px 80px 160px 90px',
                background: 'rgba(255,255,255,0.02)',
                borderBottom: '1px solid var(--border)',
              }}
            >
              {['CALL', 'PROJECT', 'SOURCE', 'DUR', 'DATE', 'STATUS'].map((col) => (
                <span
                  key={col}
                  className="font-mono text-xs tracking-widest"
                  style={{ color: 'rgba(155,154,164,0.4)' }}
                >
                  {col}
                </span>
              ))}
            </div>

            {/* Rows */}
            {calls.map((call, i) => {
              const isActive = call.status === 'recording' || call.status === 'processing'
              return (
                <div
                  key={call.id}
                  className="grid px-5 py-4 transition-colors duration-150"
                  style={{
                    gridTemplateColumns: '1fr 160px 120px 80px 160px 90px',
                    borderBottom: i < calls.length - 1 ? '1px solid var(--border)' : 'none',
                    background: isActive ? 'rgba(200,150,62,0.04)' : 'transparent',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.02)'
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background = isActive
                      ? 'rgba(200,150,62,0.04)' : 'transparent'
                  }}
                >
                  {/* Title */}
                  <div className="pr-4 min-w-0">
                    <Link
                      to={`/calls/${call.id}`}
                      className="font-body font-medium text-sm truncate block transition-colors"
                      style={{ color: 'var(--text)' }}
                      onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--accent)')}
                      onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'var(--text)')}
                    >
                      {call.title || `Call #${call.id}`}
                    </Link>
                    {call.summaries?.[0]?.summary && (
                      <p
                        className="text-xs truncate mt-0.5"
                        style={{ color: 'var(--text-dim)' }}
                      >
                        {call.summaries[0].summary}
                      </p>
                    )}
                  </div>

                  {/* Project */}
                  <span className="font-mono text-xs self-center" style={{ color: 'var(--text-dim)' }}>
                    {projects.find((p) => p.id === call.project_id)?.name ?? '—'}
                  </span>

                  {/* Source */}
                  <span className="font-mono text-xs self-center" style={{ color: 'var(--text-dim)' }}>
                    {call.source_app.replace('.exe', '').toUpperCase()}
                  </span>

                  {/* Duration */}
                  <span className="font-mono text-xs self-center" style={{ color: 'var(--text-dim)' }}>
                    {fmtDuration(call.duration_sec)}
                  </span>

                  {/* Date */}
                  <span className="font-mono text-xs self-center" style={{ color: 'rgba(155,154,164,0.5)' }}>
                    {fmtDate(call.started_at)}
                  </span>

                  {/* Status */}
                  <div className="self-center">
                    <StatusBadge status={call.status} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
