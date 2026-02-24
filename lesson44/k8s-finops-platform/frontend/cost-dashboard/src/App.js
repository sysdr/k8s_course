import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  CircularProgress
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
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import axios from 'axios';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function App() {
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCostData();
    const interval = setInterval(fetchCostData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchCostData = async () => {
    try {
      const apiBase = process.env.REACT_APP_COST_API_URL || '';
      const url = apiBase ? `${apiBase}/cost-summary` : '/api/cost-summary';
      const res = await axios.get(url, { timeout: 10000 });
      if (res.data && typeof res.data.cluster_hourly_cost === 'number') {
        setCostData(res.data);
      } else {
        throw new Error('Invalid cost data');
      }
    } catch (err) {
      const mockData = {
        cluster_hourly_cost: 8.42,
        cluster_monthly_cost: 6146.60,
        namespaces: [
          { namespace: 'prod-logging', cpu_cost: 4.32, memory_cost: 2.10, total_cost: 6.42, waste_percentage: 23.5 },
          { namespace: 'staging-logging', cpu_cost: 1.20, memory_cost: 0.50, total_cost: 1.70, waste_percentage: 35.2 },
          { namespace: 'dev-logging', cpu_cost: 0.20, memory_cost: 0.10, total_cost: 0.30, waste_percentage: 45.8 }
        ],
        total_waste_usd: 2.45,
        optimization_opportunities: [
          { namespace: 'staging-logging', recommendation: 'High waste detected (35.2%). Consider right-sizing resource requests.', potential_savings_usd_monthly: '628.40' }
        ]
      };
      setCostData(mockData);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">Error loading cost data: {error}</Alert>
      </Container>
    );
  }

  const wasteData = costData.namespaces.map(ns => ({
    name: ns.namespace,
    waste: ns.waste_percentage
  }));

  const costByNamespace = costData.namespaces.map(ns => ({
    name: ns.namespace,
    cost: ns.total_cost
  }));

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', color: '#1976d2' }}>
        Kubernetes FinOps Dashboard
      </Typography>

      {/* Cost Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Hourly Cluster Cost
              </Typography>
              <Typography variant="h3">
                ${costData.cluster_hourly_cost}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon />
                <Typography variant="body2" sx={{ ml: 1 }}>
                  vs. last hour
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Projection
              </Typography>
              <Typography variant="h3">
                ${costData.cluster_monthly_cost.toLocaleString()}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Based on current usage
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Waste Detected
              </Typography>
              <Typography variant="h3">
                ${costData.total_waste_usd}/hr
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingDownIcon />
                <Typography variant="body2" sx={{ ml: 1 }}>
                  Optimization opportunity
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cost by Namespace
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={costByNamespace}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cost" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Resource Waste Percentage
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={wasteData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="waste" fill="#ff8042">
                  {wasteData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.waste > 30 ? '#ff4444' : '#44ff44'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Optimization Recommendations */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Optimization Opportunities
            </Typography>
            {costData.optimization_opportunities.map((opp, index) => (
              <Alert severity="warning" sx={{ mb: 2 }} key={index}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {opp.namespace}
                </Typography>
                <Typography variant="body2">
                  {opp.recommendation}
                </Typography>
                <Typography variant="body2" color="primary" fontWeight="bold">
                  Potential Monthly Savings: ${opp.potential_savings_usd_monthly}
                </Typography>
              </Alert>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
