import axios from 'axios';

// Use relative URLs that will be proxied by nginx
const INGESTION_API = process.env.REACT_APP_INGESTION_API || '/api/ingestion';
const ANALYTICS_API = process.env.REACT_APP_ANALYTICS_API || '/api';

export const submitLog = async (logData) => {
  const response = await axios.post(`${INGESTION_API}/v1/logs`, logData);
  return response.data;
};

export const fetchSummary = async () => {
  const response = await axios.get(`${ANALYTICS_API}/v1/analytics/summary`);
  return response.data;
};

export const fetchRecentLogs = async (limit = 20) => {
  const response = await axios.get(`${ANALYTICS_API}/v1/analytics/recent?limit=${limit}`);
  return response.data;
};

export const fetchErrors = async (limit = 10) => {
  const response = await axios.get(`${ANALYTICS_API}/v1/analytics/errors?limit=${limit}`);
  return response.data;
};

export const fetchServiceStats = async () => {
  const response = await axios.get(`${ANALYTICS_API}/v1/analytics/services`);
  return response.data;
};
