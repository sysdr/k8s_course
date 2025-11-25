import React from 'react';
import './Statistics.css';

function Statistics({ stats }) {
  if (!stats) return null;

  return (
    <div className="statistics">
      <h2>📊 Inventory Statistics</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_products}</div>
          <div className="stat-label">Total Products</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${stats.total_inventory_value.toFixed(2)}</div>
          <div className="stat-label">Inventory Value</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.categories?.length || 0}</div>
          <div className="stat-label">Categories</div>
        </div>
      </div>
    </div>
  );
}

export default Statistics;
