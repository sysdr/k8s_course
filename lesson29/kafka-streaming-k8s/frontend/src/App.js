import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Paper, Typography, Box, Card, CardContent,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, AppBar, Toolbar
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';

function App() {
  const [stats, setStats] = useState({});
  const [recentLogs, setRecentLogs] = useState([]);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsResponse = await axios.get(`${API_URL}/stats`);
        setStats(statsResponse.data);
        
        // Fetch logs for first service
        const services = Object.keys(statsResponse.data);
        if (services.length > 0) {
          const logsResponse = await axios.get(`${API_URL}/logs/${services[0]}?limit=20`);
          setRecentLogs(logsResponse.data.logs || []);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Calculate totals
  const totalLogs = Object.values(stats).reduce((acc, service) => {
    return acc + Object.values(service).reduce((sum, level) => sum + (level.count || 0), 0);
  }, 0);

  const errorCount = Object.values(stats).reduce((acc, service) => {
    return acc + ((service.ERROR?.count || 0) + (service.CRITICAL?.count || 0));
  }, 0);

  const getLevelColor = (level) => {
    const colors = {
      'DEBUG': 'default',
      'INFO': 'info',
      'WARNING': 'warning',
      'ERROR': 'error',
      'CRITICAL': 'error'
    };
    return colors[level] || 'default';
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">
            Kafka Log Analytics Dashboard
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Grid container spacing={3}>
          {/* Summary Cards */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Logs Processed
                </Typography>
                <Typography variant="h4">
                  {totalLogs.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Active Services
                </Typography>
                <Typography variant="h4">
                  {Object.keys(stats).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card sx={{ bgcolor: errorCount > 0 ? '#ffebee' : 'inherit' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Errors + Critical
                </Typography>
                <Typography variant="h4" color={errorCount > 0 ? 'error' : 'inherit'}>
                  {errorCount.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Service Statistics */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Service Statistics
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Service</TableCell>
                      <TableCell>DEBUG</TableCell>
                      <TableCell>INFO</TableCell>
                      <TableCell>WARNING</TableCell>
                      <TableCell>ERROR</TableCell>
                      <TableCell>CRITICAL</TableCell>
                      <TableCell>Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(stats).map(([service, levels]) => (
                      <TableRow key={service}>
                        <TableCell>{service}</TableCell>
                        <TableCell>{levels.DEBUG?.count || 0}</TableCell>
                        <TableCell>{levels.INFO?.count || 0}</TableCell>
                        <TableCell>{levels.WARNING?.count || 0}</TableCell>
                        <TableCell>{levels.ERROR?.count || 0}</TableCell>
                        <TableCell>{levels.CRITICAL?.count || 0}</TableCell>
                        <TableCell>
                          <strong>
                            {Object.values(levels).reduce((sum, level) => sum + (level.count || 0), 0)}
                          </strong>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>

          {/* Recent Logs */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Recent Log Events
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Service</TableCell>
                      <TableCell>Level</TableCell>
                      <TableCell>Message</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentLogs.map((log, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          {new Date(log.timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell>{log.service}</TableCell>
                        <TableCell>
                          <Chip 
                            label={log.level} 
                            color={getLevelColor(log.level)} 
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{log.message}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
