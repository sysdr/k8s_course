import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export class LogService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
  });

  async submitLog(logData: any) {
    return this.api.post('/api/v1/logs', logData);
  }

  async getStats() {
    return this.api.get('/api/v1/stats');
  }
}
