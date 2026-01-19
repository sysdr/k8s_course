import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  Alert
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import axios from 'axios';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import PaymentIcon from '@mui/icons-material/Payment';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

function App() {
  const [orders, setOrders] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [stats, setStats] = useState({
    totalOrders: 0,
    successRate: 0,
    avgOrderValue: 0,
    activeVersion: 'v1'
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API_URL}/orders?limit=50`);
      setOrders(response.data);
      calculateStats(response.data);
      updateMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    }
  };

  const calculateStats = (orderData) => {
    const total = orderData.length;
    const successful = orderData.filter(o => o.status === 'completed').length;
    const avgValue = orderData.reduce((sum, o) => sum + o.total, 0) / total || 0;
    const versions = orderData.map(o => o.version);
    const activeVersion = versions[versions.length - 1] || 'v1';

    setStats({
      totalOrders: total,
      successRate: (successful / total * 100).toFixed(1),
      avgOrderValue: avgValue.toFixed(2),
      activeVersion
    });
  };

  const updateMetrics = (orderData) => {
    const versionMetrics = {};
    
    orderData.forEach(order => {
      const version = order.version;
      if (!versionMetrics[version]) {
        versionMetrics[version] = { orders: 0, revenue: 0 };
      }
      versionMetrics[version].orders += 1;
      versionMetrics[version].revenue += order.total;
    });

    const metricsData = Object.entries(versionMetrics).map(([version, data]) => ({
      version,
      orders: data.orders,
      revenue: data.revenue.toFixed(2)
    }));

    setMetrics(metricsData);
  };

  const createTestOrder = async () => {
    setLoading(true);
    try {
      const testOrder = {
        customer_id: `CUST-${Math.floor(Math.random() * 10000)}`,
        items: [
          {
            product_id: `PROD-${Math.floor(Math.random() * 100)}`,
            quantity: Math.floor(Math.random() * 5) + 1,
            price: parseFloat((Math.random() * 100 + 10).toFixed(2))
          }
        ]
      };

      await axios.post(`${API_URL}/orders`, testOrder);
      await fetchOrders();
    } catch (error) {
      console.error('Failed to create order:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom sx={{ mb: 4 }}>
        Progressive Delivery Dashboard
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Real-time monitoring of order processing across deployment versions. 
        Watch traffic distribution during canary and blue-green deployments.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShoppingCartIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Orders</Typography>
              </Box>
              <Typography variant="h4">{stats.totalOrders}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Success Rate</Typography>
              </Box>
              <Typography variant="h4">{stats.successRate}%</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PaymentIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Avg Order Value</Typography>
              </Box>
              <Typography variant="h4">${stats.avgOrderValue}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Active Version</Typography>
              <Chip 
                label={stats.activeVersion} 
                color="primary" 
                size="large"
                sx={{ fontSize: '1.2rem', p: 2 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Version Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="version" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="orders" stroke="#8884d8" fill="#8884d8" />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Revenue by Version
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="version" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="revenue" stroke="#82ca9d" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Recent Orders</Typography>
          <Button 
            variant="contained" 
            onClick={createTestOrder}
            disabled={loading}
          >
            Create Test Order
          </Button>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Order ID</TableCell>
                <TableCell>Customer</TableCell>
                <TableCell align="right">Total</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Timestamp</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.slice(0, 20).map((order) => (
                <TableRow key={order.order_id}>
                  <TableCell>{order.order_id}</TableCell>
                  <TableCell>{order.customer_id}</TableCell>
                  <TableCell align="right">${order.total.toFixed(2)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={order.status} 
                      color={order.status === 'completed' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={order.version} size="small" />
                  </TableCell>
                  <TableCell>{new Date(order.timestamp).toLocaleString()}</TableCell>
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
