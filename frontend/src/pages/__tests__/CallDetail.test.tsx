import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CallDetail } from '../CallDetail'
import * as client from '../../api/client'

vi.mock('../../api/client')

const SAMPLE = {
  id: 1, title: 'Standup Q2', source_app: 'Teams.exe',
  started_at: '2026-03-30T09:00:00Z', ended_at: '2026-03-30T09:30:00Z',
  duration_sec: 1800, status: 'done', project_id: null,
  participants: [], recording_trigger: 'auto', audio_path: null,
  transcript: { id: 1, call_id: 1, full_text: 'Ciao a tutti.', segments: [], language: 'it' },
  summary: {
    id: 1, call_id: 1,
    summary: 'Discusso roadmap.',
    key_points: ['Roadmap approvata'],
    next_steps: ['Marco: PR auth'],
    decisions: ['Usare Supabase'],
  },
}

function renderWithProviders() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/calls/1']}>
        <Routes><Route path="/calls/:id" element={<CallDetail />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(client.getCall).mockResolvedValue(SAMPLE as any)
  vi.mocked(client.getProjects).mockResolvedValue([])
})

describe('CallDetail', () => {
  it('mostra il titolo', async () => {
    renderWithProviders()
    expect(await screen.findByText('Standup Q2')).toBeInTheDocument()
  })

  it('mostra il summary', async () => {
    renderWithProviders()
    expect(await screen.findByText('Discusso roadmap.')).toBeInTheDocument()
  })

  it('mostra key points e next steps', async () => {
    renderWithProviders()
    expect(await screen.findByText('Roadmap approvata')).toBeInTheDocument()
    expect(await screen.findByText('Marco: PR auth')).toBeInTheDocument()
  })

  it('espande la trascrizione al click', async () => {
    renderWithProviders()
    const btn = await screen.findByText('EXPAND FULL TRANSCRIPT')
    fireEvent.click(btn)
    expect(screen.getByText('Ciao a tutti.')).toBeInTheDocument()
  })
})
