import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

interface LogMetrics {
  service: string;
  total: number;
  errors: number;
  warnings: number;
  info: number;
}

interface TimeSeriesData {
  timestamp: string;
  count: number;
}

const App: React.FC = () => {
  const [metrics, setMetrics] = useState<LogMetrics[]>([]);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'metrics') {
        setMetrics(data.metrics);
      } else if (data.type === 'timeseries') {
        setTimeSeries(prev => [...prev.slice(-50), data.point]);
      }
    };
    
    ws.onerror = () => {
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    // Fetch initial data
    fetchMetrics();
    
    // Poll for updates every 5 seconds as fallback
    const interval = setInterval(fetchMetrics, 5000);
    
    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics');
      const data = await response.json();
      setMetrics(data.services || []);
      setTimeSeries(data.timeSeries || []);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const totalLogs = metrics.reduce((sum, m) => sum + m.total, 0);
  const totalErrors = metrics.reduce((sum, m) => sum + m.errors, 0);
  const errorRate = totalLogs > 0 ? ((totalErrors / totalLogs) * 100).toFixed(2) : '0.00';

  return (
    <div className="App">
      <header className="App-header">
        <h1>Log Analytics Dashboard</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <div className="metrics-container">
        <div className="metric-card info-card">
          <h3>Total Logs</h3>
          <div className="metric-value">{totalLogs.toLocaleString()}</div>
        </div>
        <div className="metric-card error-card">
          <h3>Total Errors</h3>
          <div className="metric-value error">{totalErrors.toLocaleString()}</div>
        </div>
        <div className="metric-card warning-card">
          <h3>Error Rate</h3>
          <div className="metric-value warning">{errorRate}%</div>
        </div>
        <div className="metric-card">
          <h3>Active Services</h3>
          <div className="metric-value success">{metrics.length}</div>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart-card">
          <h2>Logs by Service</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="info" fill="#10b981" name="Info" />
              <Bar dataKey="warnings" fill="#f59e0b" name="Warnings" />
              <Bar dataKey="errors" fill="#ef4444" name="Errors" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h2>Log Ingestion Rate (Last 50 Points)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={3} name="Logs/sec" dot={{ fill: '#10b981', r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="services-table">
        <h2>Service Details</h2>
        <table>
          <thead>
            <tr>
              <th>Service</th>
              <th>Total Logs</th>
              <th>Errors</th>
              <th>Warnings</th>
              <th>Info</th>
              <th>Error Rate</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map(metric => (
              <tr key={metric.service}>
                <td>{metric.service}</td>
                <td>{metric.total.toLocaleString()}</td>
                <td className="error-cell">{metric.errors.toLocaleString()}</td>
                <td className="warning-cell">{metric.warnings.toLocaleString()}</td>
                <td className="info-cell">{metric.info.toLocaleString()}</td>
                <td>{metric.total > 0 ? ((metric.errors / metric.total) * 100).toFixed(2) : '0.00'}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default App;
