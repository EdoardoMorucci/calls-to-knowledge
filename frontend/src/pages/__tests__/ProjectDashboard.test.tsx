import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProjectDashboard } from '../ProjectDashboard'
import * as client from '../../api/client'

vi.mock('../../api/client')

const SAMPLE_PROJECT = {
  id: 1, name: 'Progetto Alpha', description: 'Descrizione di test',
  created_at: '2026-03-01T00:00:00Z',
  calls: [{
    id: 1, title: 'Standup', source_app: 'Teams.exe',
    started_at: '2026-03-30T09:00:00Z', status: 'done',
    project_id: 1, duration_sec: 600,
  }],
  total_calls: 1,
  total_duration_sec: 600,
  all_next_steps: [{ text: 'Marco: PR auth', call_id: 1, started_at: '2026-03-30T09:00:00Z' }],
  all_decisions: [{ text: 'Usare Supabase', call_id: 1, started_at: '2026-03-30T09:00:00Z' }],
}

function renderWithProviders() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/projects/1']}>
        <Routes><Route path="/projects/:id" element={<ProjectDashboard />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(client.getProject).mockResolvedValue(SAMPLE_PROJECT as any)
})

describe('ProjectDashboard', () => {
  it('mostra il nome del progetto', async () => {
    renderWithProviders()
    expect(await screen.findByText('Progetto Alpha')).toBeInTheDocument()
  })

  it('mostra le stat card con i counter', async () => {
    renderWithProviders()
    expect(await screen.findByText('CALLS')).toBeInTheDocument()
    expect(await screen.findByText('NEXT STEPS')).toBeInTheDocument()
    expect(await screen.findByText('DECISIONS')).toBeInTheDocument()
  })

  it('mostra i next steps', async () => {
    renderWithProviders()
    expect(await screen.findByText('Marco: PR auth')).toBeInTheDocument()
  })

  it('mostra le decisioni', async () => {
    renderWithProviders()
    expect(await screen.findByText('Usare Supabase')).toBeInTheDocument()
  })

  it('lista le chiamate del progetto', async () => {
    renderWithProviders()
    expect(await screen.findByText('Standup')).toBeInTheDocument()
  })
})
