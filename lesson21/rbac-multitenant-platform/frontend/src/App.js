import React, { useState, useEffect } from 'react';
import './App.css';
import RBACDashboard from './components/RBACDashboard';
import NamespaceAnalytics from './components/NamespaceAnalytics';
import PermissionValidator from './components/PermissionValidator';

function App() {
  const [activeTab, setActiveTab] = useState('rbac');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔐 RBAC Multi-Tenant Analytics Platform</h1>
        <p>Real-time Role-Based Access Control Management</p>
      </header>

      <nav className="tab-navigation">
        <button 
          className={activeTab === 'rbac' ? 'active' : ''}
          onClick={() => setActiveTab('rbac')}
        >
          RBAC Dashboard
        </button>
        <button 
          className={activeTab === 'analytics' ? 'active' : ''}
          onClick={() => setActiveTab('analytics')}
        >
          Namespace Analytics
        </button>
        <button 
          className={activeTab === 'validator' ? 'active' : ''}
          onClick={() => setActiveTab('validator')}
        >
          Permission Validator
        </button>
      </nav>

      <main className="App-main">
        {activeTab === 'rbac' && <RBACDashboard />}
        {activeTab === 'analytics' && <NamespaceAnalytics />}
        {activeTab === 'validator' && <PermissionValidator />}
      </main>

      <footer className="App-footer">
        <p>Kubernetes RBAC Platform • Lesson 21: Role-Based Access Control</p>
      </footer>
    </div>
  );
}

export default App;
