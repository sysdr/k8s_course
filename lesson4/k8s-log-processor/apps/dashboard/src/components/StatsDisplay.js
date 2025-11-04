import React from 'react';

function StatsDisplay({ stats }) {
  return (
    <div className="panel">
      <h2>Statistics</h2>
      <div className="metric">
        <strong>Total Count:</strong> {stats.total_logs || 0}
      </div>
      <div className="metric">
        <strong>Level Distribution:</strong>
        {Object.keys(stats.by_level || {}).length > 0 ? (
          <ul>
            {Object.entries(stats.by_level || {}).map(([level, count]) => (
              <li key={level}>
                {level}: {count} ({stats.total_logs > 0 ? ((count / stats.total_logs) * 100).toFixed(1) : 0}%)
              </li>
            ))}
          </ul>
        ) : (
          <p>No data available</p>
        )}
      </div>
    </div>
  );
}

export default StatsDisplay;
