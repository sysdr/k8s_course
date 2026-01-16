import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Chip,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Sync as SyncIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';
import ApplicationList from './components/ApplicationList';
import DeploymentHistory from './components/DeploymentHistory';
import { fetchApplications, fetchStats, fetchEvents } from './services/api';

function App() {
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [appsData, statsData, eventsData] = await Promise.all([
        fetchApplications(),
        fetchStats(),
        fetchEvents()
      ]);
      
      const applications = Array.isArray(appsData) ? appsData : [];
      setApplications(applications);
      setEvents(Array.isArray(eventsData.events) ? eventsData.events : (Array.isArray(eventsData) ? eventsData : []));
      
      // Calculate stats from applications if event-processor is unavailable
      if (applications.length > 0) {
        const healthyCount = applications.filter(app => app.health_status === 'Healthy').length;
        const syncedCount = applications.filter(app => app.sync_status === 'Synced').length;
        const outOfSyncCount = applications.filter(app => app.sync_status === 'OutOfSync').length;
        
        // Use stats from API if available, otherwise calculate from applications
        const calculatedStats = {
          total_applications: applications.length,
          total_deployments: statsData?.total_deployments || 0,
          successful_deployments: statsData?.successful_deployments || healthyCount,
          failed_deployments: statsData?.failed_deployments || outOfSyncCount,
          healthy_applications: healthyCount,
          synced_applications: syncedCount,
          out_of_sync_applications: outOfSyncCount
        };
        
        setStats(calculatedStats);
      } else {
        // Use API stats or defaults
        setStats(statsData || {
          total_applications: 0,
          total_deployments: 0,
          successful_deployments: 0,
          failed_deployments: 0
        });
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Healthy': return 'success';
      case 'Synced': return 'success';
      case 'Degraded': return 'warning';
      case 'OutOfSync': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Healthy': return <CheckCircle color="success" />;
      case 'Synced': return <CheckCircle color="success" />;
      case 'Degraded': return <Warning color="warning" />;
      case 'OutOfSync': return <Error color="error" />;
      default: return <SyncIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            GitOps Dashboard - ArgoCD Platform
          </Typography>
          <Chip 
            icon={<CheckCircle />}
            label={`${stats?.total_applications || 0} Applications`}
            color="primary"
            variant="outlined"
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Statistics Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Deployments (24h)
                </Typography>
                <Typography variant="h4">
                  {stats?.total_deployments || stats?.total_applications || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'success.light' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Successful
                </Typography>
                <Typography variant="h4">
                  {stats?.successful_deployments || stats?.healthy_applications || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'error.light' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Failed
                </Typography>
                <Typography variant="h4">
                  {stats?.failed_deployments || stats?.out_of_sync_applications || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Applications
                </Typography>
                <Typography variant="h4">
                  {applications.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Application Status */}
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Applications
              </Typography>
              <ApplicationList 
                applications={applications}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            </Paper>
          </Grid>

          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Deployments
              </Typography>
              <DeploymentHistory 
                events={events.slice(0, 10)}
                getStatusColor={getStatusColor}
              />
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
