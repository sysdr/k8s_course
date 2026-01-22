import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import { LokiService } from './services/LokiService';
import LogViewer from './components/LogViewer';
import './App.css';

function App() {
  const [logs, setLogs] = useState([]);
  const [errorRateData, setErrorRateData] = useState([]);
  const [serviceFilter, setServiceFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [stats, setStats] = useState({
    totalLogs: 0,
    errors: 0,
    warnings: 0,
    info: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const lokiService = new LokiService('http://localhost:3100');

  useEffect(() => {
    fetchLogs();
    fetchErrorRates();
    
    // Refresh every 15 seconds
    const interval = setInterval(() => {
      fetchLogs();
      fetchErrorRates();
    }, 15000);

    return () => clearInterval(interval);
  }, [serviceFilter, severityFilter]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const query = buildLogQLQuery();
      const data = await lokiService.queryLogs(query, 100);
      setLogs(data);
      calculateStats(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      setError('Failed to connect to Loki. Make sure the logging stack is running.');
    } finally {
      setLoading(false);
    }
  };

  const fetchErrorRates = async () => {
    try {
      const services = ['api-gateway', 'order-service', 'payment-service'];
      const rates = [];
      
      for (const service of services) {
        const query = `sum(rate({service="${service}",severity="error"}[5m]))`;
        const rate = await lokiService.queryRange(query, 3600);
        rates.push({
          service,
          data: rate
        });
      }
      
      setErrorRateData(rates);
    } catch (err) {
      console.error('Failed to fetch error rates:', err);
    }
  };

  const buildLogQLQuery = () => {
    let query = '{namespace="logging-system"';
    
    if (serviceFilter !== 'all') {
      query += `,service="${serviceFilter}"`;
    }
    
    if (severityFilter !== 'all') {
      query += `,severity="${severityFilter}"`;
    }
    
    query += '}';
    return query;
  };

  const calculateStats = (logData) => {
    const stats = {
      totalLogs: logData.length,
      errors: logData.filter(log => log.severity === 'error').length,
      warnings: logData.filter(log => log.severity === 'warning').length,
      info: logData.filter(log => log.severity === 'info').length
    };
    setStats(stats);
  };

  return (
    <div className="App">
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Kubernetes Logging Dashboard - Loki Stack
          </Typography>
          <Chip 
            label={loading ? 'Refreshing...' : 'Live'} 
            color={loading ? 'default' : 'success'}
            size="small"
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <div>
                    <Typography color="textSecondary" gutterBottom>
                      Total Logs
                    </Typography>
                    <Typography variant="h4">
                      {stats.totalLogs}
                    </Typography>
                  </div>
                  <InfoIcon color="primary" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <div>
                    <Typography color="textSecondary" gutterBottom>
                      Errors
                    </Typography>
                    <Typography variant="h4" color="error">
                      {stats.errors}
                    </Typography>
                  </div>
                  <ErrorIcon color="error" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <div>
                    <Typography color="textSecondary" gutterBottom>
                      Warnings
                    </Typography>
                    <Typography variant="h4" color="warning.main">
                      {stats.warnings}
                    </Typography>
                  </div>
                  <WarningIcon color="warning" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <div>
                    <Typography color="textSecondary" gutterBottom>
                      Info
                    </Typography>
                    <Typography variant="h4" color="info.main">
                      {stats.info}
                    </Typography>
                  </div>
                  <InfoIcon color="info" sx={{ fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Service</InputLabel>
                <Select
                  value={serviceFilter}
                  label="Service"
                  onChange={(e) => setServiceFilter(e.target.value)}
                >
                  <MenuItem value="all">All Services</MenuItem>
                  <MenuItem value="api-gateway">API Gateway</MenuItem>
                  <MenuItem value="order-service">Order Service</MenuItem>
                  <MenuItem value="payment-service">Payment Service</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  label="Severity"
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="warning">Warning</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {/* Error Rate Chart */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Error Rate by Service (per 5 minutes)
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                type="category"
                allowDuplicatedCategory={false}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              {errorRateData.map((service) => (
                <Line
                  key={service.service}
                  dataKey="value"
                  data={service.data}
                  name={service.service}
                  type="monotone"
                  stroke={`#${Math.floor(Math.random()*16777215).toString(16)}`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </Paper>

        {/* Log Viewer */}
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Recent Logs
          </Typography>
          <LogViewer logs={logs} loading={loading} />
        </Paper>
      </Container>
    </div>
  );
}

export default App;
