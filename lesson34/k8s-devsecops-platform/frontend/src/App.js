import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  LinearProgress
} from '@mui/material';
import {
  Security as SecurityIcon,
  Speed as SpeedIcon,
  BugReport as BugReportIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Block as BlockIcon,
  NetworkCheck as NetworkIcon,
  VpnKey as KeyIcon,
  Assignment as AuditIcon,
  Shield as ShieldIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [securityData, setSecurityData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (token) {
      fetchSecurityData();
      fetchAnalytics();
      // Refresh data every 30 seconds
      const interval = setInterval(() => {
        fetchSecurityData();
        fetchAnalytics();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSecurityData = async () => {
    try {
      setLoadingData(true);
      const response = await axios.get(`${API_URL}/security/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setSecurityData(response.data);
    } catch (err) {
      console.error('Failed to fetch security data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_URL}/analytics/summary`, {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: {
          time_range: '1h'
        }
      });
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setSecurityData(null);
    setAnalytics(null);
  };

  if (!token) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <SecurityIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
            <Typography variant="h4">Secure Login</Typography>
          </Box>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            autoComplete="username"
          />
          
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            autoComplete="current-password"
          />
          
          <Button
            fullWidth
            variant="contained"
            onClick={handleLogin}
            disabled={loading}
            sx={{ mt: 3 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            Demo credentials: admin/admin123 or user/user123
          </Alert>
        </Paper>
      </Container>
    );
  }

  const vuln = securityData?.vulnerabilities;
  const policies = securityData?.policy_violations;
  const threats = securityData?.runtime_threats;
  const network = securityData?.network_security;
  const secrets = securityData?.secrets;
  const audit = securityData?.audit;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3">DevSecOps Security Dashboard</Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time security monitoring and compliance
          </Typography>
        </Box>
        <Button variant="outlined" onClick={handleLogout}>Logout</Button>
      </Box>

      {loadingData && <LinearProgress sx={{ mb: 2 }} />}

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)',
            color: 'white',
            border: '2px solid #ff6b35'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ErrorIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Critical CVEs</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                {vuln?.critical_count || 0}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                {vuln?.blocked_deployments || 0} deployments blocked
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)',
            color: 'white',
            border: '2px solid #ff9800'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WarningIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>High CVEs</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                {vuln?.high_count || 0}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                {vuln?.total_scanned || 0} images scanned
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
            color: 'white',
            border: '2px solid #1976d2'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BlockIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Policy Violations</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                {policies?.total_violations || 0}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                {policies?.blocked_deployments || 0} blocked
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: threats?.critical_alerts > 0 
              ? 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)'
              : 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
            color: 'white',
            border: threats?.critical_alerts > 0 ? '2px solid #ff6b35' : '2px solid #2e7d32'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShieldIcon sx={{ mr: 1, color: 'white' }} />
                <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Runtime Threats</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>
                {threats?.critical_alerts || 0}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                {threats?.warning_alerts || 0} warnings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for detailed sections */}
      <Paper sx={{ mb: 3, background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)' }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, v) => setActiveTab(v)}
          sx={{
            '& .MuiTab-root': {
              color: '#1976d2',
              fontWeight: 'bold',
              '&.Mui-selected': {
                color: '#0d47a1',
                background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
                color: 'white',
                borderRadius: '8px 8px 0 0'
              }
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#1976d2',
              height: 3
            }
          }}
        >
          <Tab label="Vulnerabilities" sx={{ color: '#ff9800' }} />
          <Tab label="Policy Violations" sx={{ color: '#2196f3' }} />
          <Tab label="Runtime Threats" sx={{ color: '#4caf50' }} />
          <Tab label="Network Security" sx={{ color: '#00bcd4' }} />
          <Tab label="Secrets" sx={{ color: '#ffc107' }} />
          <Tab label="Audit Logs" sx={{ color: '#009688' }} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)', border: '2px solid #ff9800' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#e65100', fontWeight: 'bold' }}>
            <BugReportIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#ff6b35' }} />
            Vulnerability Scanning Results (Trivy)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Automated vulnerability scanning blocking deployments - Shift-left security in action
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Critical</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{vuln?.critical_count || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)', color: 'white', border: '2px solid #ff9800' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>High</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{vuln?.high_count || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)', color: 'white', border: '2px solid #0097a7' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Medium</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{vuln?.medium_count || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Blocked Deployments</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{vuln?.blocked_deployments || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Total Scanned:</strong> {vuln?.total_scanned || 0} container images
            <br />
            <strong>Failed Builds:</strong> {vuln?.blocked_deployments || 0} deployments blocked due to vulnerabilities
          </Alert>
        </Paper>
      )}

      {activeTab === 1 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)', border: '2px solid #2196f3' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#1565c0', fontWeight: 'bold' }}>
            <BlockIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#2196f3' }} />
            Policy Violations & Enforcement (Kyverno)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Runtime policy enforcement with audit + enforce modes
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)', color: 'white', border: '2px solid #1976d2' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Total Violations</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{policies?.total_violations || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Blocked Deployments</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{policies?.blocked_deployments || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)', color: 'white', border: '2px solid #0097a7' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Enforce Mode</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{policies?.enforce_mode_count || 0}</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>Audit: {policies?.audit_mode_count || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {policies?.top_policies && policies.top_policies.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Most Violated Policies</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Policy</TableCell>
                      <TableCell align="right">Violations</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {policies.top_policies.map((policy, idx) => (
                      <TableRow key={idx}>
                        <TableCell><code>{policy.policy}</code></TableCell>
                        <TableCell align="right">{policy.count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Paper>
      )}

      {activeTab === 2 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)', border: '2px solid #4caf50' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#2e7d32', fontWeight: 'bold' }}>
            <ShieldIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#4caf50' }} />
            Runtime Threat Detection (Falco / eBPF)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Detect shell execution, privilege escalation, suspicious behavior
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Critical Alerts</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{threats?.critical_alerts || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)', color: 'white', border: '2px solid #ff9800' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Warning Alerts</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{threats?.warning_alerts || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)', color: 'white', border: '2px solid #2e7d32' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Affected Pods</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{threats?.affected_pods || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {threats?.recent_threats && threats.recent_threats.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Recent Threats</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Alert</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Pod</TableCell>
                      <TableCell>Process</TableCell>
                      <TableCell>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {threats.recent_threats.map((threat, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{threat.alert}</TableCell>
                        <TableCell>
                          <Chip 
                            label={threat.severity} 
                            sx={{
                              backgroundColor: threat.severity === 'CRITICAL' ? '#ff9800' : '#ffc107',
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{threat.pod}</TableCell>
                        <TableCell><code>{threat.process}</code></TableCell>
                        <TableCell>{new Date(threat.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Paper>
      )}

      {activeTab === 3 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%)', border: '2px solid #00bcd4' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#00838f', fontWeight: 'bold' }}>
            <NetworkIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#00bcd4' }} />
            Network Security / Zero Trust Visibility
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Calico NetworkPolicies + mTLS zero trust
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)', color: 'white', border: '2px solid #2e7d32' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Allowed Connections</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{network?.allowed_connections || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Blocked Connections</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{network?.blocked_connections || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)', color: 'white', border: '2px solid #0097a7' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Encrypted Traffic</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{network?.encrypted_traffic_percent || 0}%</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>mTLS enabled</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Policy Hits:</strong> {network?.policy_hits || 0} network policy evaluations
          </Alert>
        </Paper>
      )}

      {activeTab === 4 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #fff9c4 0%, #fff59d 100%)', border: '2px solid #ffc107' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#f57f17', fontWeight: 'bold' }}>
            <KeyIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#ffc107' }} />
            Secrets & Vault Activity
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Secrets management with Vault and rotation
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ffc107 0%, #ffb300 100%)', color: 'white', border: '2px solid #ffb300' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Total Access</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{secrets?.total_access || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Failed Attempts</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{secrets?.failed_attempts || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)', color: 'white', border: '2px solid #0097a7' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Last Rotation</Typography>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                    {secrets?.last_rotation 
                      ? new Date(secrets.last_rotation).toLocaleString()
                      : 'Never'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {secrets?.recent_access && secrets.recent_access.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Recent Secret Access</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Secret</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {secrets.recent_access.map((access, idx) => (
                      <TableRow key={idx}>
                        <TableCell><code>{access.secret}</code></TableCell>
                        <TableCell>{access.action}</TableCell>
                        <TableCell>{access.user}</TableCell>
                        <TableCell>
                          <Chip 
                            label={access.status} 
                            sx={{
                              backgroundColor: access.status === 'success' ? '#4caf50' : '#ff9800',
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{new Date(access.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Paper>
      )}

      {activeTab === 5 && (
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%)', border: '2px solid #009688' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#00695c', fontWeight: 'bold' }}>
            <AuditIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#009688' }} />
            Audit & Compliance Evidence
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Complete audit logging of security events
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #009688 0%, #00796b 100%)', color: 'white', border: '2px solid #00796b' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Total Events</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{audit?.total_events || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #ff9800 0%, #ff6b35 100%)', color: 'white', border: '2px solid #ff6b35' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Blocked Actions</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{audit?.blocked_actions || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)', color: 'white', border: '2px solid #2e7d32' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Allowed Actions</Typography>
                  <Typography variant="h3" sx={{ color: 'white', fontWeight: 'bold' }}>{audit?.allowed_actions || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {audit?.recent_events && audit.recent_events.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Recent Audit Events</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Resource</TableCell>
                      <TableCell>Result</TableCell>
                      <TableCell>Reason</TableCell>
                      <TableCell>Time</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {audit.recent_events.map((event, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{event.user}</TableCell>
                        <TableCell>{event.action}</TableCell>
                        <TableCell><code>{event.resource}</code></TableCell>
                        <TableCell>
                          <Chip 
                            label={event.result} 
                            sx={{
                              backgroundColor: event.result === 'allowed' ? '#4caf50' : '#ff9800',
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{event.reason || '-'}</TableCell>
                        <TableCell>{new Date(event.timestamp).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Paper>
      )}

      {/* Analytics Summary (Legacy) */}
      {analytics && (
        <Paper sx={{ p: 3, mt: 3, background: 'linear-gradient(135deg, #e1f5fe 0%, #b3e5fc 100%)', border: '2px solid #03a9f4' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#0277bd', fontWeight: 'bold' }}>
            <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle', color: '#03a9f4' }} />
            System Analytics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)', color: 'white', border: '2px solid #1976d2' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Total Logs</Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>{analytics.total_logs?.toLocaleString() || 0}</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>Last hour</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #00bcd4 0%, #0097a7 100%)', color: 'white', border: '2px solid #0097a7' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Error Rate</Typography>
                  <Typography variant="h4" sx={{ color: 'white', fontWeight: 'bold' }}>{analytics.error_rate || 0}%</Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    {analytics.error_rate > 5 ? '⚠️ Above threshold' : 'Within normal range'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)', color: 'white', border: '2px solid #2e7d32' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>Top Services</Typography>
                  {analytics.top_services?.slice(0, 3).map((service, idx) => (
                    <Typography key={idx} variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                      {service.service}: {service.count.toLocaleString()}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Container>
  );
}

export default App;
