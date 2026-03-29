import { useEffect, useRef, useState } from 'react'
import type { WsEvent, RecordingStatusEvent } from '../types'

export interface WebSocketState {
  status: RecordingStatusEvent['status']
  app: string
  durationSec: number
}

export function useWebSocket(onEvent: (event: WsEvent) => void): WebSocketState {
  const [wsState, setWsState] = useState<WebSocketState>({
    status: 'idle',
    app: '',
    durationSec: 0,
  })
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>
    let ws: WebSocket

    function connect() {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      ws = new WebSocket(`${proto}//${window.location.host}/ws`)

      ws.onmessage = (e: MessageEvent) => {
        const event: WsEvent = JSON.parse(e.data as string)
        if (event.type === 'recording_status') {
          setWsState({
            status: event.status,
            app: event.app,
            durationSec: event.duration_sec,
          })
        }
        onEventRef.current(event)
      }

      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    connect()
    return () => {
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [])

  return wsState
}
