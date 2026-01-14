import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Refresh,
  Storage,
  DataObject
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/health/all`);
      setHealthData(response.data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch health data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(fetchHealthData, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch(status) {
      case 'healthy':
        return <CheckCircle style={{ color: '#4caf50' }} />;
      case 'unhealthy':
        return <Error style={{ color: '#f44336' }} />;
      case 'degraded':
        return <Warning style={{ color: '#ff9800' }} />;
      default:
        return <Warning style={{ color: '#9e9e9e' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'healthy':
        return 'success';
      case 'unhealthy':
        return 'error';
      case 'degraded':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading && !healthData) {
    return (
      <Container maxWidth="lg" style={{ marginTop: '50px', textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="h6" style={{ marginTop: '20px' }}>
          Loading health data...
        </Typography>
      </Container>
    );
  }

  if (error && !healthData) {
    return (
      <Container maxWidth="lg" style={{ marginTop: '50px' }}>
        <Alert severity="error">
          Failed to connect to backend: {error}
        </Alert>
        <Button 
          variant="contained" 
          onClick={fetchHealthData}
          style={{ marginTop: '20px' }}
        >
          Retry
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" style={{ marginTop: '30px', marginBottom: '30px' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h3" component="h1">
          <Storage style={{ fontSize: '40px', verticalAlign: 'middle', marginRight: '10px' }} />
          Stateful Application Debugger
        </Typography>
        <Button 
          variant="outlined" 
          startIcon={<Refresh />}
          onClick={fetchHealthData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Alert severity="info" style={{ marginBottom: '20px' }}>
        <strong>Break-It-Friday Challenge:</strong> Fix all broken scenarios to turn all services green!
        Last updated: {lastUpdate?.toLocaleTimeString()}
      </Alert>

      {healthData && (
        <>
          <Card style={{ marginBottom: '30px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h5" style={{ color: 'white' }}>
                  Overall System Status
                </Typography>
                <Box display="flex" alignItems="center">
                  {getStatusIcon(healthData.overall_status)}
                  <Chip 
                    label={healthData.overall_status.toUpperCase()}
                    color={getStatusColor(healthData.overall_status)}
                    style={{ marginLeft: '10px', fontWeight: 'bold' }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Grid container spacing={3}>
            {Object.entries(healthData.services).map(([serviceName, serviceData]) => (
              <Grid item xs={12} md={6} key={serviceName}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                      <Typography variant="h6">
                        <DataObject style={{ verticalAlign: 'middle', marginRight: '5px' }} />
                        {serviceName.charAt(0).toUpperCase() + serviceName.slice(1)}
                      </Typography>
                      <Chip 
                        label={serviceData.status}
                        color={getStatusColor(serviceData.status)}
                        icon={getStatusIcon(serviceData.status)}
                      />
                    </Box>

                    <Divider style={{ margin: '15px 0' }} />

                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Latency" 
                          secondary={`${serviceData.latency_ms} ms`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Last Check" 
                          secondary={new Date(serviceData.timestamp).toLocaleTimeString()}
                        />
                      </ListItem>
                    </List>

                    {serviceData.details && (
                      <>
                        <Divider style={{ margin: '15px 0' }} />
                        <Typography variant="subtitle2" gutterBottom>
                          Details:
                        </Typography>
                        <List dense>
                          {Object.entries(serviceData.details).map(([key, value]) => (
                            <ListItem key={key}>
                              <ListItemText 
                                primary={key.replace(/_/g, ' ').toUpperCase()} 
                                secondary={typeof value === 'object' ? JSON.stringify(value) : value}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}

                    {serviceData.error && (
                      <Alert severity="error" style={{ marginTop: '10px' }}>
                        {serviceData.error}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Card style={{ marginTop: '30px' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Debugging Scenarios Status
              </Typography>
              <List>
                {[
                  { id: 1, name: 'PVC Pending - StorageClass Mismatch', difficulty: 'Easy' },
                  { id: 2, name: 'Resource Quota Exhaustion', difficulty: 'Easy' },
                  { id: 3, name: 'PostgreSQL CrashLoop', difficulty: 'Medium' },
                  { id: 4, name: 'Volume Permission Errors', difficulty: 'Medium' },
                  { id: 5, name: 'Redis Anti-Affinity Issues', difficulty: 'Medium' },
                  { id: 6, name: 'Storage Provisioning Timeout', difficulty: 'Hard' }
                ].map((scenario) => (
                  <ListItem key={scenario.id}>
                    <ListItemText
                      primary={`Scenario ${scenario.id}: ${scenario.name}`}
                      secondary={`Difficulty: ${scenario.difficulty}`}
                    />
                    <Chip 
                      label="Check Manually" 
                      variant="outlined"
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </>
      )}
    </Container>
  );
}

export default App;
