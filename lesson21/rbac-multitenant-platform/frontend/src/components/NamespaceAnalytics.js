import React, { useState, useEffect } from 'react';
import axios from 'axios';

const NamespaceAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || '';

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/analytics/namespaces`);
      setAnalytics(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading analytics...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{analytics?.total_namespaces || 0}</h3>
          <p>Accessible Namespaces</p>
        </div>
        <div className="stat-card">
          <h3>
            {analytics?.analytics?.reduce((sum, ns) => sum + ns.pod_count, 0) || 0}
          </h3>
          <p>Total Pods</p>
        </div>
        <div className="stat-card">
          <h3>
            {analytics?.analytics?.reduce((sum, ns) => sum + ns.deployment_count, 0) || 0}
          </h3>
          <p>Total Deployments</p>
        </div>
        <div className="stat-card">
          <h3>
            {analytics?.analytics?.reduce((sum, ns) => sum + ns.serviceaccount_count, 0) || 0}
          </h3>
          <p>Total ServiceAccounts</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>📊 Namespace Details</h2>
        <table>
          <thead>
            <tr>
              <th>Namespace</th>
              <th>Pods</th>
              <th>Services</th>
              <th>Deployments</th>
              <th>ServiceAccounts</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {analytics?.analytics?.map((ns) => (
              <tr key={ns.namespace}>
                <td><strong>{ns.namespace}</strong></td>
                <td>{ns.pod_count}</td>
                <td>{ns.service_count}</td>
                <td>{ns.deployment_count}</td>
                <td>{ns.serviceaccount_count}</td>
                <td>{new Date(ns.created).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NamespaceAnalytics;
