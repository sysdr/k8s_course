import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import LogSubmitForm from './components/LogSubmitForm';
import { fetchSummary, fetchRecentLogs, fetchErrors } from './services/api';

function App() {
  const [summary, setSummary] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, logsData, errorsData] = await Promise.all([
        fetchSummary(),
        fetchRecentLogs(),
        fetchErrors()
      ]);
      
      setSummary(summaryData);
      // Ensure logs are sorted by timestamp (most recent first)
      const sortedLogs = logsData.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeB - timeA; // Descending order (newest first)
      });
      setRecentLogs(sortedLogs);
      setErrors(errorsData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !summary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  const chartData = summary ? [
    { name: 'DEBUG', count: summary.by_level?.DEBUG || 0 },
    { name: 'INFO', count: summary.by_level?.INFO || 0 },
    { name: 'WARN', count: summary.by_level?.WARN || 0 },
    { name: 'ERROR', count: summary.by_level?.ERROR || 0 },
    { name: 'FATAL', count: summary.by_level?.FATAL || 0 }
  ] : [
    { name: 'DEBUG', count: 0 },
    { name: 'INFO', count: 0 },
    { name: 'WARN', count: 0 },
    { name: 'ERROR', count: 0 },
    { name: 'FATAL', count: 0 }
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Analytics Dashboard
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Logs Processed
              </Typography>
              <Typography variant="h4">
                {summary?.total_processed || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Logs by Level
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Submit New Log
            </Typography>
            <LogSubmitForm onSubmit={loadData} />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Recent Errors ({errors.length})
            </Typography>
            {errors.map((error, index) => (
              <Alert severity="error" key={index} sx={{ mb: 1 }}>
                <strong>{error.service}:</strong> {error.message}
              </Alert>
            ))}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Typography variant="h6" sx={{ p: 2 }}>
              Recent Logs
            </Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Service</TableCell>
                  <TableCell>Message</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">No logs available</TableCell>
                  </TableRow>
                ) : (
                  recentLogs.map((log, index) => {
                    // Handle both ISO string and Unix timestamp formats
                    let date;
                    if (typeof log.timestamp === 'string') {
                      date = new Date(log.timestamp);
                    } else if (typeof log.timestamp === 'number') {
                      // If timestamp is in seconds, convert to milliseconds
                      date = new Date(log.timestamp > 1e12 ? log.timestamp : log.timestamp * 1000);
                    } else {
                      date = new Date();
                    }
                    
                    return (
                      <TableRow key={index}>
                        <TableCell>{isNaN(date.getTime()) ? 'Invalid Date' : date.toLocaleString()}</TableCell>
                        <TableCell>{log.level}</TableCell>
                        <TableCell>{log.service}</TableCell>
                        <TableCell>{log.message}</TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
