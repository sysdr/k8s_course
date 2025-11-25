import React, { useState, useEffect } from 'react';
import './App.css';
import ProductList from './components/ProductList';
import Statistics from './components/Statistics';
import ConnectionStatus from './components/ConnectionStatus';

const API_URL = process.env.REACT_APP_API_URL || 'http://api-backend:8000';

function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      console.log(`Attempting to fetch from: ${API_URL}`);
      
      // Fetch products
      const productsResponse = await fetch(`${API_URL}/api/products`);
      if (!productsResponse.ok) {
        throw new Error(`HTTP ${productsResponse.status}: ${productsResponse.statusText}`);
      }
      const productsData = await productsResponse.json();
      setProducts(productsData);

      // Fetch statistics
      const statsResponse = await fetch(`${API_URL}/api/stats`);
      if (!statsResponse.ok) {
        throw new Error(`HTTP ${statsResponse.status}: ${statsResponse.statusText}`);
      }
      const statsData = await statsResponse.json();
      setStats(statsData);

      setConnectionStatus('connected');
      setError(null);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError(`Connection failed: ${err.message}. API URL: ${API_URL}`);
      setConnectionStatus('error');
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🛒 E-Commerce Dashboard</h1>
        <ConnectionStatus status={connectionStatus} apiUrl={API_URL} />
      </header>

      <main className="App-main">
        {loading && <div className="loading">Loading...</div>}
        
        {error && (
          <div className="error-banner">
            <h2>⚠️ Connection Error</h2>
            <p>{error}</p>
            <button onClick={fetchData}>Retry Connection</button>
          </div>
        )}

        {!loading && !error && (
          <>
            <Statistics stats={stats} />
            <ProductList products={products} />
          </>
        )}
      </main>
    </div>
  );
}

export default App;
