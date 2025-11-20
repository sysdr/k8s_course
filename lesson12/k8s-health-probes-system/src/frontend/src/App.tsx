import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Grid, Paper, Typography, Box, Chip, Alert,
  Table, TableBody, TableCell, TableHead, TableRow,
  LinearProgress, Card, CardContent, CircularProgress
} from '@mui/material';
import {
  CheckCircle, Error, Warning, Refresh, TrendingUp, 
  Storage, Speed, ShowChart, Assessment
} from '@mui/icons-material';
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, 
  XAxis, YAxis, Tooltip, LineChart, Line, Legend, Area, AreaChart
} from 'recharts';
import axios from 'axios';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  liveness: boolean;
  readiness: boolean;
  uptime: number;
  details?: any;
}

interface LogSummary {
  total_logs: number;
  by_level: Record<string, number>;
  by_service: Record<string, number>;
}

interface ServiceMetrics {
  name: string;
  logsReceived?: number;
  logsSent?: number;
  logsProcessed?: number;
  processingErrors?: number;
  bufferSize?: number;
  cacheHitRate?: number;
  modelLoadTime?: number;
  apiRequests?: number;
  activeConnections?: number;
  dbPoolSize?: number;
  processingTime?: number;
  requestDuration?: number;
}

interface TimeSeriesData {
  time: string;
  [key: string]: string | number;
}

// Color scheme: Green, Orange, Red, Yellow, Teal, Pink, Amber (NO PURPLE/BLUE)
const COLORS = ['#00C49F', '#FF8042', '#FF4444', '#FFBB28', '#00CED1', '#FF69B4', '#FFA500'];
const CHART_COLORS = {
  primary: '#00C49F',      // Teal/Green
  secondary: '#FF8042',    // Orange
  success: '#4CAF50',      // Green
  warning: '#FFA500',      // Amber
  error: '#FF4444',        // Red
  info: '#00CED1',         // Dark Turquoise
  accent: '#FF69B4'        // Pink
};

// Prometheus metrics parser
const parsePrometheusMetrics = (text: string): Record<string, number> => {
  const metrics: Record<string, number> = {};
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.trim() === '' || line.startsWith('#')) continue;
    
    const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([0-9.]+)/);
    if (match) {
      const [, name, value] = match;
      metrics[name] = parseFloat(value);
    }
  }
  
  return metrics;
};

const App: React.FC = () => {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [summary, setSummary] = useState<LogSummary | null>(null);
  const [metrics, setMetrics] = useState<Record<string, ServiceMetrics>>({});
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const timeSeriesRef = useRef<TimeSeriesData[]>([]);

  const fetchHealth = async () => {
    const serviceEndpoints = [
      { name: 'Log Collector', url: '/collector', key: 'collector' },
      { name: 'Log Processor', url: '/processor', key: 'processor' },
      { name: 'Analytics API', url: '/api', key: 'api' }
    ];

    const healthResults: ServiceHealth[] = [];

    for (const svc of serviceEndpoints) {
      try {
        const [liveRes, readyRes] = await Promise.all([
          axios.get(`${svc.url}/health/live`).catch(() => ({ data: null })),
          axios.get(`${svc.url}/health/ready`).catch(() => ({ data: null }))
        ]);

        const liveness = liveRes.data !== null;
        const readiness = readyRes.data !== null;

        healthResults.push({
          name: svc.name,
          status: liveness && readiness ? 'healthy' : liveness ? 'degraded' : 'unhealthy',
          liveness,
          readiness,
          uptime: liveRes.data?.details?.uptime_seconds || 0,
          details: liveRes.data?.details || {}
        });
      } catch {
        healthResults.push({
          name: svc.name,
          status: 'unhealthy',
          liveness: false,
          readiness: false,
          uptime: 0
        });
      }
    }

    setServices(healthResults);
  };

  const fetchMetrics = async () => {
    const serviceEndpoints = [
      { name: 'Log Collector', url: '/collector/metrics', key: 'collector' },
      { name: 'Log Processor', url: '/processor/metrics', key: 'processor' },
      { name: 'Analytics API', url: '/api/metrics', key: 'api' }
    ];

    const metricsData: Record<string, ServiceMetrics> = {};

    for (const svc of serviceEndpoints) {
      try {
        const response = await axios.get(svc.url, { 
          responseType: 'text',
          timeout: 5000
        });
        const parsed = parsePrometheusMetrics(response.data);
        
        if (svc.key === 'collector') {
          metricsData[svc.key] = {
            name: svc.name,
            logsReceived: parsed['logs_received_total'] || 0,
            logsSent: parsed['logs_sent_total'] || 0,
            bufferSize: parsed['log_buffer_size'] || 0,
            processingTime: parsed['log_processing_seconds_sum'] || 0
          };
        } else if (svc.key === 'processor') {
          metricsData[svc.key] = {
            name: svc.name,
            logsProcessed: parsed['logs_processed_total'] || 0,
            processingErrors: parsed['processing_errors_total'] || 0,
            cacheHitRate: parsed['cache_hit_rate'] || 0,
            modelLoadTime: parsed['model_load_seconds'] || 0,
            processingTime: parsed['log_processing_duration_seconds_sum'] || 0
          };
        } else if (svc.key === 'api') {
          metricsData[svc.key] = {
            name: svc.name,
            apiRequests: parsed['api_requests_total'] || 0,
            activeConnections: parsed['api_active_connections'] || 0,
            dbPoolSize: parsed['db_connection_pool_size'] || 0,
            requestDuration: parsed['api_request_duration_seconds_sum'] || 0
          };
        }
      } catch (err) {
        // Silently fail metrics fetch
        metricsData[svc.key] = { name: svc.name };
      }
    }

    setMetrics(metricsData);

    // Update time series data
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    const newDataPoint: TimeSeriesData = {
      time: timeStr,
      logsReceived: metricsData.collector?.logsReceived || 0,
      logsSent: metricsData.collector?.logsSent || 0,
      logsProcessed: metricsData.processor?.logsProcessed || 0,
      processingErrors: metricsData.processor?.processingErrors || 0,
      apiRequests: metricsData.api?.apiRequests || 0,
      activeConnections: metricsData.api?.activeConnections || 0
    };

    timeSeriesRef.current = [...timeSeriesRef.current, newDataPoint].slice(-20);
    setTimeSeries(timeSeriesRef.current);
  };

  const fetchSummary = async () => {
    try {
      const res = await axios.get('/api/api/logs/summary');
      setSummary(res.data);
    } catch (err) {
      setError('Failed to fetch log summary');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([fetchHealth(), fetchSummary(), fetchMetrics()]);
        setLastUpdate(new Date());
      } catch (err) {
        setError('Failed to fetch some data');
      }
      setLoading(false);
    };

    loadData();
    const interval = setInterval(loadData, 3000); // Update every 3 seconds for real-time
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle color="success" />;
      case 'degraded': return <Warning color="warning" />;
      default: return <Error color="error" />;
    }
  };

  const levelData = summary ? Object.entries(summary.by_level).map(([name, value]) => ({
    name, value
  })) : [];

  const serviceData = summary ? Object.entries(summary.by_service).map(([name, value]) => ({
    name, value
  })) : [];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: CHART_COLORS.primary }}>
          Kubernetes Health Probes System Dashboard
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            icon={<Refresh />}
            label={`Auto-refresh: 3s | Last: ${lastUpdate.toLocaleTimeString()}`}
            variant="outlined"
            size="small"
            sx={{ borderColor: CHART_COLORS.primary }}
          />
          {loading && <CircularProgress size={20} />}
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2, bgcolor: CHART_COLORS.primary }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        {/* Real-time Metrics Cards */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: CHART_COLORS.primary, color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <ShowChart sx={{ mr: 1 }} />
                <Typography variant="h6">Logs Received</Typography>
              </Box>
              <Typography variant="h3">{metrics.collector?.logsReceived?.toLocaleString() || 0}</Typography>
              <Typography variant="caption">Real-time from Log Collector</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: CHART_COLORS.secondary, color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TrendingUp sx={{ mr: 1 }} />
                <Typography variant="h6">Logs Processed</Typography>
              </Box>
              <Typography variant="h3">{metrics.processor?.logsProcessed?.toLocaleString() || 0}</Typography>
              <Typography variant="caption">ML Processing Complete</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: CHART_COLORS.warning, color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Speed sx={{ mr: 1 }} />
                <Typography variant="h6">API Requests</Typography>
              </Box>
              <Typography variant="h3">{metrics.api?.apiRequests?.toLocaleString() || 0}</Typography>
              <Typography variant="caption">Total API Calls</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: CHART_COLORS.error, color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Error sx={{ mr: 1 }} />
                <Typography variant="h6">Processing Errors</Typography>
              </Box>
              <Typography variant="h3">{metrics.processor?.processingErrors?.toLocaleString() || 0}</Typography>
              <Typography variant="caption">Error Count</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Health */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, borderLeft: `4px solid ${CHART_COLORS.primary}` }}>
            <Typography variant="h6" gutterBottom sx={{ color: CHART_COLORS.primary, fontWeight: 'bold' }}>
              Service Health Status & Operations
            </Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Service</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Liveness Probe</strong></TableCell>
                  <TableCell><strong>Readiness Probe</strong></TableCell>
                  <TableCell><strong>Uptime</strong></TableCell>
                  <TableCell><strong>Operations</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {services.map((svc) => {
                  let svcKey = 'collector';
                  if (svc.name === 'Log Processor') svcKey = 'processor';
                  else if (svc.name === 'Analytics API') svcKey = 'api';
                  const svcMetrics = metrics[svcKey];
                  return (
                    <TableRow key={svc.name}>
                      <TableCell><strong>{svc.name}</strong></TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getStatusIcon(svc.status)}
                          <Chip
                            label={svc.status}
                            sx={{
                              bgcolor: svc.status === 'healthy' ? CHART_COLORS.success : 
                                      svc.status === 'degraded' ? CHART_COLORS.warning : CHART_COLORS.error,
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={svc.liveness ? 'Pass' : 'Fail'}
                          sx={{
                            bgcolor: svc.liveness ? CHART_COLORS.success : CHART_COLORS.error,
                            color: 'white'
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={svc.readiness ? 'Pass' : 'Fail'}
                          sx={{
                            bgcolor: svc.readiness ? CHART_COLORS.success : CHART_COLORS.error,
                            color: 'white'
                          }}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{Math.round(svc.uptime)}s</TableCell>
                      <TableCell>
                        <Box>
                          {svc.name === 'Log Collector' && (
                            <Typography variant="caption" display="block">
                              Buffer: {metrics.collector?.bufferSize || 0} | 
                              Sent: {metrics.collector?.logsSent || 0}
                            </Typography>
                          )}
                          {svc.name === 'Log Processor' && (
                            <Typography variant="caption" display="block">
                              Cache Hit: {(metrics.processor?.cacheHitRate || 0).toFixed(2)}% | 
                              Model: {metrics.processor?.modelLoadTime ? `${metrics.processor.modelLoadTime.toFixed(1)}s` : 'N/A'}
                            </Typography>
                          )}
                          {svc.name === 'Analytics API' && (
                            <Typography variant="caption" display="block">
                              Connections: {metrics.api?.activeConnections || 0} | 
                              Pool: {metrics.api?.dbPoolSize || 0}/10
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Real-time Operations Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, borderLeft: `4px solid ${CHART_COLORS.secondary}` }}>
            <Typography variant="h6" gutterBottom sx={{ color: CHART_COLORS.secondary, fontWeight: 'bold' }}>
              Real-time Operations Metrics
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={timeSeries}>
                <defs>
                  <linearGradient id="colorLogsReceived" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.8}/>
                    <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorLogsProcessed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.secondary} stopOpacity={0.8}/>
                    <stop offset="95%" stopColor={CHART_COLORS.secondary} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="logsReceived" stackId="1" stroke={CHART_COLORS.primary} fillOpacity={1} fill="url(#colorLogsReceived)" name="Logs Received" />
                <Area type="monotone" dataKey="logsProcessed" stackId="1" stroke={CHART_COLORS.secondary} fillOpacity={1} fill="url(#colorLogsProcessed)" name="Logs Processed" />
                <Line type="monotone" dataKey="processingErrors" stroke={CHART_COLORS.error} strokeWidth={2} name="Errors" />
                <Line type="monotone" dataKey="apiRequests" stroke={CHART_COLORS.warning} strokeWidth={2} name="API Requests" />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* System Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, borderLeft: `4px solid ${CHART_COLORS.info}` }}>
            <Typography variant="h6" gutterBottom sx={{ color: CHART_COLORS.info, fontWeight: 'bold' }}>
              System Performance Metrics
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">Buffer Size</Typography>
                    <Typography variant="h5">{metrics.collector?.bufferSize || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">Cache Hit Rate</Typography>
                    <Typography variant="h5">{(metrics.processor?.cacheHitRate || 0).toFixed(1)}%</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">Active Connections</Typography>
                    <Typography variant="h5">{metrics.api?.activeConnections || 0}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">DB Pool Available</Typography>
                    <Typography variant="h5">{metrics.api?.dbPoolSize || 0}/10</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Log Distribution Charts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, borderLeft: `4px solid ${CHART_COLORS.accent}` }}>
            <Typography variant="h6" gutterBottom sx={{ color: CHART_COLORS.accent, fontWeight: 'bold' }}>
              Logs by Level Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={levelData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {levelData.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, borderLeft: `4px solid ${CHART_COLORS.warning}` }}>
            <Typography variant="h6" gutterBottom sx={{ color: CHART_COLORS.warning, fontWeight: 'bold' }}>
              Logs by Service
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={serviceData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill={CHART_COLORS.secondary} radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: CHART_COLORS.info, color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Storage sx={{ mr: 1 }} />
                <Typography variant="h6">Total Logs</Typography>
              </Box>
              <Typography variant="h3">{summary?.total_logs || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: CHART_COLORS.accent, color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Assessment sx={{ mr: 1 }} />
                <Typography variant="h6">Log Levels</Typography>
              </Box>
              <Typography variant="h3">{levelData.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: CHART_COLORS.success, color: 'white' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <CheckCircle sx={{ mr: 1 }} />
                <Typography variant="h6">Active Services</Typography>
              </Box>
              <Typography variant="h3">{services.filter(s => s.status === 'healthy').length}/{services.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default App;
