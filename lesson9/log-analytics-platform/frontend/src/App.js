import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Paper, Typography, Box, Card, CardContent,
  TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, CircularProgress, Alert
} from '@mui/material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:30080';

function App() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Query filters
  const [selectedService, setSelectedService] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [limit, setLimit] = useState(20);

  // Fetch stats periodically
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/stats`);
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setError('Failed to connect to API Gateway');
    }
  };

  const queryLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/query`, {
        service: selectedService || null,
        level: selectedLevel || null,
        limit: limit
      });
      setLogs(response.data.results || []);
      setError(null);
    } catch (err) {
      console.error('Query failed:', err);
      setError('Failed to query logs');
    } finally {
      setLoading(false);
    }
  };

  const ingestTestLog = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/v1/logs`, {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        service: 'test-service',
        message: `Test log message at ${new Date().toLocaleTimeString()}`,
        metadata: { test: true }
      });
      setError(null);
      queryLogs();
    } catch (err) {
      console.error('Failed to ingest log:', err);
      setError('Failed to ingest test log');
    }
  };

  const getLevelColor = (level) => {
    const colors = {
      'INFO': 'info',
      'WARN': 'warning',
      'ERROR': 'error',
      'DEBUG': 'default',
      'CRITICAL': 'error'
    };
    return colors[level] || 'default';
  };

  // Prepare chart data
  const chartData = stats ? Object.entries(stats.by_level || {}).map(([level, count]) => ({
    level,
    count
  })) : [];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Analytics Platform
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Kubernetes Services & Networking Demo
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Processed
              </Typography>
              <Typography variant="h4">
                {stats?.total_processed?.toLocaleString() || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Error Rate
              </Typography>
              <Typography variant="h4" color="error">
                {stats?.error_rate_percentage?.toFixed(2) || '0'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Avg Processing Time
              </Typography>
              <Typography variant="h4">
                {stats?.avg_processing_time_ms?.toFixed(2) || '0'}ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Services
              </Typography>
              <Typography variant="h4">
                {stats ? Object.keys(stats.by_service || {}).length : '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Log Levels Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Logs by Level
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="level" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Services Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Logs by Service
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats ? Object.entries(stats.by_service || {}).map(([service, count]) => ({
                service: service.substring(0, 15),
                count
              })) : []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="service" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Query Interface */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Query Logs
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Service"
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  placeholder="All services"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Level</InputLabel>
                  <Select
                    value={selectedLevel}
                    onChange={(e) => setSelectedLevel(e.target.value)}
                  >
                    <MenuItem value="">All levels</MenuItem>
                    <MenuItem value="DEBUG">DEBUG</MenuItem>
                    <MenuItem value="INFO">INFO</MenuItem>
                    <MenuItem value="WARN">WARN</MenuItem>
                    <MenuItem value="ERROR">ERROR</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  type="number"
                  label="Limit"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={queryLogs}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : 'Search'}
                </Button>
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={ingestTestLog}
                >
                  Test Ingest
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Logs Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Log Entries ({logs.length})
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Service</TableCell>
                    <TableCell>Message</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logs.map((log, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.level}
                          color={getLevelColor(log.level)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{log.service}</TableCell>
                      <TableCell>{log.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
