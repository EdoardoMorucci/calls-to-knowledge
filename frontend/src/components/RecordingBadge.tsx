import type { WebSocketState } from '../hooks/useWebSocket'

function pad(n: number) { return n.toString().padStart(2, '0') }

function formatDuration(sec: number): string {
  return `${pad(Math.floor(sec / 60))}:${pad(sec % 60)}`
}

export function RecordingBadge({ status, app, durationSec }: WebSocketState) {
  if (status === 'idle') return null

  const isRecording = status === 'recording'
  const label = isRecording
    ? (app ? app.replace('.exe', '').toUpperCase() : 'REC')
    : 'PROCESSING'

  return (
    <div
      className="flex items-center gap-2.5 px-3 py-1.5 rounded-sm border animate-fade-in"
      style={{
        borderColor: isRecording ? 'rgba(217,79,53,0.4)' : 'rgba(200,150,62,0.4)',
        background: isRecording ? 'rgba(217,79,53,0.08)' : 'rgba(200,150,62,0.08)',
      }}
    >
      {/* Live dot — ping when recording, static when processing */}
      <span className="relative flex h-2 w-2 shrink-0">
        {isRecording && (
          <span
            className="absolute inline-flex h-full w-full rounded-full animate-ping"
            style={{ backgroundColor: '#D94F35', opacity: 0.5 }}
          />
        )}
        <span
          className="relative inline-flex h-2 w-2 rounded-full"
          style={{ backgroundColor: isRecording ? '#D94F35' : '#C8963E' }}
        />
      </span>

      {/* Label */}
      <span
        className="font-mono text-xs tracking-widest"
        style={{ color: isRecording ? '#D94F35' : '#C8963E' }}
      >
        {label}
      </span>

      {/* Timer */}
      {isRecording && (
        <span className="font-mono text-xs" style={{ color: 'rgba(240,239,232,0.4)' }}>
          {formatDuration(durationSec)}
        </span>
      )}
    </div>
  )
}
