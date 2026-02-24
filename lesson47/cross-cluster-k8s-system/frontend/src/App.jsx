import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  CircularProgress
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import axios from 'axios';

const CLUSTER_A_URL = process.env.REACT_APP_CLUSTER_A_URL || 'http://localhost:8000';
const CLUSTER_B_URL = process.env.REACT_APP_CLUSTER_B_URL || 'http://localhost:8001';

function App() {
  const [clusterAHealth, setClusterAHealth] = useState(null);
  const [clusterBHealth, setClusterBHealth] = useState(null);
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Cluster A health
        const healthA = await axios.get(`${CLUSTER_A_URL}/health`);
        setClusterAHealth(healthA.data);

        // Fetch Cluster B health
        const healthB = await axios.get(`${CLUSTER_B_URL}/health`);
        setClusterBHealth(healthB.data);

        // Fetch processing stats
        const statsResponse = await axios.get(`${CLUSTER_B_URL}/stats`);
        setStats(statsResponse.data);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Cross-Cluster Logging Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Cluster A - Log Ingestion</Typography>
            <CardContent>
              <Typography>Status: {clusterAHealth?.status}</Typography>
              <Typography>Kafka: {clusterAHealth?.kafka_connected ? '✓' : '✗'}</Typography>
              <Typography>Redis: {clusterAHealth?.redis_connected ? '✓' : '✗'}</Typography>
            </CardContent>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Cluster B - Log Processor</Typography>
            <CardContent>
              <Typography>Status: {clusterBHealth?.status}</Typography>
              <Typography>Kafka: {clusterBHealth?.kafka_connected ? '✓' : '✗'}</Typography>
              <Typography>Database: {clusterBHealth?.database_connected ? '✓' : '✗'}</Typography>
              <Typography>Cluster A Reachable: {clusterBHealth?.cluster_a_reachable ? '✓' : '✗'}</Typography>
              <Typography>Processed: {clusterBHealth?.processed_count}</Typography>
            </CardContent>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Log Statistics by Service</Typography>
            {stats.map(stat => (
              <Card key={stat.service} sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1">{stat.service}</Typography>
                  <Typography>Total: {stat.total_logs}</Typography>
                  <Typography>Errors: {stat.error_count}</Typography>
                  <Typography>Warnings: {stat.warning_count}</Typography>
                </CardContent>
              </Card>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
