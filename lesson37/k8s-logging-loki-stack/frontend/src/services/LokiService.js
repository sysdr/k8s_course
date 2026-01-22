import axios from 'axios';

export class LokiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 10000,
    });
  }

  async queryLogs(query, limit = 100) {
    try {
      const response = await this.client.get('/loki/api/v1/query', {
        params: {
          query: query,
          limit: limit,
        },
      });

      return this.parseLokiResponse(response.data);
    } catch (error) {
      console.error('Loki query error:', error);
      throw error;
    }
  }

  async queryRange(query, rangeSeconds = 3600) {
    try {
      const end = Math.floor(Date.now() / 1000);
      const start = end - rangeSeconds;

      const response = await this.client.get('/loki/api/v1/query_range', {
        params: {
          query: query,
          start: start * 1000000000, // nanoseconds
          end: end * 1000000000,
          step: '60s',
        },
      });

      return this.parseRangeResponse(response.data);
    } catch (error) {
      console.error('Loki range query error:', error);
      return [];
    }
  }

  parseLokiResponse(data) {
    if (!data.data || !data.data.result) {
      return [];
    }

    const logs = [];
    data.data.result.forEach((stream) => {
      stream.values.forEach(([timestamp, logLine]) => {
        try {
          const parsedLog = JSON.parse(logLine);
          logs.push({
            timestamp: new Date(parseInt(timestamp) / 1000000),
            ...parsedLog,
            ...stream.stream,
          });
        } catch (e) {
          logs.push({
            timestamp: new Date(parseInt(timestamp) / 1000000),
            message: logLine,
            ...stream.stream,
          });
        }
      });
    });

    return logs.sort((a, b) => b.timestamp - a.timestamp);
  }

  parseRangeResponse(data) {
    if (!data.data || !data.data.result || data.data.result.length === 0) {
      return [];
    }

    const result = data.data.result[0];
    if (!result.values) {
      return [];
    }

    return result.values.map(([timestamp, value]) => ({
      time: new Date(parseInt(timestamp) / 1000000).toLocaleTimeString(),
      value: parseFloat(value),
    }));
  }
}
