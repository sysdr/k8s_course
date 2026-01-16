import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box
} from '@mui/material';

function ApplicationList({ applications, getStatusColor, getStatusIcon }) {
  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Application</TableCell>
            <TableCell>Namespace</TableCell>
            <TableCell>Sync Status</TableCell>
            <TableCell>Health Status</TableCell>
            <TableCell>Repository</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {applications.map((app) => (
            <TableRow key={app.name}>
              <TableCell>
                <strong>{app.name}</strong>
              </TableCell>
              <TableCell>{app.namespace}</TableCell>
              <TableCell>
                <Chip
                  icon={getStatusIcon(app.sync_status)}
                  label={app.sync_status || 'Unknown'}
                  color={getStatusColor(app.sync_status)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  icon={getStatusIcon(app.health_status)}
                  label={app.health_status || 'Unknown'}
                  color={getStatusColor(app.health_status)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Box sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
                  {app.repo_url?.substring(app.repo_url.lastIndexOf('/') + 1) || 'N/A'}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default ApplicationList;
