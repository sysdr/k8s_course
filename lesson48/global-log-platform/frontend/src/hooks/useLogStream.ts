import { useEffect, useRef, useState } from 'react';

export interface LogEvent {
  service:   string;
  level:     'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL';
  message:   string;
  timestamp: number;
  trace_id?: string;
  region:    string;
}

export interface StreamState {
  events:      LogEvent[];
  connected:   boolean;
  error:       string | null;
  regionStats: Record<string, number>;
}

const WS_URL = import.meta.env.VITE_AGGREGATOR_WS ?? 'ws://localhost:8001/ws/logs';
const MAX_EVENTS = 500;

export function useLogStream(): StreamState {
  const [state, setState] = useState<StreamState>({
    events: [], connected: false, error: null, regionStats: {},
  });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setState(s => ({ ...s, connected: true, error: null }));
        const ping = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 30_000);
        ws.addEventListener('close', () => clearInterval(ping));
      };

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data as string);
          const incoming: LogEvent[] = data.events ?? [];
          setState(s => {
            const merged = [...incoming, ...s.events].slice(0, MAX_EVENTS);
            const stats = merged.reduce<Record<string, number>>((acc, e) => {
              acc[e.region] = (acc[e.region] ?? 0) + 1;
              return acc;
            }, {});
            return { ...s, events: merged, regionStats: stats };
          });
        } catch (e) { /* ignore malformed frame */ }
      };

      ws.onerror = () => setState(s => ({ ...s, error: 'WebSocket error' }));
      ws.onclose = () => {
        setState(s => ({ ...s, connected: false }));
        reconnectTimer = setTimeout(connect, 3_000);
      };
    };

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return state;
}
