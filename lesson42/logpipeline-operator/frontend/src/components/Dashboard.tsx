import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent
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

interface MetricData {
  time: string;
  throughput: number;
  errors: number;
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [stats, setStats] = useState({
    totalPipelines: 0,
    activePipelines: 0,
    logsProcessed: 0,
    errorRate: 0
  });

  useEffect(() => {
    // Fetch metrics from API
    const fetchMetrics = async () => {
      // Mock data for demonstration
      const mockData = Array.from({ length: 20 }, (_, i) => ({
        time: `${i}:00`,
        throughput: Math.floor(Math.random() * 1000) + 500,
        errors: Math.floor(Math.random() * 50)
      }));
      setMetrics(mockData);

      setStats({
        totalPipelines: 5,
        activePipelines: 4,
        logsProcessed: 1500000,
        errorRate: 0.02
      });
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Pipelines
            </Typography>
            <Typography variant="h4">{stats.totalPipelines}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Active Pipelines
            </Typography>
            <Typography variant="h4">{stats.activePipelines}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Logs Processed
            </Typography>
            <Typography variant="h4">
              {stats.logsProcessed.toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Error Rate
            </Typography>
            <Typography variant="h4">
              {(stats.errorRate * 100).toFixed(2)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Log Processing Throughput
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="throughput"
                stroke="#8884d8"
                activeDot={{ r: 8 }}
              />
              <Line type="monotone" dataKey="errors" stroke="#ff7300" />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default Dashboard;
