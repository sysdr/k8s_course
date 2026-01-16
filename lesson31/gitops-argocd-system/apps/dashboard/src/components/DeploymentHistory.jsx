import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  Chip,
  Box,
  Typography
} from '@mui/material';
import { format } from 'date-fns';

function DeploymentHistory({ events, getStatusColor }) {
  return (
    <List>
      {events.map((event, index) => (
        <ListItem key={index} divider>
          <ListItemText
            primary={
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2" fontWeight="bold">
                  {event.app_name}
                </Typography>
                <Chip
                  label={event.sync_status}
                  color={getStatusColor(event.sync_status)}
                  size="small"
                />
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="caption" display="block">
                  {event.event_type}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {format(new Date(event.timestamp), 'MMM dd, HH:mm:ss')}
                </Typography>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}

export default DeploymentHistory;
