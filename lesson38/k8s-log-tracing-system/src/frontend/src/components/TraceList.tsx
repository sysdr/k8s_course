import React from "react";
import { useTraces } from "../hooks/useTraces";

export const TraceList: React.FC = () => {
  const { traces, loading } = useTraces();

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h3 className="text-sm font-semibold text-slate-600 mb-2">Recent Traces</h3>
      {loading && <p className="text-slate-400 italic text-sm">Loading …</p>}
      {!loading && traces.length === 0 && <p className="text-slate-400 italic text-sm">No traces yet</p>}
      <ul className="space-y-1 max-h-40 overflow-y-auto">
        {traces.map((t, i) => (
          <li key={i} className="font-mono text-xs text-blue-600 bg-blue-50 rounded px-2 py-1 truncate">
            {t.trace_id}
          </li>
        ))}
      </ul>
    </div>
  );
};
