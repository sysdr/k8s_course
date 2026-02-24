import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  Box
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';

interface ClusterMetrics {
  cluster: string;
  total_logs: number;
  errors: number;
  services: number;
}

const App: React.FC = () => {
  const defaultClusters: ClusterMetrics[] = [
    { cluster: 'us-west-2', total_logs: 15420, errors: 23, services: 12 },
    { cluster: 'eu-west-1', total_logs: 12350, errors: 18, services: 10 },
    { cluster: 'ap-southeast-1', total_logs: 9870, errors: 15, services: 9 }
  ];
  const [clusters, setClusters] = useState<ClusterMetrics[]>(defaultClusters);
  const [chartData, setChartData] = useState([
    { time: '00:00', usWest: 4000, euWest: 2400, apSoutheast: 2400 },
    { time: '04:00', usWest: 3000, euWest: 1398, apSoutheast: 2210 },
    { time: '08:00', usWest: 2000, euWest: 9800, apSoutheast: 2290 },
    { time: '12:00', usWest: 2780, euWest: 3908, apSoutheast: 2000 },
    { time: '16:00', usWest: 1890, euWest: 4800, apSoutheast: 2181 },
    { time: '20:00', usWest: 2390, euWest: 3800, apSoutheast: 2500 },
  ]);

  const apiBase = (typeof process !== 'undefined' && process.env?.REACT_APP_ANALYTICS_URL) || '';

  useEffect(() => {
    if (!apiBase) return;
    const fetchMetrics = async () => {
      try {
        const res = await axios.get(apiBase + '/api/v1/analytics/metrics', { timeout: 5000 });
        const all = res.data?.all_services;
        if (all && typeof all === 'object') {
          const names = Object.keys(all);
          const next: ClusterMetrics[] = names.map((name) => {
            const m = all[name] || {};
            const total = Number(m.total) || 0;
            const errors = Number(m.ERROR) || Number(m.error) || 0;
            return { cluster: name, total_logs: total, errors, services: names.length };
          });
          if (next.length > 0) setClusters(next);
          const now = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
          setChartData((prev) => {
            const last = prev[prev.length - 1];
            const us = next.find((c) => c.cluster.includes('us-west'))?.total_logs ?? last?.usWest ?? 0;
            const eu = next.find((c) => c.cluster.includes('eu-west'))?.total_logs ?? last?.euWest ?? 0;
            const ap = next.find((c) => c.cluster.includes('ap-southeast'))?.total_logs ?? last?.apSoutheast ?? 0;
            const nextPoint = { time: now, usWest: us, euWest: eu, apSoutheast: ap };
            const slice = prev.slice(-11);
            return [...slice, nextPoint];
          });
        }
      } catch (_) {}
    };
    fetchMetrics();
    const t = setInterval(fetchMetrics, 10000);
    return () => clearInterval(t);
  }, [apiBase]);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div">
            Multi-Cluster Kubernetes Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Grid container spacing={3}>
          {clusters.map((cluster) => (
            <Grid item xs={12} md={4} key={cluster.cluster}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Cluster: {cluster.cluster}
                  </Typography>
                  <Typography variant="h4">
                    {cluster.total_logs.toLocaleString()}
                  </Typography>
                  <Typography color="textSecondary">
                    Total Logs Processed
                  </Typography>
                  <Typography variant="body2" color="error">
                    {cluster.errors} Errors
                  </Typography>
                  <Typography variant="body2">
                    {cluster.services} Services
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
          
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Cross-Cluster Traffic Distribution
              </Typography>
              <LineChart width={1000} height={300} data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="usWest" stroke="#8884d8" name="US West" />
                <Line type="monotone" dataKey="euWest" stroke="#82ca9d" name="EU West" />
                <Line type="monotone" dataKey="apSoutheast" stroke="#ffc658" name="AP Southeast" />
              </LineChart>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default App;
