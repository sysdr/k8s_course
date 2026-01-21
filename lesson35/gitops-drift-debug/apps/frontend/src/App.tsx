// @ts-nocheck - Type definitions available in Docker build
import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Box,
  CircularProgress,
  Divider,
  LinearProgress,
  Tooltip
} from '@mui/material';
import { Warning, CheckCircle, Error, Sync, HealthAndSafety, Timer, History } from '@mui/icons-material';
import axios from 'axios';

interface DriftEvent {
  resource_type: string;
  resource_name: string;
  namespace: string;
  git_sha: string;
  live_sha: string;
  user?: string;
  timestamp: string;
  drift_type?: string | null;
  drift_risk_level?: string | null;
  change_description?: string | null;
}

interface DeploymentInfo {
  name: string;
  namespace: string;
  replicas: number;
  image: string;
  status: string;
  drift_detected: boolean;
  // Enhanced fields
  health_status?: string;
  sync_status?: string;
  sync_mode?: string;
  auto_heal_enabled?: boolean;
  drift_grace_window_minutes?: number | null;
  drift_type?: string | null;
  drift_risk_level?: string | null;
  last_action_taken?: string | null;
  last_action_timestamp?: string | null;
}

const App: React.FC = () => {
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventsRes, deploymentsRes] = await Promise.all([
          axios.get('/api/v1/drift-events?limit=10'),
          axios.get('/api/v1/deployments')
        ]);
        
        setDriftEvents(eventsRes.data);
        setDeployments(deploymentsRes.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data from API');
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string, driftDetected: boolean) => {
    if (driftDetected) {
      return <Warning color="warning" />;
    }
    return status === 'Healthy' ? <CheckCircle color="success" /> : <Error color="error" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        GitOps Drift Detection Dashboard
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Real-time monitoring of ArgoCD sync status and drift events
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Drift Alert */}
      {driftEvents.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <strong>{driftEvents.length} drift event(s) detected</strong> - Manual kubectl changes have been detected
        </Alert>
      )}

      {/* Deployment Status Cards with Enhanced Information */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {deployments.map((deployment) => (
          <Grid item xs={12} md={4} key={`${deployment.namespace}-${deployment.name}`}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Typography variant="h6">
                    {deployment.name}
                  </Typography>
                  {getStatusIcon(deployment.status, deployment.drift_detected)}
                </Box>
                
                <Typography color="text.secondary" gutterBottom>
                  Namespace: {deployment.namespace}
                </Typography>
                
                <Divider sx={{ my: 2 }} />
                
                {/* 1. Sync Strategy Visibility */}
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                    Sync Strategy
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                    <Chip 
                      icon={<Sync />}
                      label={`Mode: ${deployment.sync_mode || 'Manual'}`}
                      color={deployment.sync_mode === 'Auto' ? 'primary' : 'default'}
                      size="small"
                    />
                    <Chip 
                      label={deployment.auto_heal_enabled ? 'Auto-Heal: ON' : 'Auto-Heal: OFF'}
                      color={deployment.auto_heal_enabled ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                  {deployment.drift_grace_window_minutes !== null && deployment.drift_grace_window_minutes !== undefined && (
                    <Box>
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        <Timer fontSize="small" color="warning" />
                        <Typography variant="caption">
                          Drift Grace Window: {deployment.drift_grace_window_minutes} minutes remaining
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(deployment.drift_grace_window_minutes / 30) * 100} 
                        color="warning"
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>
                  )}
                </Box>

                {/* 2. Health vs Sync Distinction */}
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                    Status Indicators
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    <Tooltip title="Health Status: Pods are running and responding">
                      <Chip 
                        icon={<HealthAndSafety />}
                        label={`Health: ${deployment.health_status || deployment.status}`}
                        color={deployment.health_status === 'Healthy' ? 'success' : 'error'}
                        size="small"
                      />
                    </Tooltip>
                    <Tooltip title="Sync Status: Matches Git configuration">
                      <Chip 
                        icon={<Sync />}
                        label={`Sync: ${deployment.sync_status || 'Unknown'}`}
                        color={deployment.sync_status === 'Synced' ? 'success' : 'warning'}
                        size="small"
                      />
                    </Tooltip>
                  </Box>
                  {(deployment.health_status === 'Healthy' && deployment.sync_status === 'OutOfSync') && (
                    <Alert severity="info" sx={{ mt: 1, fontSize: '0.75rem' }}>
                      Healthy but not synced - pods work but config differs from Git
                    </Alert>
                  )}
                </Box>

                {/* 3. Drift Classification */}
                {deployment.drift_detected && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                      Drift Classification
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                      {deployment.drift_type && (
                        <Chip 
                          label={`Type: ${deployment.drift_type}`}
                          color={
                            deployment.drift_type === 'Intentional' ? 'info' :
                            deployment.drift_type === 'Accidental' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      )}
                      {deployment.drift_risk_level && (
                        <Chip 
                          label={`Risk: ${deployment.drift_risk_level}`}
                          color={
                            deployment.drift_risk_level === 'Low' ? 'success' :
                            deployment.drift_risk_level === 'Medium' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      )}
                    </Box>
                  </Box>
                )}

                {/* 4. Reconciliation Outcome Tracking */}
                {deployment.last_action_taken && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                      Last Action
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <History fontSize="small" color="action" />
                      <Typography variant="body2" sx={{ flex: 1 }}>
                        {deployment.last_action_taken}
                      </Typography>
                    </Box>
                    {deployment.last_action_timestamp && (
                      <Typography variant="caption" color="text.secondary">
                        {new Date(deployment.last_action_timestamp).toLocaleString()}
                      </Typography>
                    )}
                  </Box>
                )}

                <Divider sx={{ my: 2 }} />
                
                {/* Basic Info */}
                <Box>
                  <Typography variant="body2">
                    Replicas: <strong>{deployment.replicas}</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                    Image: <strong>{deployment.image}</strong>
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Drift Events Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Recent Drift Events
        </Typography>
        
        {driftEvents.length === 0 ? (
          <Alert severity="success">
            No drift events detected. All applications are in sync with Git!
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Resource</strong></TableCell>
                  <TableCell><strong>Namespace</strong></TableCell>
                  <TableCell><strong>Drift Type</strong></TableCell>
                  <TableCell><strong>Risk Level</strong></TableCell>
                  <TableCell><strong>Git SHA</strong></TableCell>
                  <TableCell><strong>Live SHA</strong></TableCell>
                  <TableCell><strong>User</strong></TableCell>
                  <TableCell><strong>Timestamp</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {driftEvents.map((event, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      {event.resource_type}: {event.resource_name}
                    </TableCell>
                    <TableCell>{event.namespace}</TableCell>
                    <TableCell>
                      {event.drift_type ? (
                        <Chip 
                          label={event.drift_type}
                          color={
                            event.drift_type === 'Intentional' ? 'info' :
                            event.drift_type === 'Accidental' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      ) : (
                        <Typography variant="body2" color="text.secondary">Unknown</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {event.drift_risk_level ? (
                        <Chip 
                          label={event.drift_risk_level}
                          color={
                            event.drift_risk_level === 'Low' ? 'success' :
                            event.drift_risk_level === 'Medium' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      ) : (
                        <Typography variant="body2" color="text.secondary">-</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <code>{event.git_sha.substring(0, 8)}</code>
                    </TableCell>
                    <TableCell>
                      <code>{event.live_sha.substring(0, 8)}</code>
                    </TableCell>
                    <TableCell>{event.user || 'Unknown'}</TableCell>
                    <TableCell>
                      {new Date(event.timestamp).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Instructions */}
      <Paper sx={{ p: 3, mt: 3, bgcolor: '#f5f5f5' }}>
        <Typography variant="h6" gutterBottom>
          🔍 Debugging Exercise
        </Typography>
        <Typography variant="body1" paragraph>
          This dashboard shows the current sync status of your deployments. Notice that the
          <strong> worker</strong> deployment shows drift detected.
        </Typography>
        <Typography variant="body2">
          <strong>Your Task:</strong>
        </Typography>
        <ol>
          <li>Identify which deployment has drift (check the warning badges)</li>
          <li>Use kubectl to find what changed: <code>kubectl get deployment worker -n production -o yaml</code></li>
          <li>Compare with Git manifest in <code>gitops/base/worker-deployment.yaml</code></li>
          <li>Decide: Revert the change or commit it to Git?</li>
          <li>If reverting: <code>argocd app sync worker --force</code></li>
          <li>If committing: Update Git and push to make ArgoCD happy</li>
        </ol>
      </Paper>
    </Container>
  );
};

export default App;
