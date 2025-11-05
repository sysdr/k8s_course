import React, { useState, useEffect, useRef } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Box,
  Card,
  CardContent,
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';

interface LogStats {
  total: number;
  byLevel: Record<string, number>;
  byService: Record<string, number>;
  timeline: Array<{ timestamp: string; count: number }>;
}

const SERVICES = ['auth-service', 'api-gateway', 'payment-service', 'user-service', 'notification-service'];
const LEVELS = ['INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL'];

function App() {
  const [stats, setStats] = useState<LogStats>({
    total: 0,
    byLevel: {},
    byService: {},
    timeline: []
  });
  
  const baseCountRef = useRef(0);
  const lastUpdateRef = useRef(Date.now());

  useEffect(() => {
    // Initialize with demo data
    const generateInitialData = (): LogStats => {
      baseCountRef.current = 5000 + Math.floor(Math.random() * 10000);
      const byLevel: Record<string, number> = {};
      const byService: Record<string, number> = {};
      
      // Generate realistic distribution
      byLevel['INFO'] = Math.floor(baseCountRef.current * 0.65);
      byLevel['WARNING'] = Math.floor(baseCountRef.current * 0.20);
      byLevel['ERROR'] = Math.floor(baseCountRef.current * 0.10);
      byLevel['DEBUG'] = Math.floor(baseCountRef.current * 0.04);
      byLevel['CRITICAL'] = Math.floor(baseCountRef.current * 0.01);
      
      SERVICES.forEach(service => {
        byService[service] = Math.floor(baseCountRef.current / SERVICES.length * (0.8 + Math.random() * 0.4));
      });
      
      // Generate timeline for last 24 hours
      const timeline = [];
      const now = new Date();
      for (let i = 23; i >= 0; i--) {
        const hour = new Date(now);
        hour.setHours(hour.getHours() - i);
        const hourStr = hour.getHours().toString().padStart(2, '0') + ':00';
        const baseCount = 200 + Math.floor(Math.random() * 800);
        // Add some variation based on hour (more during business hours)
        const multiplier = (hour.getHours() >= 9 && hour.getHours() <= 17) ? 1.5 : 0.8;
        timeline.push({
          timestamp: hourStr,
          count: Math.floor(baseCount * multiplier)
        });
      }
      
      return {
        total: baseCountRef.current,
        byLevel,
        byService,
        timeline
      };
    };

    setStats(generateInitialData());

    // Update data every 2 seconds for real-time effect
    const interval = setInterval(() => {
      setStats(prevStats => {
        const now = Date.now();
        const timeDiff = (now - lastUpdateRef.current) / 1000; // seconds
        lastUpdateRef.current = now;
        
        // Increment base count (simulate new logs coming in)
        const increment = Math.floor(timeDiff * (50 + Math.random() * 100));
        baseCountRef.current += increment;
        
        // Update by level with realistic distribution
        const newByLevel = { ...prevStats.byLevel };
        newByLevel['INFO'] = (newByLevel['INFO'] || 0) + Math.floor(increment * 0.65);
        newByLevel['WARNING'] = (newByLevel['WARNING'] || 0) + Math.floor(increment * 0.20);
        newByLevel['ERROR'] = (newByLevel['ERROR'] || 0) + Math.floor(increment * 0.10);
        newByLevel['DEBUG'] = (newByLevel['DEBUG'] || 0) + Math.floor(increment * 0.04);
        newByLevel['CRITICAL'] = (newByLevel['CRITICAL'] || 0) + Math.floor(increment * 0.01);
        
        // Update by service
        const newByService = { ...prevStats.byService };
        SERVICES.forEach(service => {
          newByService[service] = (newByService[service] || 0) + Math.floor(increment / SERVICES.length * (0.8 + Math.random() * 0.4));
        });
        
        // Update timeline - add new data point and shift old ones
        const newTimeline = [...prevStats.timeline];
        const currentHour = new Date().getHours();
        const currentMinute = new Date().getMinutes();
        const currentTimeStr = currentHour.toString().padStart(2, '0') + ':00';
        
        // Update current hour's count
        if (newTimeline.length > 0) {
          const lastIndex = newTimeline.length - 1;
          if (newTimeline[lastIndex].timestamp === currentTimeStr) {
            // Same hour, increment count
            newTimeline[lastIndex].count += Math.floor(increment / 12); // Distribute over 5-second intervals
          } else {
            // New hour, add new point
            newTimeline.push({
              timestamp: currentTimeStr,
              count: Math.floor(200 + Math.random() * 800)
            });
            // Keep only last 24 hours
            if (newTimeline.length > 24) {
              newTimeline.shift();
            }
          }
        }
        
        // Calculate total from byLevel
        const total = Object.values(newByLevel).reduce((sum, count) => sum + count, 0);
        
        return {
          total,
          byLevel: newByLevel,
          byService: newByService,
          timeline: newTimeline
        };
      });
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const levelData = Object.entries(stats.byLevel)
    .filter(([_, count]) => count > 0)
    .map(([level, count]) => ({
      level,
      count
    }))
    .sort((a, b) => {
      const order = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'];
      return order.indexOf(a.level) - order.indexOf(b.level);
    });

  const serviceData = Object.entries(stats.byService)
    .filter(([_, count]) => count > 0)
    .map(([service, count]) => ({
      service,
      count
    }))
    .sort((a, b) => b.count - a.count);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Log Analytics Dashboard
          </Typography>
          <Typography variant="body2">
            Real-time Monitoring
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Summary Cards */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Logs
                </Typography>
                <Typography variant="h4">
                  {stats.total.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ bgcolor: '#ffebee' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
                  <Typography color="textSecondary" gutterBottom>
                    Errors
                  </Typography>
                </Box>
                <Typography variant="h4" color="error.main">
                  {(stats.byLevel.ERROR || 0).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ bgcolor: '#fff3e0' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography color="textSecondary" gutterBottom>
                    Warnings
                  </Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {(stats.byLevel.WARNING || 0).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card sx={{ bgcolor: '#e3f2fd' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <InfoIcon sx={{ mr: 1, color: 'info.main' }} />
                  <Typography color="textSecondary" gutterBottom>
                    Info
                  </Typography>
                </Box>
                <Typography variant="h4" color="info.main">
                  {(stats.byLevel.INFO || 0).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Timeline Chart */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Log Volume (Last 24 Hours)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Level Distribution */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Logs by Level
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={levelData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="level" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Service Distribution */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Logs by Service
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={serviceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="service" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
