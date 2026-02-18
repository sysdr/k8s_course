import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import { fetchAnalyticsSummary, fetchRecentLogs } from './services/api';

interface MetricsSummary {
  source: string;
  metrics: {
    ERROR?: string;
    WARN?: string;
    INFO?: string;
  };
}

const App: React.FC = () => {
  const [summaries, setSummaries] = useState<MetricsSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchAnalyticsSummary();
        setSummaries(data.summaries || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to load analytics data');
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getTotalLogs = () => {
    return summaries.reduce((total, s) => {
      const sum = Object.values(s.metrics).reduce((a, b) => a + parseInt(b || '0'), 0);
      return total + sum;
    }, 0);
  };

  const getErrorCount = () => {
    return summaries.reduce((total, s) => total + parseInt(s.metrics.ERROR || '0'), 0);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom>
        Log Analytics Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <InfoIcon color="primary" sx={{ mr: 1, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Total Logs
                  </Typography>
                  <Typography variant="h4">{getTotalLogs()}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ErrorIcon color="error" sx={{ mr: 1, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Errors
                  </Typography>
                  <Typography variant="h4">{getErrorCount()}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <WarningIcon color="warning" sx={{ mr: 1, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" variant="body2">
                    Active Services
                  </Typography>
                  <Typography variant="h4">{summaries.length}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Log Metrics by Service
        </Typography>
        {summaries.map((summary) => (
          <Box key={summary.source} sx={{ mb: 2 }}>
            <Typography variant="h6">{summary.source}</Typography>
            <Typography>
              Errors: {summary.metrics.ERROR || 0} | 
              Warnings: {summary.metrics.WARN || 0} | 
              Info: {summary.metrics.INFO || 0}
            </Typography>
          </Box>
        ))}
      </Paper>
    </Container>
  );
};

export default App;
