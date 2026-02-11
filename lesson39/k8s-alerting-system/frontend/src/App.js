import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Typography, Box, Chip } from "@mui/material";

const ALERTMANAGER_URL = "http://localhost:9093";

function App() {
  const [alerts, setAlerts] = useState([]);
  
  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${ALERTMANAGER_URL}/api/v2/alerts`);
        setAlerts(res.data);
      } catch (e) {}
    };
    fetch();
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, []);
  
  const active = alerts.filter(a => a.status.state === "active");
  
  return (
    <Container sx={{ py: 4 }}>
      <Typography variant="h3">Alert Dashboard</Typography>
      <Typography variant="h5" sx={{ mt: 2 }}>
        Active: {active.length}
      </Typography>
      {active.map((a, i) => (
        <Box key={i} sx={{ mt: 2, p: 2, border: 1 }}>
          <Typography fontWeight="bold">{a.labels.alertname}</Typography>
          <Typography variant="body2">{a.annotations.summary}</Typography>
          <Chip label={a.labels.severity} size="small" sx={{ mt: 1 }} />
        </Box>
      ))}
    </Container>
  );
}

export default App;
