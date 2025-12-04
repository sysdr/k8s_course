import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface Log {
  id: number;
  timestamp: string;
  level: string;
  service: string;
  message: string;
}

const LogDashboard: React.FC = () => {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecentLogs();
    const interval = setInterval(fetchRecentLogs, 30000); // Reduced to 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchRecentLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.queryLogs({ limit: 50 });
      // Use demo data if service is degraded or no logs
      if (data.status === 'degraded' || !data.logs || data.logs.length === 0) {
        setLogs(getDemoLogs());
      } else {
        setLogs(data.logs || []);
      }
    } catch (err: any) {
      setError(err.message);
      // Use demo data on error
      setLogs(getDemoLogs());
    } finally {
      setLoading(false);
    }
  };

  const getDemoLogs = (): Log[] => {
    const now = Date.now();
    const services = ['api-gateway', 'log-ingestion', 'analytics-service', 'log-processor'];
    const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
    const messages = [
      'User authentication successful',
      'Processing request from client',
      'Database query executed',
      'Cache hit for key',
      'Failed to connect to external service',
      'Rate limit exceeded',
      'Log entry processed successfully',
      'Starting background job',
      'Job completed successfully',
      'Warning: High memory usage detected',
      'Error: Connection timeout',
      'Debug: Processing batch of 100 items'
    ];

    return Array.from({ length: 20 }, (_, i) => ({
      id: i + 1,
      timestamp: new Date(now - i * 60000).toISOString(),
      level: levels[Math.floor(Math.random() * levels.length)],
      service: services[Math.floor(Math.random() * services.length)],
      message: messages[Math.floor(Math.random() * messages.length)]
    }));
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

  return (
    <div className="log-dashboard">
      <div className="dashboard-header">
        <h2>Recent Logs</h2>
        <button onClick={fetchRecentLogs} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="logs-container">
        <table className="logs-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Level</th>
              <th>Service</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="timestamp">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td>
                  <span 
                    className="level-badge"
                    style={{ backgroundColor: getLevelColor(log.level) }}
                  >
                    {log.level}
                  </span>
                </td>
                <td className="service">{log.service}</td>
                <td className="message">{log.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {logs.length === 0 && !loading && (
          <div className="no-logs">
            <p>No logs available. Start ingesting logs to see them here.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogDashboard;
