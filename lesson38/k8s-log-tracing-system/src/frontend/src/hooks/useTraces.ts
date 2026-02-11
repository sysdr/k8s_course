import { useState, useEffect } from "react";

interface TraceEntry {
  trace_id: string;
}

export function useTraces(pollMs = 5000) {
  const [traces, setTraces] = useState<TraceEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const fetch_ = async () => {
      try {
        const res = await fetch("/api/analytics/recent-traces");
        if (res.ok) {
          const data = await res.json();
          if (active) setTraces(data.traces || []);
        }
      } catch {}
      if (active) setLoading(false);
    };
    fetch_();
    const interval = setInterval(fetch_, pollMs);
    return () => { active = false; clearInterval(interval); };
  }, [pollMs]);

  return { traces, loading };
}
