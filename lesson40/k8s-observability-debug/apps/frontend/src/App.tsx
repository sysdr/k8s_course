import React, { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Box,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import axios from 'axios';

interface MetricData {
  timestamp: number;
  value: number;
  labels: Record<string, string>;
}

interface ServiceHealth {
  status: string;
  timestamp: number;
}

const App: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        
        // Fetch service health
        try {
          const healthResponse = await axios.get('/api/health');
          setHealth(healthResponse.data);
        } catch (err) {
          console.warn('Health check failed:', err);
          setHealth({ status: 'unknown', timestamp: Date.now() });
        }

        // Fetch metrics from Prometheus - try multiple queries
        const queries = [
          'log_entries_processed_total',
          'http_request_duration_seconds_count',
          'active_processing_jobs',
          'up{job="log-processor"}'
        ];
        
        let allMetrics: MetricData[] = [];
        
        for (const query of queries) {
          try {
            const metricsResponse = await axios.get('/api/prometheus/query', {
              params: { query }
            });
            
            if (metricsResponse.data.status === 'success' && metricsResponse.data.data.result) {
              const results = metricsResponse.data.data.result.map((r: any) => ({
                timestamp: r.value[0],
                value: parseFloat(r.value[1]),
                labels: r.metric || {}
              }));
              allMetrics = [...allMetrics, ...results];
            }
          } catch (err) {
            console.warn(`Query ${query} failed:`, err);
          }
        }

        if (allMetrics.length === 0) {
          setError('No metrics data available - check Prometheus scraping');
        } else {
          setMetrics(allMetrics);
          setError(null);
        }

        setLoading(false);
      } catch (err) {
        const errorMessage = (err as any).response?.data?.error || (err as Error).message;
        setError('Failed to fetch observability data: ' + errorMessage);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Observability Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Service Health Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Health
              </Typography>
              {health ? (
                <Chip
                  label={health.status.toUpperCase()}
                  color={health.status === 'healthy' ? 'success' : 'error'}
                  sx={{ mt: 1 }}
                />
              ) : (
                <Chip label="UNKNOWN" color="warning" sx={{ mt: 1 }} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Metrics Count */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Metrics
              </Typography>
              <Typography variant="h4" color="primary">
                {metrics.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Scrape Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Prometheus Scraping
              </Typography>
              <Chip
                label={metrics.length > 0 ? 'ACTIVE' : 'NO DATA'}
                color={metrics.length > 0 ? 'success' : 'error'}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Metrics Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Request Duration Metrics
            </Typography>
            {metrics.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metrics.slice(0, 50).map((m, i) => ({ 
                  name: `Metric ${i + 1}`, 
                  value: m.value,
                  timestamp: new Date(m.timestamp * 1000).toLocaleTimeString()
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#8884d8" name="Metric Value" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Alert severity="warning">
                No metrics data available. Check if Prometheus is scraping the application.
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* Debug Information */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Debug Information
            </Typography>
            <Typography variant="body2" component="pre" sx={{ backgroundColor: '#f5f5f5', p: 2, overflow: 'auto' }}>
              {JSON.stringify({ health, metricsCount: metrics.length }, null, 2)}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default App;
