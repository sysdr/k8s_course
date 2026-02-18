import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002';

export const fetchAnalyticsSummary = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/v1/analytics/summary`);
  return response.data;
};

export const fetchRecentLogs = async (limit: number = 100) => {
  const response = await axios.get(`${API_BASE_URL}/api/v1/analytics/recent-logs?limit=${limit}`);
  return response.data;
};
