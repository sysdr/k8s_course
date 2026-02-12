import React from 'react';
import { Paper, Typography, Grid } from '@mui/material';

const MetricsView: React.FC = () => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h5" gutterBottom>
            Prometheus Metrics
          </Typography>
          <Typography variant="body1">
            Metrics are exposed at /metrics endpoint for each service
          </Typography>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default MetricsView;
