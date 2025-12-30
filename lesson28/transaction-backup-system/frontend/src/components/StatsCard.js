import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';

export default function StatsCard({ title, value, color = 'primary' }) {
  return (
    <Card>
      <CardContent>
        <Typography color="textSecondary" gutterBottom variant="body2">
          {title}
        </Typography>
        <Typography variant="h4" color={color + '.main'}>
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}
