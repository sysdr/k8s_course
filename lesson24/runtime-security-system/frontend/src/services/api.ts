import axios from 'axios';

const API_BASE = process.env.VITE_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: API_BASE, timeout: 10000 });

export const securityAPI = {
  getEvents: () => api.get('/api/v1/events'),
  getStatistics: () => api.get('/api/v1/statistics'),
  ingestEvent: (event: any) => api.post('/api/v1/events/ingest', event)
};
