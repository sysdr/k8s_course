import React from 'react';

interface DashboardProps {
  summary: any;
  logs: any[];
  loading: boolean;
  onRefresh: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ summary, logs, loading, onRefresh }) => {
  if (loading && !summary) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-controls">
        <button onClick={onRefresh} disabled={loading}>
          {loading ? '🔄 Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {summary && (
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Total Logs</h3>
            <div className="metric-value">{summary.total_logs?.toLocaleString()}</div>
          </div>
          
          <div className="metric-card">
            <h3>Error Rate</h3>
            <div className="metric-value">{summary.error_rate}%</div>
          </div>
          
          <div className="metric-card">
            <h3>Top Source</h3>
            <div className="metric-value">
              {summary.top_sources?.[0]?.source || 'N/A'}
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Critical Logs</h3>
            <div className="metric-value critical">
              {summary.logs_by_level?.CRITICAL || 0}
            </div>
          </div>
        </div>
      )}

      {summary?.logs_by_level && (
        <div className="section">
          <h2>Logs by Level</h2>
          <div className="level-breakdown">
            {Object.entries(summary.logs_by_level).map(([level, count]: [string, any]) => (
              <div key={level} className={`level-item level-${level.toLowerCase()}`}>
                <span className="level-label">{level}</span>
                <span className="level-count">{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary?.top_sources && (
        <div className="section">
          <h2>Top Sources</h2>
          <div className="sources-list">
            {summary.top_sources.map((source: any, idx: number) => (
              <div key={idx} className="source-item">
                <span className="source-name">{source.source}</span>
                <span className="source-count">{source.count.toLocaleString()}</span>
                <div className="source-bar" style={{ width: `${(source.count / summary.top_sources[0].count) * 100}%` }} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="section">
        <h2>Recent Logs</h2>
        <div className="logs-container">
          {logs.slice(0, 20).map((log, idx) => (
            <div key={idx} className={`log-entry log-${log.level?.toLowerCase()}`}>
              <span className="log-time">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className={`log-level level-${log.level?.toLowerCase()}`}>
                {log.level}
              </span>
              <span className="log-source">{log.source}</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
