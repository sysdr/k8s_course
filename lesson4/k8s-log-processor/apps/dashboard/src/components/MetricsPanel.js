import React from 'react';

function MetricsPanel({ stats }) {
  return (
    <div className="panel">
      <h2>Metrics</h2>
      <div className="metric">
        <strong>Total Logs:</strong> {stats.total_logs || 0}
      </div>
      <div className="metric">
        <strong>By Level:</strong>
        <ul>
          {Object.entries(stats.by_level || {}).map(([level, count]) => (
            <li key={level}>{level}: {count}</li>
          ))}
        </ul>
      </div>
      <div className="metric">
        <strong>By Source:</strong>
        <ul>
          {Object.entries(stats.by_source || {}).map(([source, count]) => (
            <li key={source}>{source}: {count}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default MetricsPanel;
