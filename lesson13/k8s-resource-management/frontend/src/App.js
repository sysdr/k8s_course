import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Box } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function App() {
  const [analytics, setAnalytics] = useState({
    total_logs: 0,
    logs_by_level: {},
    logs_by_service: {},
    error_rate: 0
  });
  
  const [timeseries, setTimeseries] = useState({ timestamps: [], error_rates: [], total_logs: [] });

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        // Use nginx proxy path instead of direct service access
        const analyticsUrl = process.env.REACT_APP_ANALYTICS_URL || '/api/analytics';
        const response = await axios.get(`${analyticsUrl}/analytics`);
        setAnalytics(response.data);
        
        const tsResponse = await axios.get(`${analyticsUrl}/analytics/timeseries`);
        setTimeseries(tsResponse.data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      }
    };

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 10000);
    return () => clearInterval(interval);
  }, []);

  const levelData = Object.entries(analytics.logs_by_level).map(([name, value]) => ({
    name,
    value
  }));

  const serviceData = Object.entries(analytics.logs_by_service).map(([name, value]) => ({
    name,
    value
  }));

  const timeseriesData = timeseries.timestamps.map((timestamp, idx) => ({
    time: new Date(timestamp).toLocaleTimeString(),
    errorRate: timeseries.error_rates[idx],
    totalLogs: timeseries.total_logs[idx]
  }));

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Analytics Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
            <Typography variant="h6" gutterBottom>Total Logs</Typography>
            <Typography variant="h3">{analytics.total_logs.toLocaleString()}</Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
            <Typography variant="h6" gutterBottom>Error Rate</Typography>
            <Typography variant="h3" color={analytics.error_rate > 5 ? 'error' : 'success'}>
              {analytics.error_rate}%
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
            <Typography variant="h6" gutterBottom>Services</Typography>
            <Typography variant="h3">{Object.keys(analytics.logs_by_service).length}</Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
            <Typography variant="h6" gutterBottom>Status</Typography>
            <Typography variant="h3" color="success">Healthy</Typography>
          </Paper>
        </Grid>

        {/* Error Rate Timeseries */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Error Rate Over Time</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeseriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="errorRate" stroke="#FF8042" name="Error Rate %" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Logs by Level */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Logs by Level</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={levelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={entry => entry.name}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {levelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Logs by Service */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Logs by Service</Typography>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={serviceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#0088FE" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
