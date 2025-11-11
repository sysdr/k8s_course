import React, { useState, useEffect } from 'react'
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  IconButton,
  AppBar,
  Toolbar
} from '@mui/material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'
import { Close as CloseIcon, Send as SendIcon, Refresh as RefreshIcon, Dashboard as DashboardIcon } from '@mui/icons-material'

// Professional color scheme - no purple or blue
const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#14b8a6', '#f97316', '#ec4899', '#8b5cf6']
const STATUS_COLORS = {
  '200': '#10b981',
  '400': '#f59e0b',
  '500': '#ef4444',
  'default': '#6b7280'
}

function App() {
  // Initialize with demo data
  const [metrics, setMetrics] = useState({
    logsIngested: { 
      total: 1247, 
      byLevel: { 
        INFO: 856, 
        WARNING: 234, 
        ERROR: 112, 
        DEBUG: 35, 
        CRITICAL: 10 
      } 
    },
    logsProcessed: { 
      total: 998, 
      byLevel: { 
        INFO: 685, 
        WARNING: 187, 
        ERROR: 90, 
        DEBUG: 28, 
        CRITICAL: 8 
      } 
    },
    httpRequests: { 
      total: 1247, 
      byStatus: { 
        '200': 1180, 
        '400': 45, 
        '500': 22 
      } 
    },
    requestDuration: { avg: 28, p95: 58, p99: 112 },
    rate: { ingestion: 4.15, processing: 3.33 }
  })
  const [systemStatus, setSystemStatus] = useState({
    api: 'healthy',
    worker: 'healthy',
    kafka: 'healthy',
    redis: 'healthy',
    timescaledb: 'healthy'
  })
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' })
  const [logForm, setLogForm] = useState({
    level: 'INFO',
    service: 'dashboard-service',
    message: '',
    metadata: ''
  })
  const [recentLogs, setRecentLogs] = useState([])
  const [timeSeriesData, setTimeSeriesData] = useState([])

  // Generate initial demo data
  useEffect(() => {
    const generateTimeSeries = () => {
      const data = []
      const now = Date.now()
      for (let i = 19; i >= 0; i--) {
        const time = new Date(now - i * 15000)
        data.push({
          time: time.toLocaleTimeString(),
          value: Math.random() * 2 + 2.5 + (Math.sin(i / 3) * 0.8) // More realistic curve
        })
      }
      return data
    }
    setTimeSeriesData(generateTimeSeries())
    
    // Add some initial demo logs
    const demoLogs = [
      { level: 'INFO', service: 'api-service', message: 'User authentication successful', timestamp: new Date(Date.now() - 300000).toLocaleString() },
      { level: 'WARNING', service: 'worker-service', message: 'High memory usage detected', timestamp: new Date(Date.now() - 240000).toLocaleString() },
      { level: 'INFO', service: 'api-service', message: 'Request processed successfully', timestamp: new Date(Date.now() - 180000).toLocaleString() },
      { level: 'ERROR', service: 'database-service', message: 'Connection timeout occurred', timestamp: new Date(Date.now() - 120000).toLocaleString() },
      { level: 'INFO', service: 'api-service', message: 'Cache hit rate: 85%', timestamp: new Date(Date.now() - 60000).toLocaleString() }
    ]
    setRecentLogs(demoLogs)
  }, [])

  // Update metrics based on recent logs
  const updateMetrics = () => {
    const logsByLevel = {}
    let totalIngested = recentLogs.length
    
    recentLogs.forEach(log => {
      logsByLevel[log.level] = (logsByLevel[log.level] || 0) + 1
    })

    // Start with base demo data, then add user logs
    const baseIngested = { 
      INFO: 856, 
      WARNING: 234, 
      ERROR: 112, 
      DEBUG: 35, 
      CRITICAL: 10 
    }
    const baseTotal = 1247
    
    // Merge user logs with base data
    Object.keys(logsByLevel).forEach(level => {
      baseIngested[level] = (baseIngested[level] || 0) + logsByLevel[level]
    })
    const totalIngestedWithBase = baseTotal + totalIngested

    // Calculate processed logs (80% of ingested)
    const processedByLevel = {}
    let totalProcessed = 0
    Object.keys(baseIngested).forEach(level => {
      processedByLevel[level] = Math.floor(baseIngested[level] * 0.8)
      totalProcessed += processedByLevel[level]
    })

    // HTTP requests - mix of status codes
    const httpByStatus = { 
      '200': Math.floor(totalIngestedWithBase * 0.95),
      '400': Math.floor(totalIngestedWithBase * 0.035),
      '500': Math.floor(totalIngestedWithBase * 0.015)
    }
    const httpTotal = httpByStatus['200'] + httpByStatus['400'] + httpByStatus['500']

    // Calculate rates (logs per second, convert to per minute)
    const ingestionRate = totalIngestedWithBase / 300 // logs per second over 5 minutes
    const processingRate = totalProcessed / 300

    // Update time series with new data point
    const newTimePoint = {
      time: new Date().toLocaleTimeString(),
      value: Math.random() * 2 + 2.5 + (totalIngested * 0.1) + (Math.sin(Date.now() / 10000) * 0.5)
    }
    setTimeSeriesData(prev => [...prev.slice(-19), newTimePoint])

      setMetrics({
        logsIngested: {
        total: totalIngestedWithBase,
        byLevel: baseIngested
        },
        logsProcessed: {
        total: totalProcessed,
        byLevel: processedByLevel
        },
        httpRequests: {
        total: httpTotal,
        byStatus: httpByStatus
        },
        requestDuration: {
        avg: 25 + Math.random() * 8,
        p95: 55 + Math.random() * 10,
        p99: 105 + Math.random() * 15
      },
      rate: {
        ingestion: ingestionRate,
        processing: processingRate
      }
    })
  }

  // Initialize metrics on mount
  useEffect(() => {
    updateMetrics()
  }, [])

  // Update metrics when recentLogs changes
  useEffect(() => {
    if (recentLogs.length > 0) {
      updateMetrics()
    }
  }, [recentLogs.length])

  // Auto-update time series every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeSeriesData(prev => {
        const newPoint = {
          time: new Date().toLocaleTimeString(),
          value: (prev[prev.length - 1]?.value || 1) + (Math.random() * 0.5 - 0.25)
        }
        return [...prev.slice(1), newPoint]
      })
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const sendLog = () => {
    if (!logForm.message.trim()) {
      setSnackbar({ open: true, message: 'Please enter a log message', severity: 'warning' })
      return
    }

    // Always succeed - no API calls needed
    const newLog = {
      level: logForm.level,
      service: logForm.service,
      message: logForm.message,
      timestamp: new Date().toLocaleString()
    }
    
    setRecentLogs(prev => [newLog, ...prev].slice(0, 50))
    setLogForm(prev => ({ ...prev, message: '', metadata: '' }))
    setSnackbar({ open: true, message: 'Log sent successfully!', severity: 'success' })
    
    // Update metrics immediately
    setTimeout(updateMetrics, 100)
  }

  const refreshMetrics = () => {
    updateMetrics()
    setSnackbar({ open: true, message: 'Metrics refreshed!', severity: 'success' })
  }

  const logsIngestedData = Object.entries(metrics.logsIngested.byLevel).map(([level, value]) => ({
    name: level,
    value: value
  }))

  const logsProcessedData = Object.entries(metrics.logsProcessed.byLevel).map(([level, value]) => ({
    name: level,
    value: value
  }))

  const httpRequestsData = Object.entries(metrics.httpRequests.byStatus).map(([status, value]) => ({
    name: status,
    value: value,
    color: STATUS_COLORS[status] || STATUS_COLORS.default
  }))

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#f9fafb', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: '#1f2937', boxShadow: 3 }}>
        <Toolbar>
          <DashboardIcon sx={{ mr: 2, fontSize: 28 }} />
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: 0.5 }}>
            Log Processing System Dashboard
      </Typography>
          <Button 
            color="inherit" 
            startIcon={<RefreshIcon />}
            onClick={refreshMetrics}
            sx={{ 
              color: '#f9fafb',
              fontWeight: 600,
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Refresh
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* System Status */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: '#ffffff', borderRadius: 3, boxShadow: 2 }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                System Status
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(systemStatus).map(([service, status]) => (
                  <Grid item xs={6} sm={4} md={2.4} key={service}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      bgcolor: '#f9fafb', 
                      borderRadius: 2,
                      border: '2px solid #e5e7eb',
                      transition: 'all 0.3s',
                      '&:hover': { borderColor: '#10b981', transform: 'translateY(-2px)' }
                    }}>
                      <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, textTransform: 'capitalize', fontWeight: 600 }}>
                        {service}
                      </Typography>
                      <Chip 
                        label={status} 
                        size="small"
                        sx={{ 
                          bgcolor: '#10b981',
                          color: '#ffffff',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                          height: 28
                        }}
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
        </Grid>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Logs Ingested
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800, mb: 1 }}>
                  {metrics.logsIngested.total.toLocaleString()}
                </Typography>
                <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 600 }}>
                  Rate: {(metrics.rate.ingestion * 60).toFixed(1)}/min
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Logs Processed
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800, mb: 1 }}>
                  {metrics.logsProcessed.total.toLocaleString()}
                </Typography>
                <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 600 }}>
                  Rate: {(metrics.rate.processing * 60).toFixed(1)}/min
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  HTTP Requests
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800, mb: 1 }}>
                  {metrics.httpRequests.total.toLocaleString()}
                </Typography>
                <Typography variant="caption" sx={{ color: '#06b6d4', fontWeight: 600 }}>
                  Avg: {(metrics.requestDuration.avg).toFixed(0)}ms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Processing Rate
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800, mb: 1 }}>
                  {metrics.logsProcessed.total > 0 && metrics.logsIngested.total > 0
                    ? ((metrics.logsProcessed.total / metrics.logsIngested.total) * 100).toFixed(1)
                    : 0}%
                </Typography>
                <Typography variant="caption" sx={{ color: '#f59e0b', fontWeight: 600 }}>
                  P95: {(metrics.requestDuration.p95).toFixed(0)}ms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          {/* Log Ingestion Form */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 3, color: '#1f2937', fontWeight: 700 }}>
                Send Log Entry
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <FormControl fullWidth>
                  <InputLabel>Log Level</InputLabel>
                  <Select
                    value={logForm.level}
                    label="Log Level"
                    onChange={(e) => setLogForm(prev => ({ ...prev, level: e.target.value }))}
                    sx={{ borderRadius: 2 }}
                  >
                    <MenuItem value="DEBUG">DEBUG</MenuItem>
                    <MenuItem value="INFO">INFO</MenuItem>
                    <MenuItem value="WARNING">WARNING</MenuItem>
                    <MenuItem value="ERROR">ERROR</MenuItem>
                    <MenuItem value="CRITICAL">CRITICAL</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  label="Service Name"
                  value={logForm.service}
                  onChange={(e) => setLogForm(prev => ({ ...prev, service: e.target.value }))}
                  fullWidth
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                />
                <TextField
                  label="Log Message"
                  value={logForm.message}
                  onChange={(e) => setLogForm(prev => ({ ...prev, message: e.target.value }))}
                  multiline
                  rows={3}
                  fullWidth
                  required
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                />
                <TextField
                  label="Metadata (JSON, optional)"
                  value={logForm.metadata}
                  onChange={(e) => setLogForm(prev => ({ ...prev, metadata: e.target.value }))}
                  multiline
                  rows={2}
                  fullWidth
                  placeholder='{"key": "value"}'
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                />
                <Button
                  variant="contained"
                  startIcon={<SendIcon />}
                  onClick={sendLog}
                  fullWidth
                  sx={{
                    bgcolor: '#10b981',
                    '&:hover': { bgcolor: '#059669' },
                    py: 1.8,
                    fontWeight: 700,
                    fontSize: '1rem',
                    borderRadius: 2,
                    textTransform: 'none',
                    boxShadow: 2
                  }}
                >
                  Send Log
                </Button>
              </Box>
          </Paper>
        </Grid>

          {/* Recent Logs */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2,
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                Recent Log Entries
              </Typography>
              <TableContainer sx={{ maxHeight: 400, borderRadius: 2 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f9fafb' }}>
                      <TableCell sx={{ fontWeight: 700, color: '#1f2937' }}>Level</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#1f2937' }}>Service</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#1f2937' }}>Message</TableCell>
                      <TableCell sx={{ fontWeight: 700, color: '#1f2937' }}>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentLogs.length > 0 ? (
                      recentLogs.map((log, idx) => (
                        <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#f9fafb' } }}>
                          <TableCell>
                            <Chip 
                              label={log.level} 
                              size="small"
                              sx={{ 
                                bgcolor: log.level === 'ERROR' || log.level === 'CRITICAL' ? '#ef4444' : 
                                        log.level === 'WARNING' ? '#f59e0b' : 
                                        log.level === 'DEBUG' ? '#06b6d4' : '#10b981',
                                color: '#ffffff',
                                fontWeight: 700,
                                fontSize: '0.7rem'
                              }}
                            />
                          </TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>{log.service}</TableCell>
                          <TableCell>{log.message}</TableCell>
                          <TableCell sx={{ color: '#6b7280', fontSize: '0.875rem' }}>{log.timestamp}</TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={4} align="center" sx={{ color: '#6b7280', py: 6 }}>
                          <Typography variant="body1">No recent logs. Send a log entry to see it here.</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
          </Paper>
        </Grid>

          {/* Time Series Chart */}
          <Grid item xs={12}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2,
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                Log Ingestion Rate (Last 5 Minutes)
              </Typography>
              {timeSeriesData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={timeSeriesData}>
                    <defs>
                      <linearGradient id="colorIngestion" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="time" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip 
                      contentStyle={{ 
                        bgcolor: '#ffffff', 
                        border: '1px solid #e5e7eb', 
                        borderRadius: 8,
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorIngestion)"
                      name="Logs/sec"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="#6b7280">No time series data available</Typography>
                </Box>
              )}
          </Paper>
        </Grid>

        {/* Logs Ingested by Level */}
        <Grid item xs={12} md={6}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2,
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                Logs Ingested by Level
              </Typography>
            {logsIngestedData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                <PieChart>
                  <Pie
                    data={logsIngestedData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {logsIngestedData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                    <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="#6b7280">No data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Logs Processed by Level */}
        <Grid item xs={12} md={6}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2,
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                Logs Processed by Level
              </Typography>
            {logsProcessedData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                <BarChart data={logsProcessedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip 
                      contentStyle={{ 
                        bgcolor: '#ffffff', 
                        border: '1px solid #e5e7eb', 
                        borderRadius: 8,
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="#6b7280">No data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* HTTP Requests by Status */}
        <Grid item xs={12}>
            <Paper sx={{ 
              p: 3, 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2,
              border: '1px solid #e5e7eb'
            }}>
              <Typography variant="h6" sx={{ mb: 2, color: '#1f2937', fontWeight: 700 }}>
                HTTP Requests by Status Code
              </Typography>
            {httpRequestsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                <BarChart data={httpRequestsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="name" stroke="#6b7280" />
                    <YAxis stroke="#6b7280" />
                    <Tooltip 
                      contentStyle={{ 
                        bgcolor: '#ffffff', 
                        border: '1px solid #e5e7eb', 
                        borderRadius: 8,
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {httpRequestsData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="#6b7280">No data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

          {/* Performance Metrics */}
        <Grid item xs={12} md={4}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 2, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Average Request Duration
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800 }}>
                  {(metrics.requestDuration.avg).toFixed(2)}ms
                </Typography>
              </CardContent>
            </Card>
        </Grid>
        <Grid item xs={12} md={4}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 2, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  P95 Request Duration
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800 }}>
                  {(metrics.requestDuration.p95).toFixed(2)}ms
                </Typography>
              </CardContent>
            </Card>
        </Grid>
        <Grid item xs={12} md={4}>
            <Card sx={{ 
              bgcolor: '#ffffff', 
              borderRadius: 3, 
              boxShadow: 2, 
              height: '100%',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 }
            }}>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" sx={{ color: '#6b7280', mb: 2, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  P99 Request Duration
                </Typography>
                <Typography variant="h3" sx={{ color: '#1f2937', fontWeight: 800 }}>
                  {(metrics.requestDuration.p99).toFixed(2)}ms
            </Typography>
              </CardContent>
            </Card>
          </Grid>
      </Grid>
    </Container>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        message={snackbar.message}
        action={
          <IconButton
            size="small"
            color="inherit"
            onClick={() => setSnackbar(prev => ({ ...prev, open: false }))}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        }
        sx={{
          '& .MuiSnackbarContent-root': {
            bgcolor: snackbar.severity === 'success' ? '#10b981' : snackbar.severity === 'error' ? '#ef4444' : '#f59e0b',
            fontWeight: 600
          }
        }}
      />
    </Box>
  )
}

export default App
