import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Typography, Grid, Box, TextField,
  Select, MenuItem, FormControl, InputLabel, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, Alert,
  Card, CardContent, Divider, LinearProgress, IconButton
} from '@mui/material';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area, CartesianGrid
} from 'recharts';
import { Refresh as RefreshIcon, TrendingUp as TrendingUpIcon } from '@mui/icons-material';
import axios from 'axios';
import { format, subHours } from 'date-fns';

// Determine API URL based on environment
// In production (docker), nginx proxies /api/ to backend
// In development, use localhost:8080 directly
const getApiUrl = () => {
  // Check if REACT_APP_API_URL is set (build-time env var)
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  // In production (served by nginx), use relative path
  // In development, use full localhost URL
  if (process.env.NODE_ENV === 'production') {
    return '/api';
  }
  return 'http://localhost:8080';
};

const API_URL = getApiUrl();

interface Log {
  id: number;
  timestamp: string;
  level: string;
  service: string;
  message: string;
  trace_id?: string;
  metadata?: Record<string, any>;
}

interface Stats {
  total_logs: number;
  logs_by_level: Record<string, number>;
  logs_by_service: Record<string, number>;
  time_range: {
    start: string;
    end: string;
  };
}

// Professional color scheme - no purple or blue
const COLORS = {
  ERROR: '#d32f2f',      // Red
  WARN: '#ed6c02',       // Orange
  WARNING: '#ed6c02',    // Orange
  INFO: '#2e7d32',       // Green
  DEBUG: '#616161',      // Gray
  FATAL: '#c62828',      // Dark Red
  default: '#757575'     // Gray
};

const LEVEL_COLORS = ['#2e7d32', '#ed6c02', '#d32f2f', '#616161', '#c62828'];

function App() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [filters, setFilters] = useState({
    service: '',
    level: '',
    limit: 100
  });

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.service) params.append('service', filters.service);
      if (filters.level) params.append('level', filters.level);
      params.append('limit', filters.limit.toString());

      const response = await axios.get(`${API_URL}/logs?${params}`);
      setLogs(response.data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats');
    }
  };

  const refreshData = () => {
    fetchLogs();
    fetchStats();
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(() => {
      refreshData();
    }, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [filters.service, filters.level, filters.limit]);

  const levelChartData = stats ? Object.entries(stats.logs_by_level)
    .map(([name, value]) => ({
      name: name.toUpperCase(),
      value,
      percentage: ((value / stats.total_logs) * 100).toFixed(1)
    }))
    .sort((a, b) => b.value - a.value) : [];

  const serviceChartData = stats ? Object.entries(stats.logs_by_service)
    .slice(0, 10)
    .map(([name, value]) => ({
      name: name.length > 15 ? name.substring(0, 15) + '...' : name,
      value,
      fullName: name
    }))
    .sort((a, b) => b.value - a.value) : [];

  const getLevelColor = (level: string): string => {
    return COLORS[level.toUpperCase() as keyof typeof COLORS] || COLORS.default;
  };

  const errorCount = stats?.logs_by_level?.ERROR || 0;
  const warnCount = stats?.logs_by_level?.WARN || stats?.logs_by_level?.WARNING || 0;
  const infoCount = stats?.logs_by_level?.INFO || 0;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', pb: 4 }}>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
              Log Analytics Platform
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time log monitoring and analysis dashboard
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Last updated: {format(lastUpdate, 'HH:mm:ss')}
            </Typography>
            <IconButton onClick={refreshData} color="primary" size="small">
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading && <LinearProgress sx={{ mb: 3 }} />}

        <Grid container spacing={3}>
          {/* Key Metrics Cards */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'success.main', color: 'white' }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                  Total Logs (24h)
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {stats?.total_logs?.toLocaleString() || '0'}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <TrendingUpIcon sx={{ fontSize: 16 }} />
                  <Typography variant="caption" sx={{ opacity: 0.9 }}>
                    Active monitoring
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'error.main', color: 'white' }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                  Errors
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {errorCount.toLocaleString()}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9 }}>
                  {stats?.total_logs ? ((errorCount / stats.total_logs) * 100).toFixed(2) : '0'}% of total
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'warning.main', color: 'white' }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                  Warnings
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {warnCount.toLocaleString()}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9 }}>
                  {stats?.total_logs ? ((warnCount / stats.total_logs) * 100).toFixed(2) : '0'}% of total
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: '#0097a7', color: 'white' }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 1 }}>
                  Active Services
                </Typography>
                <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
                  {stats ? Object.keys(stats.logs_by_service).length : '0'}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9 }}>
                  Services logging
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Logs by Level Chart */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Log Distribution by Level
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={levelChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                  >
                    {levelChartData.map((entry, index) => (
                      <Cell key={entry.name} fill={getLevelColor(entry.name)} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => value.toLocaleString()} />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {levelChartData.map((item) => (
                  <Box key={item.name} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          bgcolor: getLevelColor(item.name)
                        }}
                      />
                      <Typography variant="body2">{item.name}</Typography>
                    </Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {item.value.toLocaleString()} ({item.percentage}%)
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>

          {/* Top Services Chart */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Top Services by Log Volume
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={serviceChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={11}
                  />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number, name: string, props: any) => [
                      value.toLocaleString(),
                      props.payload.fullName
                    ]}
                  />
                  <Bar dataKey="value" fill="#2e7d32" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Filters */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Filter Logs
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Service Name"
                    value={filters.service}
                    onChange={(e) => setFilters({ ...filters, service: e.target.value })}
                    placeholder="Filter by service..."
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>Log Level</InputLabel>
                    <Select
                      value={filters.level}
                      label="Log Level"
                      onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                    >
                      <MenuItem value="">All Levels</MenuItem>
                      <MenuItem value="DEBUG">DEBUG</MenuItem>
                      <MenuItem value="INFO">INFO</MenuItem>
                      <MenuItem value="WARN">WARN</MenuItem>
                      <MenuItem value="WARNING">WARNING</MenuItem>
                      <MenuItem value="ERROR">ERROR</MenuItem>
                      <MenuItem value="FATAL">FATAL</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Result Limit"
                    value={filters.limit}
                    onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) || 100 })}
                    inputProps={{ min: 10, max: 1000 }}
                    variant="outlined"
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Logs Table */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Recent Log Entries
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Showing {logs.length} of {stats?.total_logs || 0} total logs
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <TableContainer sx={{ maxHeight: 600 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Timestamp</TableCell>
                      <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Level</TableCell>
                      <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Service</TableCell>
                      <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Message</TableCell>
                      <TableCell sx={{ fontWeight: 600, bgcolor: 'background.paper' }}>Trace ID</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {logs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                          <Typography color="text.secondary">No logs found matching the current filters</Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      logs.map((log) => (
                        <TableRow key={log.id} hover>
                          <TableCell>
                            <Typography variant="body2">
                              {format(new Date(log.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={log.level}
                              size="small"
                              sx={{
                                bgcolor: getLevelColor(log.level),
                                color: 'white',
                                fontWeight: 600,
                                minWidth: 70
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {log.service}
                            </Typography>
                          </TableCell>
                          <TableCell sx={{ maxWidth: 500 }}>
                            <Typography
                              variant="body2"
                              sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                              title={log.message}
                            >
                              {log.message}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                              {log.trace_id || '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>

        {/* Footer */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Log Analytics Platform Dashboard • Auto-refreshing every 10 seconds
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default App;
