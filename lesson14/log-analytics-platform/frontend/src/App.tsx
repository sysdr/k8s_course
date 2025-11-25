import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Chip,
  ThemeProvider,
  createTheme
} from '@mui/material';
import { logService } from './services/logService';

// Professional theme with neutral colors
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2c3e50', // Dark slate gray
      light: '#34495e',
      dark: '#1a252f',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#27ae60', // Professional green
      light: '#2ecc71',
      dark: '#229954',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
    },
    error: {
      main: '#e74c3c',
    },
    warning: {
      main: '#f39c12',
    },
    success: {
      main: '#27ae60',
    },
    info: {
      main: '#95a5a6',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          borderRadius: '8px',
          transition: 'box-shadow 0.3s ease',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        contained: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: '6px',
          padding: '8px 16px',
        },
        outlined: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: '6px',
          padding: '8px 16px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#f8f9fa',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          color: '#2c3e50',
        },
      },
    },
  },
});

interface LogEntry {
  id: number;
  timestamp: string;
  level: string;
  message: string;
  source: string;
  host?: string;
}

interface Stats {
  total_logs: number;
  oldest_log: string;
  newest_log: string;
}

function App() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [level, setLevel] = useState<string>('');
  const [source, setSource] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await logService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await logService.queryLogs({
        level: level || undefined,
        source: source || undefined,
        limit: 50
      });
      setLogs(response.logs);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  }, [level, source]);

  useEffect(() => {
    fetchStats();
    fetchLogs();
  }, [fetchLogs]);

  const getLevelStyle = (level: string) => {
    const styles: Record<string, { bgcolor: string; color: string }> = {
      DEBUG: { bgcolor: '#ecf0f1', color: '#7f8c8d' },
      INFO: { bgcolor: '#d5f4e6', color: '#27ae60' },
      WARN: { bgcolor: '#fef5e7', color: '#f39c12' },
      ERROR: { bgcolor: '#fadbd8', color: '#e74c3c' },
      FATAL: { bgcolor: '#e8d5d5', color: '#c0392b' }
    };
    return styles[level] || { bgcolor: '#ecf0f1', color: '#7f8c8d' };
  };

  return (
    <ThemeProvider theme={theme}>
      <AppBar position="static" sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Log Analytics Platform
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Statistics Cards */}
          {stats && (
            <>
              <Grid item xs={12} md={4}>
                <Card sx={{ bgcolor: 'background.paper', borderLeft: '4px solid', borderColor: 'primary.main' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                      Total Logs
                    </Typography>
                    <Typography variant="h4" sx={{ color: 'primary.main', fontWeight: 600 }}>
                      {stats.total_logs.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ bgcolor: 'background.paper', borderLeft: '4px solid', borderColor: 'text.secondary' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                      Oldest Log
                    </Typography>
                    <Typography variant="h6" sx={{ color: 'text.primary', fontWeight: 500 }}>
                      {new Date(stats.oldest_log).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ bgcolor: 'background.paper', borderLeft: '4px solid', borderColor: 'secondary.main' }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                      Newest Log
                    </Typography>
                    <Typography variant="h6" sx={{ color: 'text.primary', fontWeight: 500 }}>
                      {new Date(stats.newest_log).toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </>
          )}

          {/* Filters */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: 'background.paper' }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'text.primary', fontWeight: 600, mb: 2 }}>
                Filters
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Level</InputLabel>
                  <Select
                    value={level}
                    label="Level"
                    onChange={(e) => setLevel(e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="DEBUG">DEBUG</MenuItem>
                    <MenuItem value="INFO">INFO</MenuItem>
                    <MenuItem value="WARN">WARN</MenuItem>
                    <MenuItem value="ERROR">ERROR</MenuItem>
                    <MenuItem value="FATAL">FATAL</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Source"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  sx={{ minWidth: 200 }}
                />

                <Button
                  variant="contained"
                  onClick={fetchLogs}
                  disabled={loading}
                  sx={{ bgcolor: 'primary.main', '&:hover': { bgcolor: 'primary.dark' } }}
                >
                  {loading ? 'Loading...' : 'Search'}
                </Button>

                <Button
                  variant="outlined"
                  onClick={() => {
                    setLevel('');
                    setSource('');
                    fetchLogs();
                  }}
                  sx={{ borderColor: 'text.secondary', color: 'text.primary', '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' } }}
                >
                  Clear
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Logs Table */}
          <Grid item xs={12}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>Host</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.level}
                          size="small"
                          sx={{
                            ...getLevelStyle(log.level),
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            height: '24px',
                          }}
                        />
                      </TableCell>
                      <TableCell>{log.source}</TableCell>
                      <TableCell>{log.message}</TableCell>
                      <TableCell>{log.host || 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

export default App;
