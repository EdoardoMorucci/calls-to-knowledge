import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CallsList } from '../CallsList'
import * as client from '../../api/client'

vi.mock('../../api/client')
vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({ status: 'idle', app: '', durationSec: 0 }),
}))

const SAMPLE_CALL = {
  id: 1, title: 'Standup mattutino', source_app: 'Teams.exe',
  started_at: '2026-03-30T09:00:00Z', ended_at: null,
  duration_sec: 600, status: 'done', project_id: null,
  participants: [], recording_trigger: 'auto', audio_path: null,
  summaries: [{ summary: 'Discusso roadmap Q2' }],
}

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}><MemoryRouter>{ui}</MemoryRouter></QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(client.getCalls).mockResolvedValue([SAMPLE_CALL] as any)
  vi.mocked(client.getProjects).mockResolvedValue([])
})

describe('CallsList', () => {
  it('mostra il titolo della chiamata', async () => {
    renderWithProviders(<CallsList />)
    expect(await screen.findByText('Standup mattutino')).toBeInTheDocument()
  })

  it('mostra il badge dei record count', async () => {
    renderWithProviders(<CallsList />)
    expect(await screen.findByText('1 RECORD')).toBeInTheDocument()
  })

  it('mostra il messaggio empty state', async () => {
    vi.mocked(client.getCalls).mockResolvedValue([])
    renderWithProviders(<CallsList />)
    expect(await screen.findByText(/No recordings yet/)).toBeInTheDocument()
  })

  it('mostra il badge di stato', async () => {
    renderWithProviders(<CallsList />)
    expect(await screen.findByText('DONE')).toBeInTheDocument()
  })
})
