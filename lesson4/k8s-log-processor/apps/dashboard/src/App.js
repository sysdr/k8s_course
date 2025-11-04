import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import MetricsPanel from './components/MetricsPanel';
import LogStream from './components/LogStream';
import StatsDisplay from './components/StatsDisplay';

const ANALYTICS_API = process.env.REACT_APP_ANALYTICS_API || '/api';

function App() {
  const [stats, setStats] = useState({ total_logs: 0, by_level: {}, by_source: {} });
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${ANALYTICS_API}/analytics/summary`);
        setStats(response.data);
        setRecentLogs(response.data.recent_logs || []);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="App">Loading...</div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Kubernetes Log Processing Dashboard</h1>
      </header>
      <div className="dashboard-content">
        <MetricsPanel stats={stats} />
        <StatsDisplay stats={stats} />
        <LogStream logs={recentLogs} />
      </div>
    </div>
  );
}

export default App;
