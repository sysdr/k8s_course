import React from 'react';
import { LogDashboard } from './components/LogDashboard';

const App: React.FC = () => (
  <div style={{ background: '#0f172a', minHeight: '100vh', padding: '1rem' }}>
    <LogDashboard />
  </div>
);

export default App;
