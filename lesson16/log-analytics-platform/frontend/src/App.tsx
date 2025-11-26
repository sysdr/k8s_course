import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';

const API_BASE = process.env.REACT_APP_API_URL || '';

function App() {
  const [summary, setSummary] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [summaryRes, logsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/analytics/summary`),
        axios.get(`${API_BASE}/api/query?limit=50`)
      ]);
      
      setSummary(summaryRes.data);
      setLogs(logsRes.data.results || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📊 Log Analytics Dashboard</h1>
        <p>Real-time log monitoring and analysis</p>
      </header>
      
      {error && (
        <div className="error-banner">
          ⚠️ Error: {error}
        </div>
      )}
      
      <Dashboard 
        summary={summary} 
        logs={logs} 
        loading={loading}
        onRefresh={fetchData}
      />
    </div>
  );
}

export default App;
