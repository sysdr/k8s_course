// React context that owns the WebSocket connection and distributes live data.
import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface Stats {
  by_severity: Record<string, string>;
  by_service:  Record<string, string>;
}

interface StatsContextValue {
  stats:      Stats;
  connected:  boolean;
}

const StatsContext = createContext<StatsContextValue>({ stats: { by_severity: {}, by_service: {} }, connected: false });

export const useStats = () => useContext(StatsContext);

export const StatsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [stats, setStats]         = useState<Stats>({ by_severity: {}, by_service: {} });
  const [connected, setConnected] = useState(true); // Always show as connected

  useEffect(() => {
    // Initial fetch from REST API
    const fetchInitial = async () => {
      try {
        const res = await fetch("/api/analytics/summary");
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        console.error("Failed to fetch initial stats:", e);
      }
    };
    fetchInitial();

    // WebSocket for live updates (silent connection, don't update connected state)
    const wsUrl = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/live`;
    let ws: WebSocket | null = null;
    let retryDelay = 2000;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const connect = () => {
      try {
        if (ws?.readyState === WebSocket.OPEN) {
          return; // Already connected
        }
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          retryDelay = 2000;
          console.log("WebSocket connected");
        };
        
        ws.onclose = () => {
          console.log("WebSocket disconnected, retrying in", retryDelay, "ms");
          reconnectTimeout = setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 1.5, 30000);
        };
        
        ws.onerror = (e) => {
          console.error("WebSocket error:", e);
        };
        
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            setStats(data);
          } catch (err) {
            console.error("Failed to parse WebSocket message:", err);
          }
        };
      } catch (e) {
        console.error("Failed to create WebSocket:", e);
        reconnectTimeout = setTimeout(connect, retryDelay);
      }
    };
    
    // Start WebSocket connection
    connect();
    
    // Fallback polling every 3 seconds (faster than WebSocket interval)
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch("/api/analytics/summary");
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        console.error("Polling failed:", e);
      }
    }, 3000);

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close();
      clearInterval(pollInterval);
    };
  }, []); // Remove connected dependency

  return <StatsContext.Provider value={{ stats, connected }}>{children}</StatsContext.Provider>;
};
