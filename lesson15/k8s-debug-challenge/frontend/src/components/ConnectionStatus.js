import React from 'react';
import './ConnectionStatus.css';

function ConnectionStatus({ status, apiUrl }) {
  const getStatusInfo = () => {
    switch (status) {
      case 'connected':
        return { icon: '✓', color: '#4caf50', text: 'Connected' };
      case 'error':
        return { icon: '✗', color: '#f44336', text: 'Connection Failed' };
      case 'connecting':
        return { icon: '⟳', color: '#ff9800', text: 'Connecting...' };
      default:
        return { icon: '?', color: '#9e9e9e', text: 'Unknown' };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="connection-status" style={{ borderColor: statusInfo.color }}>
      <span className="status-icon" style={{ color: statusInfo.color }}>
        {statusInfo.icon}
      </span>
      <span className="status-text">{statusInfo.text}</span>
      <span className="api-url">API: {apiUrl}</span>
    </div>
  );
}

export default ConnectionStatus;
