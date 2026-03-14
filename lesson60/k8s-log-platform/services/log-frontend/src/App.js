import React, { useState, useEffect } from "react";
import { Container, AppBar, Toolbar, Typography, Paper, Grid, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, FormControl, InputLabel, Select, MenuItem, Button, Box, Snackbar, Alert } from "@mui/material";
import axios from "axios";
import { format } from "date-fns";

function getApiBase() {
  if (typeof window !== "undefined" && window.location && window.location.origin) {
    return window.location.origin + "/api";
  }
  return process.env.REACT_APP_API_URL || "http://localhost:8000";
}
const DEMO_SERVICE = "dashboard-demo";
function App() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({ total: 0, error: 0, warn: 0, info: 0 });
  const [selectedService, setSelectedService] = useState("all");
  const [sendingDemo, setSendingDemo] = useState(false);
  const [snack, setSnack] = useState({ open: false, message: "", severity: "info" });
  const API_BASE_URL = getApiBase();
  const sendDemoLogs = async () => {
    setSendingDemo(true);
    setSnack({ open: false });
    try {
      const levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"];
      for (let i = 0; i < levels.length; i++) {
        const r = await axios.post(`${API_BASE_URL}/logs`, {
          level: levels[i],
          message: `Demo log #${i + 1} from dashboard`,
          service: DEMO_SERVICE,
        });
        if (r.status !== 200) throw new Error(r.statusText);
      }
      setSelectedService("all");
      await new Promise((r) => setTimeout(r, 300));
      const res = await axios.get(`${API_BASE_URL}/logs/recent?limit=100`);
      if (res.data && res.data.logs) {
        setLogs(res.data.logs);
        updateStats(res.data.logs);
        setSnack({ open: true, message: `Sent ${levels.length} logs. Metrics updated.`, severity: "success" });
      } else {
        setSnack({ open: true, message: "Sent but no data returned. Try selecting All Services.", severity: "warning" });
      }
    } catch (e) {
      const msg = e.response ? `${e.response.status}: ${e.response.statusText}` : e.message || "Network error";
      setSnack({ open: true, message: `Failed: ${msg}. Is the API running at ${API_BASE_URL}?`, severity: "error" });
      console.error("Demo send failed:", e);
    } finally {
      setSendingDemo(false);
    }
  };
  const fetchLogs = async () => {
    try {
      if (selectedService === "all") {
        const res = await axios.get(`${API_BASE_URL}/logs/recent?limit=100`);
        if (res.data && res.data.logs) {
          setLogs(res.data.logs);
          updateStats(res.data.logs);
        }
      } else {
        const res = await axios.get(`${API_BASE_URL}/logs/recent/${selectedService}?limit=100`);
        if (res.data && res.data.logs) {
          setLogs(res.data.logs);
          updateStats(res.data.logs);
        }
      }
    } catch (e) { console.error(e); }
  };
  const updateStats = (logsData) => {
    const s = { total: 0, error: 0, warn: 0, info: 0, debug: 0 };
    (logsData || []).forEach((log) => { s.total++; s[log.level?.toLowerCase() || "info"] = (s[log.level?.toLowerCase()] || 0) + 1; });
    setStats(s);
  };
  useEffect(() => { fetchLogs(); const id = setInterval(fetchLogs, 5000); return () => clearInterval(id); }, [selectedService]);
  const getLevelColor = (l) => ({ DEBUG: "default", INFO: "info", WARN: "warning", ERROR: "error", FATAL: "error" }[l] || "default");
  return (
    <div>
      <AppBar position="static"><Toolbar><Typography variant="h6">Log Analytics Platform</Typography></Toolbar></AppBar>
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="textSecondary">Total Logs</Typography><Typography variant="h4">{stats.total}</Typography></CardContent></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="textSecondary">Errors</Typography><Typography variant="h4" color="error">{stats.error || 0}</Typography></CardContent></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="textSecondary">Warnings</Typography><Typography variant="h4" color="warning.main">{stats.warn || 0}</Typography></CardContent></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="textSecondary">Info</Typography><Typography variant="h4" color="info.main">{stats.info || 0}</Typography></CardContent></Card></Grid>
        </Grid>
        <Paper sx={{ p: 2, mb: 3, border: "2px solid", borderColor: "primary.main", bgcolor: "grey.100" }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>No data yet? Click below to add sample logs and update the metrics.</Typography>
          <Button variant="contained" color="primary" size="large" onClick={sendDemoLogs} disabled={sendingDemo}>
            {sendingDemo ? "Sending…" : "Send demo logs"}
          </Button>
        </Paper>
        <Paper sx={{ p: 2, mb: 3 }}>
          <FormControl fullWidth><InputLabel>Service</InputLabel>
            <Select value={selectedService} onChange={(e) => setSelectedService(e.target.value)} label="Service">
              <MenuItem value="all">All Services</MenuItem>
              <MenuItem value="dashboard-demo">Dashboard Demo</MenuItem>
              <MenuItem value="demo-script">Demo Script</MenuItem>
              <MenuItem value="log-api">Log API</MenuItem>
              <MenuItem value="log-processor">Log Processor</MenuItem>
              <MenuItem value="load-test">Load Test</MenuItem>
            </Select>
          </FormControl>
        </Paper>
        <TableContainer component={Paper}>
          <Table><TableHead><TableRow><TableCell>Timestamp</TableCell><TableCell>Level</TableCell><TableCell>Service</TableCell><TableCell>Message</TableCell></TableRow></TableHead>
            <TableBody>
              {logs.map((log, i) => (
                <TableRow key={i}>
                  <TableCell>{log.timestamp ? format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss") : "N/A"}</TableCell>
                  <TableCell><Chip label={log.level} color={getLevelColor(log.level)} size="small" /></TableCell>
                  <TableCell>{log.service}</TableCell>
                  <TableCell>{log.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Container>
      <Snackbar open={snack.open} autoHideDuration={6000} onClose={() => setSnack((s) => ({ ...s, open: false }))} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>{snack.message}</Alert>
      </Snackbar>
    </div>
  );
}
export default App;
