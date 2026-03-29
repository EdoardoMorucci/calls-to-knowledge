import type { Call, CallDetail, Project, ProjectDetail } from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  if (res.status === 204) return undefined as T
  return res.json()
}

export function getCalls(projectId?: number, limit = 50, offset = 0): Promise<Call[]> {
  const params = new URLSearchParams()
  if (projectId != null) params.set('project_id', String(projectId))
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  return request(`/calls?${params}`)
}

export function getCall(id: number): Promise<CallDetail> {
  return request(`/calls/${id}`)
}

export function updateCall(
  id: number,
  data: { title?: string; project_id?: number; participants?: string[] },
): Promise<{ ok: boolean }> {
  return request(`/calls/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function deleteCall(id: number): Promise<void> {
  return request(`/calls/${id}`, { method: 'DELETE' })
}

export function reprocessCall(id: number): Promise<{ ok: boolean }> {
  return request(`/calls/${id}/reprocess`, { method: 'POST' })
}

export async function exportCall(id: number): Promise<void> {
  const res = await fetch(`${BASE}/calls/${id}/export`)
  if (!res.ok) throw new Error(`${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `call-${id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

export function getProjects(): Promise<Project[]> {
  return request('/projects')
}

export function createProject(name: string, description?: string): Promise<Project> {
  return request('/projects', { method: 'POST', body: JSON.stringify({ name, description }) })
}

export function getProject(id: number): Promise<ProjectDetail> {
  return request(`/projects/${id}`)
}

export function startRecording(): Promise<{ ok: boolean }> {
  return request('/recording/start', { method: 'POST' })
}

export function stopRecording(): Promise<{ ok: boolean }> {
  return request('/recording/stop', { method: 'POST' })
}
