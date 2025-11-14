import { useState, useEffect } from 'react';
import { fetchMetrics, LogMetrics } from '../services/api';

export const useLogMetrics = () => {
  const [metrics, setMetrics] = useState<LogMetrics>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await fetchMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError('Failed to load metrics');
        console.error('Error loading metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
    
    // Refresh every 5 seconds
    const interval = setInterval(loadMetrics, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return { metrics, loading, error };
};
