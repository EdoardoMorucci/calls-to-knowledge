import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProject } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'

function fmtHours(sec: number): string {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString('it-IT', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

function StatCard({ value, label }: { value: number | string; label: string }) {
  return (
    <div
      className="rounded-sm p-6 text-center"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <p className="font-display text-4xl mb-1" style={{ color: 'var(--text)' }}>
        {value}
      </p>
      <p className="font-mono text-xs tracking-widest" style={{ color: 'rgba(155,154,164,0.5)' }}>
        {label}
      </p>
    </div>
  )
}

export function ProjectDashboard() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
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

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
        <p className="font-mono text-xs" style={{ color: '#D94F35' }}>PROJECT NOT FOUND</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen animate-fade-in" style={{ background: 'var(--bg)' }}>
      {/* Topbar */}
      <header
        className="sticky top-0 z-10 flex items-center gap-6 px-8 py-4"
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
        <span style={{ color: 'var(--border)' }}>·</span>
        <h1 className="font-display text-lg" style={{ color: 'var(--text)' }}>
          {project.name}
        </h1>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-10 space-y-8">
        {/* Description */}
        {project.description && (
          <p className="font-body text-sm" style={{ color: 'var(--text-dim)' }}>
            {project.description}
          </p>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard value={project.total_calls} label="CALLS" />
          <StatCard value={project.all_next_steps.length} label="NEXT STEPS" />
          <StatCard value={project.all_decisions.length} label="DECISIONS" />
        </div>

        {/* Total time */}
        <p
          className="font-mono text-xs"
          style={{ color: 'rgba(155,154,164,0.4)' }}
        >
          TOTAL RECORDED TIME:{' '}
          <span style={{ color: 'var(--accent)' }}>{fmtHours(project.total_duration_sec)}</span>
        </p>

        {/* Next Steps */}
        {project.all_next_steps.length > 0 && (
          <section>
            <h2
              className="font-mono text-xs tracking-widest mb-4"
              style={{ color: 'var(--accent)' }}
            >
              ALL NEXT STEPS
            </h2>
            <div
              className="rounded-sm divide-y"
              style={{ border: '1px solid var(--border)', divideColor: 'var(--border)' }}
            >
              {project.all_next_steps.map((ns, i) => (
                <div
                  key={i}
                  className="flex items-start gap-4 px-5 py-3.5"
                  style={{ background: 'var(--surface)' }}
                >
                  <span
                    className="font-mono text-xs shrink-0 mt-0.5"
                    style={{ color: 'rgba(155,154,164,0.3)' }}
                  >
                    ☐
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm" style={{ color: 'rgba(240,239,232,0.8)' }}>
                      {ns.text}
                    </p>
                  </div>
                  <Link
                    to={`/calls/${ns.call_id}`}
                    className="font-mono text-xs shrink-0 transition-colors"
                    style={{ color: 'rgba(155,154,164,0.3)' }}
                    onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--accent)')}
                    onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'rgba(155,154,164,0.3)')}
                  >
                    {fmtDate(ns.started_at)} →
                  </Link>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Decisions */}
        {project.all_decisions.length > 0 && (
          <section>
            <h2
              className="font-mono text-xs tracking-widest mb-4"
              style={{ color: '#3A9B66' }}
            >
              ALL DECISIONS
            </h2>
            <div
              className="rounded-sm divide-y"
              style={{ border: '1px solid var(--border)' }}
            >
              {project.all_decisions.map((d, i) => (
                <div
                  key={i}
                  className="flex items-start gap-4 px-5 py-3.5"
                  style={{ background: 'var(--surface)' }}
                >
                  <span className="font-mono text-xs shrink-0 mt-0.5" style={{ color: '#3A9B66' }}>
                    ✓
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm" style={{ color: 'rgba(240,239,232,0.8)' }}>
                      {d.text}
                    </p>
                  </div>
                  <Link
                    to={`/calls/${d.call_id}`}
                    className="font-mono text-xs shrink-0 transition-colors"
                    style={{ color: 'rgba(155,154,164,0.3)' }}
                    onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--accent)')}
                    onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'rgba(155,154,164,0.3)')}
                  >
                    {fmtDate(d.started_at)} →
                  </Link>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Calls list */}
        <section>
          <h2
            className="font-mono text-xs tracking-widest mb-4"
            style={{ color: 'rgba(155,154,164,0.4)' }}
          >
            CALLS IN THIS PROJECT
          </h2>
          {project.calls.length === 0 ? (
            <p
              className="font-mono text-xs"
              style={{ color: 'rgba(155,154,164,0.3)' }}
            >
              NO CALLS ASSIGNED YET
            </p>
          ) : (
            <div
              className="rounded-sm divide-y"
              style={{ border: '1px solid var(--border)' }}
            >
              {project.calls.map((call) => (
                <div
                  key={call.id}
                  className="flex items-center justify-between px-5 py-3.5 transition-colors"
                  style={{ background: 'var(--surface)' }}
                >
                  <div>
                    <Link
                      to={`/calls/${call.id}`}
                      className="font-body text-sm font-medium transition-colors"
                      style={{ color: 'var(--text)' }}
                      onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--accent)')}
                      onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'var(--text)')}
                    >
                      {call.title || `Call #${call.id}`}
                    </Link>
                    <p className="font-mono text-xs mt-0.5" style={{ color: 'rgba(155,154,164,0.4)' }}>
                      {fmtDate(call.started_at)} · {call.source_app.replace('.exe', '').toUpperCase()}
                    </p>
                  </div>
                  <StatusBadge status={call.status} />
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
