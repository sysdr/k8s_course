import React from 'react';

interface StatisticsProps {
  stats: any;
}

const Statistics: React.FC<StatisticsProps> = ({ stats }) => {
  if (!stats) {
    return <div className="statistics loading">Loading statistics...</div>;
  }

  return (
    <div className="statistics">
      <h2>Platform Statistics</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Logs</h3>
          <div className="stat-value">{stats.total_logs?.toLocaleString() || 0}</div>
        </div>
        
        <div className="stat-card">
          <h3>Last Hour</h3>
          <div className="stat-value">{stats.last_hour?.toLocaleString() || 0}</div>
        </div>
      </div>

      <div className="stats-section">
        <h3>Logs by Level</h3>
        <div className="level-bars">
          {stats.by_level && Object.entries(stats.by_level).map(([level, count]: [string, any]) => (
            <div key={level} className="level-bar">
              <span className="level-name">{level}</span>
              <div className="bar-container">
                <div 
                  className="bar-fill"
                  style={{ 
                    width: `${(count / stats.total_logs) * 100}%`,
                    backgroundColor: getLevelColor(level)
                  }}
                />
              </div>
              <span className="level-count">{count.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="stats-section">
        <h3>Top Services</h3>
        <div className="service-list">
          {stats.by_service && Object.entries(stats.by_service).map(([service, count]: [string, any]) => (
            <div key={service} className="service-item">
              <span className="service-name">{service}</span>
              <span className="service-count">{count.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const getLevelColor = (level: string) => {
  const colors: { [key: string]: string } = {
    'ERROR': '#ff4444',
    'FATAL': '#cc0000',
    'WARN': '#ffaa00',
    'INFO': '#00aa00',
    'DEBUG': '#888888'
  };
  return colors[level] || '#666666';
};

export default Statistics;
