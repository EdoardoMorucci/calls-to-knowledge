import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCall, updateCall, deleteCall, exportCall, reprocessCall, getProjects } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString('it-IT', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function fmtDuration(sec: number | null): string {
  if (sec == null) return '—'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${h}h ${m}′`
  return `${m}′ ${s.toString().padStart(2, '0')}″`
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section
      className="rounded-sm p-6 animate-slide-up"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <h2
        className="font-mono text-xs tracking-widest mb-4"
        style={{ color: 'var(--accent)' }}
      >
        {title}
      </h2>
      {children}
    </section>
  )
}

export function CallDetail() {
  const { id } = useParams<{ id: string }>()
  const callId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [transcriptOpen, setTranscriptOpen] = useState(false)

  const { data: call, isLoading, error } = useQuery({
    queryKey: ['call', callId],
    queryFn: () => getCall(callId),
  })

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof updateCall>[1]) => updateCall(callId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['call', callId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteCall(callId),
    onSuccess: () => navigate('/calls'),
  })

  const reprocessMutation = useMutation({
    mutationFn: () => reprocessCall(callId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['call', callId] }),
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
        <span className="font-mono text-xs animate-pulse" style={{ color: 'var(--text-dim)' }}>
          LOADING...
        </span>
      </div>
    )
  }

  if (error || !call) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
        <p className="font-mono text-xs" style={{ color: '#D94F35' }}>NOT FOUND</p>
      </div>
    )
  }

  function handleTitleSave() {
    if (titleDraft.trim() && titleDraft !== call!.title) {
      updateMutation.mutate({ title: titleDraft.trim() })
    }
    setEditingTitle(false)
  }

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
        <Link
          to="/calls"
          className="font-mono text-xs tracking-widest transition-colors"
          style={{ color: 'var(--text-dim)' }}
          onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--accent)')}
          onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'var(--text-dim)')}
        >
          ← ALL CALLS
        </Link>
        <StatusBadge status={call.status} />
      </header>

      <main className="max-w-3xl mx-auto px-8 py-10 space-y-5 animate-fade-in">
        {/* Title */}
        <div className="mb-8">
          {editingTitle ? (
            <input
              autoFocus
              className="font-display text-3xl w-full bg-transparent outline-none border-b-2 pb-1"
              style={{ color: 'var(--text)', borderColor: 'var(--accent)' }}
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={handleTitleSave}
              onKeyDown={(e) => { if (e.key === 'Enter') handleTitleSave() }}
            />
          ) : (
            <h1
              className="font-display text-3xl cursor-text"
              style={{ color: 'var(--text)' }}
              onClick={() => { setTitleDraft(call.title ?? ''); setEditingTitle(true) }}
              title="Click to edit"
            >
              {call.title || <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>Untitled Call #{call.id}</span>}
            </h1>
          )}

          {/* Metadata row */}
          <div
            className="flex flex-wrap gap-5 mt-3 font-mono text-xs"
            style={{ color: 'var(--text-dim)' }}
          >
            <span>{fmtDate(call.started_at)}</span>
            <span style={{ color: 'var(--border)' }}>·</span>
            <span>{fmtDuration(call.duration_sec)}</span>
            <span style={{ color: 'var(--border)' }}>·</span>
            <span>{call.source_app.replace('.exe', '').toUpperCase()}</span>
            <span style={{ color: 'var(--border)' }}>·</span>
            <span>{call.recording_trigger.toUpperCase()}</span>
          </div>
        </div>

        {/* Project assignment */}
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs tracking-widest" style={{ color: 'rgba(155,154,164,0.4)' }}>
            PROJECT
          </span>
          <select
            className="font-mono text-xs px-2 py-1 rounded-sm outline-none appearance-none"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--text-dim)',
            }}
            value={call.project_id ?? ''}
            onChange={(e) =>
              updateMutation.mutate({ project_id: e.target.value ? Number(e.target.value) : undefined })
            }
          >
            <option value="">UNASSIGNED</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name.toUpperCase()}</option>
            ))}
          </select>
          {call.project_id && (
            <Link
              to={`/projects/${call.project_id}`}
              className="font-mono text-xs transition-colors"
              style={{ color: 'var(--accent)' }}
            >
              VIEW PROJECT →
            </Link>
          )}
        </div>

        {/* Audio */}
        {call.audio_path && (
          <Section title="AUDIO">
            <audio
              controls
              src={`/api/calls/${call.id}/audio`}
              className="w-full"
              style={{ accentColor: 'var(--accent)' }}
            />
          </Section>
        )}

        {/* Summary */}
        {call.summary?.summary && (
          <Section title="SUMMARY">
            <p className="font-body text-sm leading-relaxed" style={{ color: 'rgba(240,239,232,0.8)' }}>
              {call.summary.summary}
            </p>
          </Section>
        )}

        {/* Key Points */}
        {(call.summary?.key_points?.length ?? 0) > 0 && (
          <Section title="KEY POINTS">
            <ul className="space-y-2">
              {call.summary!.key_points.map((kp, i) => (
                <li key={i} className="flex gap-3 text-sm" style={{ color: 'rgba(240,239,232,0.8)' }}>
                  <span style={{ color: 'var(--accent)' }} className="shrink-0 mt-0.5">—</span>
                  {kp}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Next Steps */}
        {(call.summary?.next_steps?.length ?? 0) > 0 && (
          <Section title="NEXT STEPS">
            <ul className="space-y-2">
              {call.summary!.next_steps.map((ns, i) => (
                <li key={i} className="flex gap-3 text-sm" style={{ color: 'rgba(240,239,232,0.8)' }}>
                  <span
                    className="shrink-0 mt-0.5 font-mono text-xs"
                    style={{ color: 'rgba(155,154,164,0.4)' }}
                  >
                    ☐
                  </span>
                  {ns}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Decisions */}
        {(call.summary?.decisions?.length ?? 0) > 0 && (
          <Section title="DECISIONS">
            <ul className="space-y-2">
              {call.summary!.decisions.map((d, i) => (
                <li key={i} className="flex gap-3 text-sm" style={{ color: 'rgba(240,239,232,0.8)' }}>
                  <span style={{ color: '#3A9B66' }} className="shrink-0 mt-0.5">✓</span>
                  {d}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Transcript */}
        {call.transcript && (
          <Section title="TRANSCRIPT">
            <button
              className="w-full text-left flex items-center justify-between font-mono text-xs"
              style={{ color: 'var(--text-dim)' }}
              onClick={() => setTranscriptOpen((v) => !v)}
            >
              <span>{transcriptOpen ? 'COLLAPSE' : 'EXPAND FULL TRANSCRIPT'}</span>
              <span style={{ color: 'rgba(155,154,164,0.3)' }}>{transcriptOpen ? '▲' : '▼'}</span>
            </button>
            {transcriptOpen && (
              <p
                className="mt-5 text-sm leading-loose whitespace-pre-wrap font-body"
                style={{ color: 'rgba(240,239,232,0.6)' }}
              >
                {call.transcript.full_text}
              </p>
            )}
          </Section>
        )}

        {/* Actions */}
        <div
          className="flex flex-wrap gap-3 pt-4"
          style={{ borderTop: '1px solid var(--border)' }}
        >
          <button
            onClick={() => exportCall(call.id)}
            className="font-mono text-xs px-4 py-2 rounded-sm transition-colors"
            style={{
              background: 'rgba(200,150,62,0.1)',
              border: '1px solid rgba(200,150,62,0.3)',
              color: 'var(--accent)',
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(200,150,62,0.18)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(200,150,62,0.1)')}
          >
            EXPORT MARKDOWN
          </button>

          {call.status === 'error' && (
            <button
              onClick={() => reprocessMutation.mutate()}
              disabled={reprocessMutation.isPending}
              className="font-mono text-xs px-4 py-2 rounded-sm transition-colors disabled:opacity-40"
              style={{
                background: 'rgba(200,150,62,0.06)',
                border: '1px solid var(--border)',
                color: 'var(--text-dim)',
              }}
            >
              {reprocessMutation.isPending ? 'PROCESSING...' : 'REPROCESS'}
            </button>
          )}

          <button
            onClick={() => { if (confirm('Delete this call permanently?')) deleteMutation.mutate() }}
            className="font-mono text-xs px-4 py-2 rounded-sm transition-colors ml-auto"
            style={{
              background: 'transparent',
              border: '1px solid rgba(122,63,63,0.4)',
              color: 'rgba(217,79,53,0.5)',
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = 'rgba(217,79,53,0.5)'
              el.style.color = '#D94F35'
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = 'rgba(122,63,63,0.4)'
              el.style.color = 'rgba(217,79,53,0.5)'
            }}
          >
            DELETE
          </button>
        </div>
      </main>
    </div>
  )
}
