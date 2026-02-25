import React, { useMemo, useState } from 'react';
import { useLogStream } from '../hooks/useLogStream';

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: '#64748b', INFO: '#22c55e', WARN: '#f59e0b', ERROR: '#ef4444', FATAL: '#a855f7',
};

const Badge: React.FC<{ label: string; color: string }> = ({ label, color }) => (
  <span style={{
    background: color + '22', color, border: `1px solid ${color}55`,
    borderRadius: 6, padding: '1px 8px', fontSize: 11, fontWeight: 700,
  }}>
    {label}
  </span>
);

export const LogDashboard: React.FC = () => {
  const { events, connected, error, regionStats } = useLogStream();
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [search, setSearch]           = useState('');

  const filtered = useMemo(() =>
    events.filter(e =>
      (levelFilter === 'ALL' || e.level === levelFilter) &&
      (!search || e.message.toLowerCase().includes(search.toLowerCase()) ||
                  e.service.toLowerCase().includes(search.toLowerCase()))
    ), [events, levelFilter, search]);

  return (
    <div style={{ color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#f8fafc' }}>
          🌍 Global Log Platform
        </h1>
        <Badge label={connected ? '● LIVE' : '○ RECONNECTING'} color={connected ? '#22c55e' : '#f59e0b'} />
        {error && <Badge label={error} color="#ef4444" />}
      </div>

      {/* Region stats */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        {Object.entries(regionStats).map(([region, count]) => (
          <div key={region} style={{
            background: '#1e293b', border: '1px solid #334155',
            borderRadius: 10, padding: '8px 16px', fontSize: 13,
          }}>
            <span style={{ color: '#94a3b8' }}>{region}</span>
            <span style={{ color: '#38bdf8', fontWeight: 700, marginLeft: 8 }}>{count.toLocaleString()}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        {['ALL', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'].map(lvl => (
          <button key={lvl} onClick={() => setLevelFilter(lvl)}
            style={{
              background: levelFilter === lvl ? '#3b82f6' : '#1e293b',
              color: levelFilter === lvl ? '#fff' : '#94a3b8',
              border: '1px solid #334155', borderRadius: 8,
              padding: '4px 12px', cursor: 'pointer', fontSize: 12,
            }}>
            {lvl}
          </button>
        ))}
        <input
          value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search message or service..."
          style={{
            marginLeft: 'auto', background: '#1e293b', color: '#e2e8f0',
            border: '1px solid #334155', borderRadius: 8, padding: '4px 12px', fontSize: 12,
          }}
        />
      </div>

      {/* Log table */}
      <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, overflow: 'hidden' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '160px 80px 100px 1fr 140px',
          padding: '8px 12px', borderBottom: '1px solid #1e293b',
          fontSize: 11, color: '#475569', fontWeight: 700,
        }}>
          <span>TIMESTAMP</span><span>LEVEL</span><span>SERVICE</span>
          <span>MESSAGE</span><span>TRACE ID</span>
        </div>
        <div style={{ maxHeight: '65vh', overflowY: 'auto' }}>
          {filtered.slice(0, 200).map((e, i) => (
            <div key={e.trace_id ?? i} style={{
              display: 'grid', gridTemplateColumns: '160px 80px 100px 1fr 140px',
              padding: '6px 12px', borderBottom: '1px solid #1e293b1a',
              fontSize: 12, alignItems: 'center',
              background: i % 2 === 0 ? 'transparent' : '#ffffff05',
            }}>
              <span style={{ color: '#64748b' }}>
                {new Date(e.timestamp * 1000).toISOString().replace('T', ' ').slice(0, 19)}
              </span>
              <Badge label={e.level} color={LEVEL_COLORS[e.level] ?? '#94a3b8'} />
              <span style={{ color: '#7dd3fc', fontSize: 11 }}>{e.service}</span>
              <span style={{ color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {e.message}
              </span>
              <span style={{ color: '#475569', fontSize: 10 }}>{e.trace_id?.slice(0, 16) ?? '—'}</span>
            </div>
          ))}
          {filtered.length === 0 && (
            <div style={{ padding: 32, textAlign: 'center', color: '#475569' }}>
              No log events match current filters
            </div>
          )}
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: '#475569' }}>
        Showing {Math.min(filtered.length, 200)} of {filtered.length} filtered · {events.length} total buffered
      </div>
    </div>
  );
};
