import React, { useState } from 'react';
import axios from 'axios';

const PermissionValidator = () => {
  const [namespace, setNamespace] = useState('analytics');
  const [resource, setResource] = useState('pods');
  const [verb, setVerb] = useState('get');
  const [serviceAccount, setServiceAccount] = useState('log-processor-sa');
  const [saNamespace, setSaNamespace] = useState('analytics');
  const [useServiceAccount, setUseServiceAccount] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || '';

  const validatePermission = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const payload = {
        namespace,
        resource,
        verb
      };
      
      // If useServiceAccount is true, add ServiceAccount info
      if (useServiceAccount && serviceAccount && saNamespace) {
        payload.service_account = serviceAccount;
        payload.sa_namespace = saNamespace;
      }
      
      const response = await axios.post(`${API_BASE}/api/rbac/validate`, payload);
      setResult(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const commonChecks = [
    { resource: 'pods', verb: 'get' },
    { resource: 'pods', verb: 'list' },
    { resource: 'pods', verb: 'create' },
    { resource: 'pods', verb: 'delete' },
    { resource: 'pods/log', verb: 'get' },
    { resource: 'secrets', verb: 'get' },
    { resource: 'configmaps', verb: 'get' },
    { resource: 'services', verb: 'list' },
  ];

  const runBulkValidation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const checks = commonChecks.map(check => {
        const payload = {
          namespace,
          ...check
        };
        
        // Add ServiceAccount info if enabled
        if (useServiceAccount && serviceAccount && saNamespace) {
          payload.service_account = serviceAccount;
          payload.sa_namespace = saNamespace;
        }
        
        return payload;
      });
      
      const response = await axios.post(`${API_BASE}/api/rbac/bulk-validate`, checks);
      setResult(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="dashboard-section">
        <h2>🔍 Permission Validator</h2>
        <p>Test specific RBAC permissions for a ServiceAccount</p>
        
        <form onSubmit={validatePermission}>
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={useServiceAccount}
                onChange={(e) => setUseServiceAccount(e.target.checked)}
                style={{marginRight: '8px'}}
              />
              Test specific ServiceAccount (uncheck to test rbac-validator-sa)
            </label>
          </div>
          
          {useServiceAccount && (
            <>
              <div className="form-group">
                <label>ServiceAccount Name:</label>
                <input
                  type="text"
                  value={serviceAccount}
                  onChange={(e) => setServiceAccount(e.target.value)}
                  placeholder="e.g., log-processor-sa"
                />
              </div>
              
              <div className="form-group">
                <label>ServiceAccount Namespace:</label>
                <input
                  type="text"
                  value={saNamespace}
                  onChange={(e) => setSaNamespace(e.target.value)}
                  placeholder="e.g., analytics"
                />
              </div>
            </>
          )}
          
          <div className="form-group">
            <label>Namespace:</label>
            <input
              type="text"
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              placeholder="e.g., analytics"
            />
          </div>
          
          <div className="form-group">
            <label>Resource:</label>
            <input
              type="text"
              value={resource}
              onChange={(e) => setResource(e.target.value)}
              placeholder="e.g., pods, secrets, configmaps"
            />
          </div>
          
          <div className="form-group">
            <label>Verb:</label>
            <select value={verb} onChange={(e) => setVerb(e.target.value)}>
              <option value="get">get</option>
              <option value="list">list</option>
              <option value="watch">watch</option>
              <option value="create">create</option>
              <option value="update">update</option>
              <option value="patch">patch</option>
              <option value="delete">delete</option>
            </select>
          </div>
          
          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Validating...' : 'Validate Permission'}
          </button>
          
          <button 
            type="button" 
            className="primary" 
            onClick={runBulkValidation}
            disabled={loading}
            style={{marginLeft: '10px'}}
          >
            Run Common Checks
          </button>
        </form>
      </div>

      {error && (
        <div className="dashboard-section error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && result.resource && (
        <div className="dashboard-section">
          <h2>✅ Validation Result</h2>
          <div className={`permission-card ${result.allowed ? 'allowed' : 'denied'}`}>
            <h4>{result.resource} - {result.verb}</h4>
            <p><strong>Allowed:</strong> {result.allowed ? 'Yes' : 'No'}</p>
            {result.reason && <p><strong>Reason:</strong> {result.reason}</p>}
          </div>
        </div>
      )}

      {result && result.results && (
        <div className="dashboard-section">
          <h2>📋 Bulk Validation Results</h2>
          <p>
            <strong>Total Checks:</strong> {result.total_checks} | 
            <strong> Allowed:</strong> {result.allowed} | 
            <strong> Denied:</strong> {result.denied}
          </p>
          
          <div className="permission-grid">
            {result.results.map((r, idx) => (
              <div key={idx} className={`permission-card ${r.allowed ? 'allowed' : 'denied'}`}>
                <h4>{r.resource}</h4>
                <p><strong>Verb:</strong> {r.verb}</p>
                <p><strong>Status:</strong> {r.allowed ? '✓ Allowed' : '✗ Denied'}</p>
                {r.reason && <p><small>{r.reason}</small></p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PermissionValidator;
