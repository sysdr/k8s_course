import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

export interface LogMetrics {
  totalLogs?: number;
  serviceCount?: number;
  errorRate?: number;
  avgProcessingTime?: number;
  timeSeries?: Array<{ time: string; count: number }>;
  levelDistribution?: Array<{ name: string; value: number }>;
  serviceDistribution?: Array<{ name: string; value: number }>;
}

export const fetchMetrics = async (): Promise<LogMetrics> => {
  try {
    // In production, this would call the ingestion API or a dedicated metrics service
    // For now, return mock data
    const response = await axios.get(`${API_BASE_URL}/metrics`, {
      timeout: 5000
    }).catch(() => ({
      data: generateMockMetrics()
    }));
    
    return response.data;
  } catch (error) {
    console.error('API error:', error);
    return generateMockMetrics();
  }
};

const generateMockMetrics = (): LogMetrics => {
  const now = Date.now();
  return {
    totalLogs: Math.floor(Math.random() * 100000) + 50000,
    serviceCount: Math.floor(Math.random() * 10) + 5,
    errorRate: parseFloat((Math.random() * 5).toFixed(2)),
    avgProcessingTime: Math.floor(Math.random() * 100) + 50,
    timeSeries: Array.from({ length: 12 }, (_, i) => ({
      time: new Date(now - (11 - i) * 300000).toLocaleTimeString(),
      count: Math.floor(Math.random() * 1000) + 500
    })),
    levelDistribution: [
      { name: 'DEBUG', value: Math.floor(Math.random() * 1000) + 500 },
      { name: 'INFO', value: Math.floor(Math.random() * 3000) + 2000 },
      { name: 'WARNING', value: Math.floor(Math.random() * 500) + 200 },
      { name: 'ERROR', value: Math.floor(Math.random() * 200) + 50 },
      { name: 'CRITICAL', value: Math.floor(Math.random() * 50) + 10 }
    ],
    serviceDistribution: [
      { name: 'api-gateway', value: Math.floor(Math.random() * 2000) + 1000 },
      { name: 'user-service', value: Math.floor(Math.random() * 1500) + 800 },
      { name: 'order-service', value: Math.floor(Math.random() * 1000) + 500 },
      { name: 'payment-service', value: Math.floor(Math.random() * 800) + 400 }
    ]
  };
};
