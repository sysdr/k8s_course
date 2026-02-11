import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useStats } from "../context/StatsContext";

const COLORS: Record<string, string> = {
  DEBUG: "#60a5fa",
  INFO:  "#34d399",
  WARN:  "#fbbf24",
  ERROR: "#f87171",
  FATAL: "#a78bfa",
};

export const SeverityChart: React.FC = () => {
  const { stats } = useStats();
  const data = Object.entries(stats.by_severity).map(([name, count]) => ({
    name,
    count: parseInt(count, 10),
  }));

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h3 className="text-sm font-semibold text-slate-600 mb-2">Events by Severity</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="count" radius={[4,4,0,0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name] || "#94a3b8"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
