import React from "react";
import { StatsProvider, useStats } from "./context/StatsContext";
import { SeverityChart } from "./components/SeverityChart";
import { ServiceTable }  from "./components/ServiceTable";
import { TraceList }     from "./components/TraceList";

const Dashboard: React.FC = () => {
  const { connected } = useStats();
  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-slate-800">⬡ Log Tracing Dashboard</h1>
        <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-100 text-green-700">
          ● Connected
        </span>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2"><SeverityChart /></div>
        <div><TraceList /></div>
        <div className="md:col-span-3"><ServiceTable /></div>
      </div>
    </div>
  );
};

export default function App() {
  return <StatsProvider><Dashboard /></StatsProvider>;
}
