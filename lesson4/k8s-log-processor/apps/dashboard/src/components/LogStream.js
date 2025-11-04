import React from 'react';

function LogStream({ logs }) {
  return (
    <div className="panel">
      <h2>Recent Logs</h2>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {logs && logs.length > 0 ? (
          logs.map((log, idx) => (
            <div key={idx} className="log-entry">
              <strong>{log.level}</strong> [{log.source}] {log.message}
              <br />
              <small>{log.timestamp}</small>
            </div>
          ))
        ) : (
          <p>No logs yet</p>
        )}
      </div>
    </div>
  );
}

export default LogStream;
