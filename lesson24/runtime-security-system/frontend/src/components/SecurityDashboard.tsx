import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Card, CardContent, Grid, Chip } from '@mui/material';
import { SecurityEvent } from '../types/SecurityEvent';
import { securityAPI } from '../services/api';

const SecurityDashboard: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventsRes, statsRes] = await Promise.all([
          securityAPI.getEvents(),
          securityAPI.getStatistics()
        ]);
        setEvents(eventsRes.data);
        setStats(statsRes.data);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    const colors: any = {
      CRITICAL: 'error', ERROR: 'error', WARNING: 'warning', INFO: 'info', DEBUG: 'default'
    };
    return colors[severity] || 'default';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom>Runtime Security Dashboard</Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography color="textSecondary">Total Events</Typography>
            <Typography variant="h4">{stats?.total || 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography color="textSecondary">High Risk</Typography>
            <Typography variant="h4" color="error">{stats?.high_risk || 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography color="textSecondary">Containment Actions</Typography>
            <Typography variant="h4" color="warning">{stats?.containment || 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography color="textSecondary">Active Monitoring</Typography>
            <Typography variant="h4" color="success">ON</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom>Recent Security Events</Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {events.slice(-20).reverse().map((event) => (
          <Card key={event.event_id}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <Box>
                  <Typography variant="h6">{event.falco_event.rule}</Typography>
                  <Typography color="textSecondary" variant="body2">{event.falco_event.output}</Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                    <Chip label={event.falco_event.priority} size="small" 
                          color={getSeverityColor(event.falco_event.priority) as any} />
                    <Chip label={event.threat_category} size="small" variant="outlined" />
                    <Chip label={`Risk: ${event.risk_score.toFixed(0)}`} size="small" 
                          color={event.risk_score >= 70 ? 'error' : 'default'} />
                  </Box>
                </Box>
                <Typography variant="caption" color="textSecondary">
                  {new Date(event.falco_event.timestamp).toLocaleString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Container>
  );
};

export default SecurityDashboard;
