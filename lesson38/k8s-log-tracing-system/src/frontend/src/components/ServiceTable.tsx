import React from "react";
import { useStats } from "../context/StatsContext";

export const ServiceTable: React.FC = () => {
  const { stats } = useStats();
  const rows = Object.entries(stats.by_service).sort((a, b) => parseInt(b[1], 10) - parseInt(a[1], 10));

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h3 className="text-sm font-semibold text-slate-600 mb-2">Events by Service</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 border-b">
            <th className="pb-1">Service</th>
            <th className="pb-1 text-right">Count</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([svc, count]) => (
            <tr key={svc} className="border-b border-slate-100">
              <td className="py-1 font-mono text-slate-700">{svc}</td>
              <td className="py-1 text-right text-slate-500">{count}</td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={2} className="py-2 text-slate-400 italic">No data yet</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
};
