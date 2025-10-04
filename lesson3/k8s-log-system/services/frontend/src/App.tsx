import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Typography, Grid, Card, CardContent,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, CircularProgress, Box, TextField, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

const API_BASE = '/api';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

interface LogEntry {
  timestamp: string;
  level: string;
  service: string;
  message: string;
  trace_id?: string;
  user_id?: string;
}

interface Stats {
  total_received: number;
  total_processed: number;
  buffer_size: number;
  cache_hit_rate: number;
  uptime_seconds: number;
}

const App: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState('');
  const [filterService, setFilterService] = useState('');

  useEffect(() => {
    fetchLogs();
    fetchStats();
    
    const logsInterval = setInterval(fetchLogs, 5000);
    const statsInterval = setInterval(fetchStats, 2000);
    
    return () => {
      clearInterval(logsInterval);
      clearInterval(statsInterval);
    };
  }, [filterLevel, filterService]);

  const fetchLogs = async () => {
    try {
      const params: any = { limit: 100 };
      if (filterLevel) params.level = filterLevel;
      if (filterService) params.service = filterService;
      
      const response = await axios.get(`${API_BASE}/logs/search`, { params });
      setLogs(response.data.results || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const getLevelColor = (level: string): "error" | "warning" | "info" | "success" => {
    switch (level) {
      case 'ERROR': return 'error';
      case 'WARNING': return 'warning';
      case 'INFO': return 'info';
      default: return 'success';
    }
  };

  const logLevelDistribution = React.useMemo(() => {
    const distribution: { [key: string]: number } = {};
    logs.forEach(log => {
      distribution[log.level] = (distribution[log.level] || 0) + 1;
    });
    return Object.entries(distribution).map(([name, value]) => ({ name, value }));
  }, [logs]);

  const serviceDistribution = React.useMemo(() => {
    const distribution: { [key: string]: number } = {};
    logs.forEach(log => {
      distribution[log.service] = (distribution[log.service] || 0) + 1;
    });
    return Object.entries(distribution).map(([name, value]) => ({ name, value }));
  }, [logs]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Aggregation Dashboard
      </Typography>
      
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Total Received</Typography>
                <Typography variant="h4">{stats.total_received.toLocaleString()}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Total Processed</Typography>
                <Typography variant="h4">{stats.total_processed.toLocaleString()}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Buffer Size</Typography>
                <Typography variant="h4">{stats.buffer_size}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>Cache Hit Rate</Typography>
                <Typography variant="h4">{stats.cache_hit_rate.toFixed(1)}%</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Log Level Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={logLevelDistribution} cx="50%" cy="50%" labelLine={false} label outerRadius={80} fill="#8884d8" dataKey="value">
                  {logLevelDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Service Distribution</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={serviceDistribution} cx="50%" cy="50%" labelLine={false} label outerRadius={80} fill="#8884d8" dataKey="value">
                  {serviceDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Level</InputLabel>
              <Select value={filterLevel} label="Level" onChange={(e) => setFilterLevel(e.target.value)}>
                <MenuItem value="">All</MenuItem>
                <MenuItem value="INFO">INFO</MenuItem>
                <MenuItem value="WARNING">WARNING</MenuItem>
                <MenuItem value="ERROR">ERROR</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Service</InputLabel>
              <Select value={filterService} label="Service" onChange={(e) => setFilterService(e.target.value)}>
                <MenuItem value="">All</MenuItem>
                <MenuItem value="api-gateway">API Gateway</MenuItem>
                <MenuItem value="auth-service">Auth Service</MenuItem>
                <MenuItem value="payment-service">Payment Service</MenuItem>
                <MenuItem value="database">Database</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Service</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Trace ID</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log, index) => (
                  <TableRow key={index}>
                    <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip label={log.level} color={getLevelColor(log.level)} size="small" />
                    </TableCell>
                    <TableCell>{log.service}</TableCell>
                    <TableCell>{log.message}</TableCell>
                    <TableCell>{log.trace_id}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Container>
  );
};

export default App;
