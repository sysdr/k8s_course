import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Collapse,
  Box,
  Typography,
  CircularProgress
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { format } from 'date-fns';

function LogRow({ log }) {
  const [open, setOpen] = useState(false);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{format(log.timestamp, 'HH:mm:ss.SSS')}</TableCell>
        <TableCell>
          <Chip label={log.service || 'unknown'} size="small" />
        </TableCell>
        <TableCell>
          <Chip 
            label={log.level || log.severity || 'info'} 
            color={getSeverityColor(log.level || log.severity)}
            size="small"
          />
        </TableCell>
        <TableCell>{log.event || log.message || 'No message'}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Full Log Details
              </Typography>
              <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                {JSON.stringify(log, null, 2)}
              </pre>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

function LogViewer({ logs, loading }) {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (logs.length === 0) {
    return (
      <Box p={4} textAlign="center">
        <Typography variant="body1" color="textSecondary">
          No logs found. Make sure your services are generating logs.
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell width={50} />
            <TableCell>Timestamp</TableCell>
            <TableCell>Service</TableCell>
            <TableCell>Level</TableCell>
            <TableCell>Message</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {logs.map((log, index) => (
            <LogRow key={index} log={log} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default LogViewer;
