import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts';

interface LogSummary {
  total_logs: number;
  by_level: Record<string, number>;
  by_source: Record<string, number>;
  anomaly_count: number;
}

interface ConnectionStatus {
  api: 'connected' | 'disconnected' | 'checking';
  lastCheck: Date | null;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const App: React.FC = () => {
  const [summary, setSummary] = useState<LogSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    api: 'checking',
    lastCheck: null
  });

  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8002';

  const fetchSummary = async () => {
    try {
      setConnectionStatus(prev => ({ ...prev, api: 'checking' }));
      
      const response = await fetch(`${apiUrl}/api/v1/summary`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSummary(data);
      setError(null);
      setConnectionStatus({
        api: 'connected',
        lastCheck: new Date()
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch data: ${errorMessage}`);
      setConnectionStatus({
        api: 'disconnected',
        lastCheck: new Date()
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    // Poll every 2 seconds for real-time updates
    const interval = setInterval(fetchSummary, 2000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const levelData = summary ? Object.entries(summary.by_level).map(([name, value]) => ({
    name,
    value
  })) : [];

  const sourceData = summary ? Object.entries(summary.by_source).map(([name, count]) => ({
    name,
    count
  })) : [];

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>Log Analytics Dashboard</h1>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px',
          marginTop: '10px',
          flexWrap: 'wrap'
        }}>
          <span style={{
            display: 'inline-block',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: connectionStatus.api === 'connected' ? '#00C49F' : 
                           connectionStatus.api === 'checking' ? '#FFBB28' : '#FF8042',
            animation: connectionStatus.api === 'connected' ? 'pulse 2s infinite' : 'none'
          }}></span>
          <span style={{ fontSize: '14px', color: '#666' }}>
            API: {connectionStatus.api}
            {connectionStatus.lastCheck && 
              ` (Last updated: ${connectionStatus.lastCheck.toLocaleTimeString()})`
            }
          </span>
          {connectionStatus.api === 'connected' && (
            <span style={{ 
              fontSize: '12px', 
              color: '#00C49F',
              fontStyle: 'italic'
            }}>
              • Real-time updates every 2s
            </span>
          )}
        </div>
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}</style>
      </header>

      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          marginBottom: '20px',
          color: '#c00'
        }}>
          <strong>Connection Error:</strong> {error}
          <br />
          <small>This is expected for debugging exercises. Check service connectivity.</small>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <p>Loading dashboard data...</p>
        </div>
      ) : summary ? (
        <>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: '20px',
            marginBottom: '30px'
          }}>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f5f5f5', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Total Logs</h3>
              <p style={{ margin: 0, fontSize: '36px', fontWeight: 'bold', color: '#0088FE' }}>
                {summary.total_logs.toLocaleString()}
              </p>
            </div>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f5f5f5', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Anomalies</h3>
              <p style={{ margin: 0, fontSize: '36px', fontWeight: 'bold', color: '#FF8042' }}>
                {summary.anomaly_count}
              </p>
            </div>
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#f5f5f5', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Sources</h3>
              <p style={{ margin: 0, fontSize: '36px', fontWeight: 'bold', color: '#00C49F' }}>
                {Object.keys(summary.by_source).length}
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '40px', flexWrap: 'wrap' }}>
            <div>
              <h3>Logs by Level</h3>
              <PieChart width={400} height={300}>
                <Pie
                  data={levelData}
                  cx={200}
                  cy={150}
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {levelData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </div>

            <div>
              <h3>Logs by Source</h3>
              <BarChart width={500} height={300} data={sourceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </div>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '50px', color: '#666' }}>
          <p>No data available. Ensure the Log API service is running.</p>
        </div>
      )}
    </div>
  );
};

export default App;
