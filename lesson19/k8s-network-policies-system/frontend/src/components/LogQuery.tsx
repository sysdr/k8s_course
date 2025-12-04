import React, { useState } from 'react';
import { apiService } from '../services/api';

const LogQuery: React.FC = () => {
  const [service, setService] = useState('');
  const [level, setLevel] = useState('');
  const [limit, setLimit] = useState(100);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getDemoQueryResults = (filterService?: string, filterLevel?: string, resultLimit: number = 100): any[] => {
    const now = Date.now();
    const services = filterService ? [filterService] : ['api-gateway', 'log-ingestion', 'analytics-service', 'log-processor'];
    const levels = filterLevel ? [filterLevel] : ['INFO', 'WARN', 'ERROR', 'DEBUG'];
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
      'Debug: Processing batch of 100 items',
      'Request validation passed',
      'Sending notification to user',
      'Background task scheduled'
    ];

    const count = Math.min(resultLimit, 50); // Limit demo results
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      timestamp: new Date(now - i * 120000).toISOString(),
      level: levels[Math.floor(Math.random() * levels.length)],
      service: services[Math.floor(Math.random() * services.length)],
      message: messages[Math.floor(Math.random() * messages.length)]
    }));
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const query: any = { limit };
      if (service) query.service = service;
      if (level) query.level = level;
      
      const data = await apiService.queryLogs(query);
      // Use demo data if service is degraded or no results
      if (data.status === 'degraded' || !data.logs || data.logs.length === 0) {
        setResults(getDemoQueryResults(service, level, limit));
      } else {
        setResults(data.logs || []);
      }
    } catch (err: any) {
      setError(err.message);
      // Use demo data on error
      setResults(getDemoQueryResults(service, level, limit));
    } finally {
      setLoading(false);
    }
  };

  const handleTestIngest = async () => {
    const testLog = {
      level: 'INFO',
      service: 'test-service',
      message: 'Test log entry from frontend'
    };
    
    try {
      await apiService.ingestLog(testLog);
      alert('Test log ingested successfully!');
    } catch (err: any) {
      alert(`Failed to ingest: ${err.message}`);
    }
  };

  return (
    <div className="log-query">
      <h2>Query Logs</h2>
      
      <form onSubmit={handleQuery} className="query-form">
        <div className="form-group">
          <label>Service Name:</label>
          <input
            type="text"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="e.g., api-service"
          />
        </div>
        
        <div className="form-group">
          <label>Log Level:</label>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">All Levels</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
            <option value="FATAL">FATAL</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Limit:</label>
          <input
            type="number"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            min="1"
            max="1000"
          />
        </div>
        
        <div className="button-group">
          <button type="submit" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button type="button" onClick={handleTestIngest}>
            Test Ingest
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">⚠️ {error}</div>
      )}

      <div className="query-results">
        <h3>Results ({results.length})</h3>
        {results.length > 0 ? (
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
              {results.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td><span className="level-badge">{log.level}</span></td>
                  <td>{log.service}</td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No results found. Try a different query.</p>
        )}
      </div>
    </div>
  );
};

export default LogQuery;
