import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert
} from '@mui/material';
import {
  Security,
  CheckCircle,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  const [namespaceStats, setNamespaceStats] = useState([]);
  const [violations, setViolations] = useState([]);
  const [policyData, setPolicyData] = useState([]);

  useEffect(() => {
    // Mock data - in production, fetch from Kubernetes API
    setNamespaceStats([
      { name: 'logs-public', policy: 'baseline', pods: 12, violations: 0, status: 'compliant' },
      { name: 'logs-payment', policy: 'restricted', pods: 8, violations: 0, status: 'compliant' },
      { name: 'logs-system', policy: 'privileged', pods: 3, violations: 0, status: 'compliant' }
    ]);

    setViolations([
      {
        namespace: 'logs-public',
        pod: 'log-ingestion-abc123',
        violation: 'Missing seccomp profile',
        severity: 'medium',
        timestamp: new Date().toISOString()
      }
    ]);

    setPolicyData([
      { policy: 'Privileged', count: 3 },
      { policy: 'Baseline', count: 12 },
      { policy: 'Restricted', count: 8 }
    ]);
  }, []);

  const getPolicyColor = (policy) => {
    switch (policy) {
      case 'privileged': return 'error';
      case 'baseline': return 'warning';
      case 'restricted': return 'success';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'compliant': return <CheckCircle color="success" />;
      case 'warning': return <Warning color="warning" />;
      case 'violation': return <ErrorIcon color="error" />;
      default: return null;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          <Security sx={{ fontSize: 40, mr: 2, verticalAlign: 'middle' }} />
          Pod Security Standards Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Real-time monitoring of Kubernetes Pod Security Standards enforcement
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Namespaces
              </Typography>
              <Typography variant="h3">
                {namespaceStats.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Pods
              </Typography>
              <Typography variant="h3">
                {namespaceStats.reduce((sum, ns) => sum + ns.pods, 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Violations
              </Typography>
              <Typography variant="h3" color="error">
                {violations.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Policy Distribution Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pod Security Policy Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={policyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="policy" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Namespace Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Namespace Security Status
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Namespace</TableCell>
                    <TableCell>Policy</TableCell>
                    <TableCell align="right">Pods</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {namespaceStats.map((ns) => (
                    <TableRow key={ns.name}>
                      <TableCell>{ns.name}</TableCell>
                      <TableCell>
                        <Chip 
                          label={ns.policy} 
                          color={getPolicyColor(ns.policy)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">{ns.pods}</TableCell>
                      <TableCell>{getStatusIcon(ns.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Recent Violations */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Security Violations
            </Typography>
            {violations.length === 0 ? (
              <Alert severity="success">No security violations detected</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Namespace</TableCell>
                      <TableCell>Pod</TableCell>
                      <TableCell>Violation</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {violations.map((violation, index) => (
                      <TableRow key={index}>
                        <TableCell>{violation.namespace}</TableCell>
                        <TableCell>{violation.pod}</TableCell>
                        <TableCell>{violation.violation}</TableCell>
                        <TableCell>
                          <Chip 
                            label={violation.severity} 
                            color={violation.severity === 'high' ? 'error' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{new Date(violation.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Security Best Practices */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pod Security Standards Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Typography variant="subtitle1" color="error" gutterBottom>
                    <strong>Privileged</strong>
                  </Typography>
                  <Typography variant="body2">
                    • Unrestricted policy (unsafe)<br />
                    • Allows privilege escalation<br />
                    • Host access permitted<br />
                    • Use only for system workloads
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Typography variant="subtitle1" color="warning" gutterBottom>
                    <strong>Baseline</strong>
                  </Typography>
                  <Typography variant="body2">
                    • Minimally restrictive<br />
                    • Prevents known escalations<br />
                    • Compatible with most apps<br />
                    • Default for applications
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                  <Typography variant="subtitle1" color="success" gutterBottom>
                    <strong>Restricted</strong>
                  </Typography>
                  <Typography variant="body2">
                    • Heavily restricted<br />
                    • Non-root required<br />
                    • Read-only root filesystem<br />
                    • Maximum security posture
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
