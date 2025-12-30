import React, { useState, useEffect } from 'react';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Grid,
  Button,
  Alert,
  Box,
  CircularProgress
} from '@mui/material';
import BackupIcon from '@mui/icons-material/Backup';
import RestoreIcon from '@mui/icons-material/Restore';
import TransactionList from './components/TransactionList';
import StatsCard from './components/StatsCard';
import CreateTransaction from './components/CreateTransaction';
import { getStats, getTransactions, createBackup, restoreBackup } from './services/api';

function App() {
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, transData] = await Promise.all([
        getStats(),
        getTransactions()
      ]);
      setStats(statsData);
      setTransactions(transData);
      setError(null);
    } catch (err) {
      setError('Failed to load data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTransactionCreated = () => {
    setSuccess('Transaction created successfully! Data will be included in next backup.');
    loadData();
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleBackup = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await createBackup();
      setSuccess(`Backup created successfully: ${result.backup_name}`);
      setTimeout(() => setSuccess(null), 10000);
    } catch (err) {
      setError('Backup failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!window.confirm('This will restore from the latest backup. Continue?')) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const result = await restoreBackup();
      setSuccess(`Restore initiated: ${result.restore_name} from ${result.backup_name}. Please wait for completion.`);
      setTimeout(() => {
        setSuccess(null);
        loadData();
      }, 10000);
    } catch (err) {
      setError('Restore failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <BackupIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Transaction System - Backup & Restore Demo
          </Typography>
          <Button color="inherit" startIcon={<BackupIcon />} onClick={handleBackup} disabled={loading}>
            Backup Now
          </Button>
          <Button color="inherit" startIcon={<RestoreIcon />} onClick={handleRestore} disabled={loading}>
            Restore
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={3}>
                <StatsCard
                  title="Total Transactions"
                  value={stats?.total_transactions || 0}
                  color="primary"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <StatsCard
                  title="Total Volume"
                  value={`$${(stats?.total_volume || 0).toLocaleString()}`}
                  color="success"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <StatsCard
                  title="Last Hour"
                  value={stats?.recent_transactions_1h || 0}
                  color="info"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <StatsCard
                  title="Backup Size"
                  value={`${((stats?.last_backup_size || 0) / 1024 / 1024).toFixed(2)} MB`}
                  color="warning"
                />
              </Grid>
            </Grid>

            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Create Transaction
                  </Typography>
                  <CreateTransaction onSuccess={handleTransactionCreated} />
                </Paper>
              </Grid>
              <Grid item xs={12} md={8}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Recent Transactions
                  </Typography>
                  <TransactionList transactions={transactions} onRefresh={loadData} />
                </Paper>
              </Grid>
            </Grid>

            <Paper sx={{ p: 2, mt: 3 }}>
              <Alert severity="info">
                <strong>Disaster Recovery Demo:</strong> All transaction data is backed up hourly with Velero.
                Try creating transactions, then simulate a disaster (delete namespace) and restore from backup!
              </Alert>
            </Paper>
          </>
        )}
      </Container>
    </Box>
  );
}

export default App;
