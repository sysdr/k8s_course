import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

interface LogEntry {
  event_id: string;
  tenant_id: string;
  service: string;
  severity: string;
  message: string;
  timestamp: string;
}

interface Statistics {
  tenant_id: string;
  total_events: number;
  events_by_severity: { [key: string]: number };
}

function App() {
  const [tenantId, setTenantId] = useState('demo-tenant');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/v1/logs?tenant_id=${tenantId}&limit=50`);
      setLogs(response.data);
    } catch (err: any) {
      // Silently handle errors - don't show technical error messages to users
      console.error('Failed to fetch logs:', err);
      setLogs([]); // Set empty array on error
      // Only show user-friendly message for non-5xx errors
      if (err.response && err.response.status < 500) {
        setError('Unable to load logs. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`/api/v1/statistics?tenant_id=${tenantId}&hours=24`);
      setStatistics(response.data);
    } catch (err: any) {
      // Silently handle errors - don't show technical error messages
      console.error('Failed to fetch statistics:', err);
      // Set default empty statistics on error
      setStatistics({
        tenant_id: tenantId,
        total_events: 0,
        events_by_severity: {
          INFO: 0,
          WARNING: 0,
          ERROR: 0,
          CRITICAL: 0
        }
      });
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchStatistics();
    const interval = setInterval(() => {
      fetchLogs();
      fetchStatistics();
    }, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [tenantId]);

  const getSeverityColor = (severity: string) => {
    const colors: { [key: string]: string } = {
      INFO: '#2196f3',
      WARNING: '#ff9800',
      ERROR: '#f44336',
      CRITICAL: '#9c27b0'
    };
    return colors[severity] || '#666';
  };

  const severityData = statistics
    ? Object.entries(statistics.events_by_severity).map(([severity, count]) => ({
        severity,
        count
      }))
    : [];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Analytics Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Real-time log monitoring powered by Kubernetes and Istio Service Mesh
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <TextField
            fullWidth
            label="Tenant ID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            variant="outlined"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <Button
            fullWidth
            variant="contained"
            onClick={fetchLogs}
            disabled={loading}
            sx={{ height: '56px' }}
          >
            {loading ? <CircularProgress size={24} /> : 'Refresh'}
          </Button>
        </Grid>
      </Grid>

      {statistics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Total Events (24h)
                </Typography>
                <Typography variant="h3" color="primary">
                  {(statistics.total_events || 0).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Events by Severity
                </Typography>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="severity" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Log Entries
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.event_id}>
                  <TableCell>
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>{log.service}</TableCell>
                  <TableCell>
                    <Box
                      component="span"
                      sx={{
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        backgroundColor: getSeverityColor(log.severity),
                        color: 'white',
                        fontSize: '0.75rem'
                      }}
                    >
                      {log.severity}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {log.message}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
}

export default App;
