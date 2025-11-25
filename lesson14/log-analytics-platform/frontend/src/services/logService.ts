import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

interface QueryLogsRequest {
  start_time?: string;
  end_time?: string;
  level?: string;
  source?: string;
  limit?: number;
}

interface QueryLogsResponse {
  logs: any[];
  total_count: number;
  query_time_ms: number;
}

export const logService = {
  async queryLogs(params: QueryLogsRequest): Promise<QueryLogsResponse> {
    const response = await axios.post(`${API_BASE_URL}/query`, params);
    return response.data;
  },

  async getStats() {
    const response = await axios.get(`${API_BASE_URL}/stats`);
    return response.data;
  },

  async aggregate(params: any) {
    const response = await axios.post(`${API_BASE_URL}/aggregate`, params);
    return response.data;
  }
};
