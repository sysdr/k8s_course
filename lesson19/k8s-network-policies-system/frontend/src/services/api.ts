// Use relative URL to leverage nginx proxy
const API_URL = process.env.REACT_APP_API_URL || '';

export const apiService = {
  async queryLogs(query: any) {
    const response = await fetch(`${API_URL}/api/logs/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query)
    });
    
    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  async ingestLog(log: any) {
    const response = await fetch(`${API_URL}/api/logs/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(log)
    });
    
    if (!response.ok) {
      throw new Error(`Ingest failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getStats() {
    const response = await fetch(`${API_URL}/api/stats`);
    
    if (!response.ok) {
      throw new Error(`Stats failed: ${response.statusText}`);
    }
    
    return response.json();
  }
};
