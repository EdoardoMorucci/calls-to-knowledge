export interface Call {
  id: number
  title: string | null
  source_app: string
  started_at: string
  ended_at: string | null
  duration_sec: number | null
  status: 'recording' | 'processing' | 'done' | 'error'
  project_id: number | null
  participants: string[]
  recording_trigger: 'auto' | 'manual'
  audio_path: string | null
  summaries?: Array<{ summary: string }>
}

export interface CallDetail extends Call {
  transcript: Transcript | null
  summary: Summary | null
}

export interface Transcript {
  id: number
  call_id: number
  full_text: string
  segments: Segment[]
  language: string
}

export interface Segment {
  start: number
  end: number
  text: string
}

export interface Summary {
  id: number
  call_id: number
  summary: string
  key_points: string[]
  next_steps: string[]
  decisions: string[]
}

export interface Project {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface ProjectDetail extends Project {
  calls: Call[]
  total_calls: number
  total_duration_sec: number
  all_next_steps: Array<{ text: string; call_id: number; started_at: string }>
  all_decisions: Array<{ text: string; call_id: number; started_at: string }>
}

export interface RecordingStatusEvent {
  type: 'recording_status'
  status: 'idle' | 'recording' | 'processing'
  app: string
  duration_sec: number
}

export interface CallReadyEvent {
  type: 'call_ready'
  call_id: number
}

export type WsEvent = RecordingStatusEvent | CallReadyEvent
