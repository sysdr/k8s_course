import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
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
  ResponsiveContainer
} from 'recharts';

// Colors: Green, Orange, Red, Yellow, Teal, Gray (NO PURPLE OR BLUE)
const COLORS = ['#00C49F', '#FF8042', '#FF6B6B', '#FFD93D', '#20B2AA', '#95A5A6'];
const VERSION_COLORS = {
  v1: '#00C49F', // Green
  v2: '#FF8042', // Orange
  v3: '#FF6B6B'  // Red
};

function Dashboard() {
  const [metrics, setMetrics] = useState({
    v1: { requests: 750, latency: 35.5, errors: 1, success: 749 },
    v2: { requests: 280, latency: 28.2, errors: 0, success: 280 },
    v3: { requests: 120, latency: 22.8, errors: 0, success: 120 }
  });
  
  const [latencyHistory, setLatencyHistory] = useState([
    { time: '09:00', v1: 35.5, v2: 28.2, v3: 22.8 },
    { time: '09:01', v1: 36.2, v2: 27.8, v3: 23.1 },
    { time: '09:02', v1: 34.9, v2: 28.5, v3: 22.5 },
    { time: '09:03', v1: 35.8, v2: 27.9, v3: 22.9 },
    { time: '09:04', v1: 35.2, v2: 28.1, v3: 22.7 }
  ]);

  const [requestHistory, setRequestHistory] = useState([
    { time: '09:00', v1: 750, v2: 280, v3: 120 },
    { time: '09:01', v1: 720, v2: 290, v3: 130 },
    { time: '09:02', v1: 780, v2: 275, v3: 115 },
    { time: '09:03', v1: 760, v2: 285, v3: 125 },
    { time: '09:04', v1: 740, v2: 280, v3: 120 }
  ]);

  const [trafficDistribution, setTrafficDistribution] = useState([
    { name: 'Version 1', value: 750, color: VERSION_COLORS.v1 },
    { name: 'Version 2', value: 280, color: VERSION_COLORS.v2 },
    { name: 'Version 3', value: 120, color: VERSION_COLORS.v3 }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      const newMetrics = {
        v1: {
          requests: Math.floor(Math.random() * 200) + 600,
          latency: Math.random() * 10 + 30,
          errors: Math.floor(Math.random() * 3),
          success: 0
        },
        v2: {
          requests: Math.floor(Math.random() * 150) + 200,
          latency: Math.random() * 8 + 25,
          errors: Math.floor(Math.random() * 2),
          success: 0
        },
        v3: {
          requests: Math.floor(Math.random() * 100) + 80,
          latency: Math.random() * 6 + 20,
          errors: Math.floor(Math.random() * 1),
          success: 0
        }
      };
      
      newMetrics.v1.success = newMetrics.v1.requests - newMetrics.v1.errors;
      newMetrics.v2.success = newMetrics.v2.requests - newMetrics.v2.errors;
      newMetrics.v3.success = newMetrics.v3.requests - newMetrics.v3.errors;
      
      setMetrics(newMetrics);
      
      const now = new Date();
      const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      setLatencyHistory(prev => {
        const updated = [
          ...prev,
          { time: timeStr, v1: newMetrics.v1.latency, v2: newMetrics.v2.latency, v3: newMetrics.v3.latency }
        ];
        return updated.slice(-10);
      });

      setRequestHistory(prev => {
        const updated = [
          ...prev,
          { time: timeStr, v1: newMetrics.v1.requests, v2: newMetrics.v2.requests, v3: newMetrics.v3.requests }
        ];
        return updated.slice(-10);
      });

      setTrafficDistribution([
        { name: 'Version 1', value: newMetrics.v1.requests, color: VERSION_COLORS.v1 },
        { name: 'Version 2', value: newMetrics.v2.requests, color: VERSION_COLORS.v2 },
        { name: 'Version 3', value: newMetrics.v3.requests, color: VERSION_COLORS.v3 }
      ]);
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const totalRequests = metrics.v1.requests + metrics.v2.requests + metrics.v3.requests;
  const totalErrors = metrics.v1.errors + metrics.v2.errors + metrics.v3.errors;
  const avgLatency = ((metrics.v1.latency * metrics.v1.requests + 
                       metrics.v2.latency * metrics.v2.requests + 
                       metrics.v3.latency * metrics.v3.requests) / totalRequests).toFixed(2);
  const successRate = (((totalRequests - totalErrors) / totalRequests) * 100).toFixed(2);

  return (
    <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
        Istio Traffic Management - Project Outcomes Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 1 }}>
        {/* Overall Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#E8F5E9', borderLeft: '4px solid #00C49F' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Total Requests</Typography>
              <Typography variant="h4" sx={{ color: '#2E7D32', fontWeight: 'bold' }}>
                {totalRequests}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#FFF3E0', borderLeft: '4px solid #FF8042' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Average Latency</Typography>
              <Typography variant="h4" sx={{ color: '#E65100', fontWeight: 'bold' }}>
                {avgLatency}ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#FFEBEE', borderLeft: '4px solid #FF6B6B' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Total Errors</Typography>
              <Typography variant="h4" sx={{ color: '#C62828', fontWeight: 'bold' }}>
                {totalErrors}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#F1F8E9', borderLeft: '4px solid #FFD93D' }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Success Rate</Typography>
              <Typography variant="h4" sx={{ color: '#558B2F', fontWeight: 'bold' }}>
                {successRate}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Version Details Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
              Service Version Metrics
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: '#F5F5F5' }}>
                    <TableCell><strong>Version</strong></TableCell>
                    <TableCell align="right"><strong>Requests/min</strong></TableCell>
                    <TableCell align="right"><strong>Avg Latency (ms)</strong></TableCell>
                    <TableCell align="right"><strong>Errors</strong></TableCell>
                    <TableCell align="right"><strong>Success</strong></TableCell>
                    <TableCell align="right"><strong>Success Rate</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><strong style={{ color: VERSION_COLORS.v1 }}>v1 (Stable)</strong></TableCell>
                    <TableCell align="right">{metrics.v1.requests}</TableCell>
                    <TableCell align="right">{metrics.v1.latency.toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ color: '#C62828' }}>{metrics.v1.errors}</TableCell>
                    <TableCell align="right" sx={{ color: '#2E7D32' }}>{metrics.v1.success}</TableCell>
                    <TableCell align="right">{((metrics.v1.success / metrics.v1.requests) * 100).toFixed(2)}%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong style={{ color: VERSION_COLORS.v2 }}>v2 (Canary)</strong></TableCell>
                    <TableCell align="right">{metrics.v2.requests}</TableCell>
                    <TableCell align="right">{metrics.v2.latency.toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ color: '#C62828' }}>{metrics.v2.errors}</TableCell>
                    <TableCell align="right" sx={{ color: '#2E7D32' }}>{metrics.v2.success}</TableCell>
                    <TableCell align="right">{((metrics.v2.success / metrics.v2.requests) * 100).toFixed(2)}%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong style={{ color: VERSION_COLORS.v3 }}>v3 (Experimental)</strong></TableCell>
                    <TableCell align="right">{metrics.v3.requests}</TableCell>
                    <TableCell align="right">{metrics.v3.latency.toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ color: '#C62828' }}>{metrics.v3.errors}</TableCell>
                    <TableCell align="right" sx={{ color: '#2E7D32' }}>{metrics.v3.success}</TableCell>
                    <TableCell align="right">{((metrics.v3.success / metrics.v3.requests) * 100).toFixed(2)}%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Latency Comparison Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
              Latency Comparison Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={latencyHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
                <XAxis dataKey="time" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="v1" stroke={VERSION_COLORS.v1} strokeWidth={2} name="v1 (Stable)" />
                <Line type="monotone" dataKey="v2" stroke={VERSION_COLORS.v2} strokeWidth={2} name="v2 (Canary)" />
                <Line type="monotone" dataKey="v3" stroke={VERSION_COLORS.v3} strokeWidth={2} name="v3 (Experimental)" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Request Volume Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
              Request Volume Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={requestHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
                <XAxis dataKey="time" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip />
                <Legend />
                <Bar dataKey="v1" fill={VERSION_COLORS.v1} name="v1 (Stable)" />
                <Bar dataKey="v2" fill={VERSION_COLORS.v2} name="v2 (Canary)" />
                <Bar dataKey="v3" fill={VERSION_COLORS.v3} name="v3 (Experimental)" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Traffic Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
              Traffic Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trafficDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {trafficDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Performance Comparison Bar Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2C3E50' }}>
              Performance Comparison
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { name: 'v1', Latency: metrics.v1.latency, Requests: metrics.v1.requests / 10 },
                { name: 'v2', Latency: metrics.v2.latency, Requests: metrics.v2.requests / 10 },
                { name: 'v3', Latency: metrics.v3.latency, Requests: metrics.v3.requests / 10 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
                <XAxis dataKey="name" stroke="#666" />
                <YAxis yAxisId="left" stroke="#666" />
                <YAxis yAxisId="right" orientation="right" stroke="#666" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="Latency" fill="#FF8042" name="Latency (ms)" />
                <Bar yAxisId="right" dataKey="Requests" fill="#20B2AA" name="Requests (x10)" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;

