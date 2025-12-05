import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RBACDashboard = () => {
  const [rbacSummary, setRbacSummary] = useState(null);
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || '';

  useEffect(() => {
    fetchRBACData();
    const interval = setInterval(fetchRBACData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchRBACData = async () => {
    try {
      const [summaryRes, permissionsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/analytics/rbac/summary`),
        axios.get(`${API_BASE}/api/rbac/list-permissions?namespace=analytics`)
      ]);
      
      setRbacSummary(summaryRes.data);
      setPermissions(permissionsRes.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading RBAC data...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>{rbacSummary?.roles?.total || 0}</h3>
          <p>Total Roles</p>
        </div>
        <div className="stat-card">
          <h3>{rbacSummary?.roles?.cluster_roles || 0}</h3>
          <p>Cluster Roles</p>
        </div>
        <div className="stat-card">
          <h3>{rbacSummary?.bindings?.role_bindings || 0}</h3>
          <p>Role Bindings</p>
        </div>
        <div className="stat-card">
          <h3>{rbacSummary?.bindings?.cluster_role_bindings || 0}</h3>
          <p>Cluster Role Bindings</p>
        </div>
      </div>

      <div className="dashboard-section">
        <h2>📋 Current ServiceAccount Permissions</h2>
        <p><strong>Namespace:</strong> {permissions?.namespace || 'N/A'}</p>
        <p><strong>Permission Rules:</strong> {permissions?.permission_count || 0}</p>
        
        <table>
          <thead>
            <tr>
              <th>Resources</th>
              <th>Verbs</th>
              <th>API Groups</th>
            </tr>
          </thead>
          <tbody>
            {permissions?.permissions?.map((perm, idx) => (
              <tr key={idx}>
                <td>{perm.resources.join(', ')}</td>
                <td>{perm.verbs.join(', ')}</td>
                <td>{perm.api_groups.join(', ') || 'core'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="dashboard-section">
        <h2>🏢 Namespace Role Distribution</h2>
        <table>
          <thead>
            <tr>
              <th>Namespace</th>
              <th>Role Count</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(rbacSummary?.roles?.namespace_distribution || {}).map(([ns, count]) => (
              <tr key={ns}>
                <td>{ns}</td>
                <td>{count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RBACDashboard;
