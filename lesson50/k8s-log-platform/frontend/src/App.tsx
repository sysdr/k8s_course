import React, { useState, useEffect, useCallback } from "react";
import {
  Container, Typography, Box, Chip, TextField, Select, MenuItem,
  FormControl, InputLabel, Paper, Table, TableHead, TableRow,
  TableCell, TableBody, CircularProgress, Alert
} from "@mui/material";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

const LEVEL_COLORS: Record<string, "default"|"info"|"warning"|"error"|"success"> = {
  DEBUG:   "default",
  INFO:    "info",
  WARN:    "warning",
  ERROR:   "error",
  FATAL:   "error",
};

interface LogRecord {
  event_id: string;
  service: string;
  level: string;
  message: string;
  timestamp: string;
  trace_id?: string;
}

interface StatsData {
  [level: string]: number;
}

function useLogData(service: string, level: string, search: string) {
  const [logs, setLogs]         = useState<LogRecord[]>([]);
  const [stats, setStats]       = useState<StatsData>({});
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string,string> = {};
      if (service) params.service = service;
      if (level)   params.level   = level;
      if (search)  params.search  = search;

      const [logsRes, statsRes] = await Promise.all([
        axios.get<LogRecord[]>(`${API_BASE}/logs`, { params }),
        axios.get<StatsData>(`${API_BASE}/logs/stats`, { params: service ? { service } : {} }),
      ]);
      setLogs(logsRes.data);
      setStats(statsRes.data);
    } catch (err: any) {
      setError(err.message ?? "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [service, level, search]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { logs, stats, loading, error, refetch: fetchData };
}

export default function App() {
  const [service, setService] = useState("");
  const [level,   setLevel]   = useState("");
  const [search,  setSearch]  = useState("");

  const { logs, stats, loading, error } = useLogData(service, level, search);

  const chartData = Object.entries(stats).map(([name, value]) => ({ name, value }));

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" fontWeight={700} mb={3}>
        Log Analytics Platform
      </Typography>

      {/* Stats Chart */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" mb={2}>Event Distribution by Level</Typography>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#1976d2" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Paper>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3, display: "flex", gap: 2, flexWrap: "wrap" }}>
        <TextField label="Service" value={service} onChange={e => setService(e.target.value)} size="small" />
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Level</InputLabel>
          <Select value={level} label="Level" onChange={e => setLevel(e.target.value)}>
            <MenuItem value="">All</MenuItem>
            {["DEBUG","INFO","WARN","ERROR","FATAL"].map(l => (
              <MenuItem key={l} value={l}>{l}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField label="Search" value={search} onChange={e => setSearch(e.target.value)} size="small" sx={{ flex: 1, minWidth: 200 }} />
      </Paper>

      {/* Logs Table */}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>
      ) : (
        <Paper>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>Trace ID</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map(row => (
                <TableRow key={row.event_id} hover>
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    {new Date(row.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>{row.service}</TableCell>
                  <TableCell>
                    <Chip label={row.level} color={LEVEL_COLORS[row.level] ?? "default"} size="small" />
                  </TableCell>
                  <TableCell sx={{ maxWidth: 500, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {row.message}
                  </TableCell>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: 11 }}>
                    {row.trace_id?.slice(0,12) ?? "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Container>
  );
}
