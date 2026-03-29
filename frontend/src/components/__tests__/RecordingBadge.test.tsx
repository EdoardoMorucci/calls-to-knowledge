import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecordingBadge } from '../RecordingBadge'

describe('RecordingBadge', () => {
  it('non renderizza nulla in stato idle', () => {
    const { container } = render(
      <RecordingBadge status="idle" app="" durationSec={0} />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('mostra app name in uppercase e timer in stato recording', () => {
    render(<RecordingBadge status="recording" app="Teams.exe" durationSec={90} />)
    expect(screen.getByText('TEAMS')).toBeInTheDocument()
    expect(screen.getByText('01:30')).toBeInTheDocument()
  })

  it('mostra PROCESSING in stato processing senza timer', () => {
    render(<RecordingBadge status="processing" app="" durationSec={0} />)
    expect(screen.getByText('PROCESSING')).toBeInTheDocument()
    expect(screen.queryByText(/:/)).toBeNull()
  })

  it('usa REC come fallback se app è stringa vuota', () => {
    render(<RecordingBadge status="recording" app="" durationSec={5} />)
    expect(screen.getByText('REC')).toBeInTheDocument()
  })
})
