import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Alert
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({ total_logs: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    service: '',
    level: '',
    limit: 100
  });

  const [newLog, setNewLog] = useState({
    service: 'frontend',
    level: 'INFO',
    message: ''
  });

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleQueryLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/logs/query`, filters);
      const parsedLogs = response.data.logs.map(log => JSON.parse(log));
      setLogs(parsedLogs);
    } catch (err) {
      setError('Failed to query logs: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleIngestLog = async () => {
    if (!newLog.message) {
      setError('Message is required');
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/logs`, newLog);
      setNewLog({ ...newLog, message: '' });
      setError(null);
      fetchStats();
    } catch (err) {
      setError('Failed to ingest log: ' + err.message);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        📊 Log Analytics Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Logs
              </Typography>
              <Typography variant="h4">
                {stats.total_logs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Services
              </Typography>
              <Typography variant="h4">
                3
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Status
              </Typography>
              <Typography variant="h4" color="success.main">
                Healthy
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Log Ingestion */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Ingest New Log
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <TextField
                label="Service"
                value={newLog.service}
                onChange={(e) => setNewLog({ ...newLog, service: e.target.value })}
              />
              <FormControl sx={{ minWidth: 120 }}>
                <InputLabel>Level</InputLabel>
                <Select
                  value={newLog.level}
                  onChange={(e) => setNewLog({ ...newLog, level: e.target.value })}
                >
                  <MenuItem value="DEBUG">DEBUG</MenuItem>
                  <MenuItem value="INFO">INFO</MenuItem>
                  <MenuItem value="WARNING">WARNING</MenuItem>
                  <MenuItem value="ERROR">ERROR</MenuItem>
                  <MenuItem value="CRITICAL">CRITICAL</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="Message"
                fullWidth
                value={newLog.message}
                onChange={(e) => setNewLog({ ...newLog, message: e.target.value })}
              />
              <Button variant="contained" onClick={handleIngestLog}>
                Ingest
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Query Interface */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Query Logs
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <TextField
                label="Service Filter"
                value={filters.service}
                onChange={(e) => setFilters({ ...filters, service: e.target.value })}
              />
              <FormControl sx={{ minWidth: 120 }}>
                <InputLabel>Level</InputLabel>
                <Select
                  value={filters.level}
                  onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="DEBUG">DEBUG</MenuItem>
                  <MenuItem value="INFO">INFO</MenuItem>
                  <MenuItem value="WARNING">WARNING</MenuItem>
                  <MenuItem value="ERROR">ERROR</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="Limit"
                type="number"
                value={filters.limit}
                onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
              />
              <Button variant="contained" onClick={handleQueryLogs} disabled={loading}>
                {loading ? 'Querying...' : 'Query'}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            {logs.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6">Results ({logs.length})</Typography>
                {logs.map((log, idx) => (
                  <Paper key={idx} sx={{ p: 2, mt: 1, bgcolor: 'grey.100' }}>
                    <Typography variant="body2">
                      <strong>{log.level}</strong> [{log.service}] - {log.message}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {log.timestamp}
                    </Typography>
                  </Paper>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
