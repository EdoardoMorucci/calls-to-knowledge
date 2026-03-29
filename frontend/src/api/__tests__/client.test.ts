import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getCalls, getCall, updateCall, getProjects } from '../client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function mockResponse(data: unknown, status = 200) {
  mockFetch.mockResolvedValueOnce({
    ok: status < 400,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(data),
  })
}

beforeEach(() => mockFetch.mockReset())

describe('getCalls', () => {
  it('calls /api/calls', async () => {
    mockResponse([{ id: 1 }])
    const result = await getCalls()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/calls'),
      expect.any(Object),
    )
    expect(result).toEqual([{ id: 1 }])
  })

  it('includes project_id filter when provided', async () => {
    mockResponse([])
    await getCalls(42)
    const url: string = mockFetch.mock.calls[0][0]
    expect(url).toContain('project_id=42')
  })
})

describe('getCall', () => {
  it('calls /api/calls/:id', async () => {
    mockResponse({ id: 7, title: 'Standup' })
    const result = await getCall(7)
    expect(mockFetch).toHaveBeenCalledWith('/api/calls/7', expect.any(Object))
    expect(result.title).toBe('Standup')
  })
})

describe('updateCall', () => {
  it('sends PATCH with body', async () => {
    mockResponse({ ok: true })
    await updateCall(1, { title: 'Nuovo titolo' })
    const [, init] = mockFetch.mock.calls[0]
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body)).toEqual({ title: 'Nuovo titolo' })
  })
})

describe('getProjects', () => {
  it('returns project list', async () => {
    mockResponse([{ id: 1, name: 'Alpha' }])
    const result = await getProjects()
    expect(result[0].name).toBe('Alpha')
  })
})
