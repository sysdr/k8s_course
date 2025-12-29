import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import PeopleIcon from '@mui/icons-material/People';
import SpeedIcon from '@mui/icons-material/Speed';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE_URL = '/api';

function App() {
  const [stats, setStats] = useState(null);
  const [queryStats, setQueryStats] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Use Promise.allSettled to handle individual failures gracefully
      const [statsRes, queryStatsRes, usersRes] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/stats/database`, { timeout: 10000 }),
        axios.get(`${API_BASE_URL}/stats/queries`, { timeout: 10000 }),
        axios.get(`${API_BASE_URL}/users?limit=10`, { timeout: 10000 })
      ]);

      // Set data for successful requests, use empty defaults for failed ones
      setStats(statsRes.status === 'fulfilled' ? statsRes.value.data : null);
      setQueryStats(queryStatsRes.status === 'fulfilled' ? queryStatsRes.value.data : []);
      setUsers(usersRes.status === 'fulfilled' ? usersRes.value.data : []);
      setLoading(false);
      
      // Only show error if all requests failed
      if (statsRes.status === 'rejected' && queryStatsRes.status === 'rejected' && usersRes.status === 'rejected') {
        setError('Failed to fetch data from API');
      } else {
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch data from API');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        PostgreSQL Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <StorageIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Database Size
                  </Typography>
                  <Typography variant="h5">
                    {(stats?.database_size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PeopleIcon sx={{ fontSize: 40, mr: 2, color: 'success.main' }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Connections
                  </Typography>
                  <Typography variant="h5">
                    {stats?.active_connections || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <SpeedIcon sx={{ fontSize: 40, mr: 2, color: 'warning.main' }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Cache Hit Ratio
                  </Typography>
                  <Typography variant="h5">
                    {stats?.transactions?.blocks_hit 
                      ? ((stats.transactions.blocks_hit / (stats.transactions.blocks_hit + stats.transactions.blocks_read)) * 100).toFixed(1)
                      : '0'}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Query Performance Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Queries by Total Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={queryStats.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="query_hash" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="mean_time" stroke="#8884d8" name="Mean Time (ms)" />
                <Line type="monotone" dataKey="total_calls" stroke="#82ca9d" name="Total Calls" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Users */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Users
            </Typography>
            <Box>
              {users.map((user) => (
                <Card key={user.id} sx={{ mb: 1 }}>
                  <CardContent>
                    <Typography variant="body1">
                      <strong>{user.username}</strong> - {user.email}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Created: {new Date(user.created_at).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
