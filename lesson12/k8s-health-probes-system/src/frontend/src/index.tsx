import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import App from './App';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00C49F' },      // Teal/Green (no blue)
    secondary: { main: '#FF8042' },     // Orange
    success: { main: '#4CAF50' },       // Green
    warning: { main: '#FFA500' },       // Amber
    error: { main: '#FF4444' },         // Red
    info: { main: '#00CED1' },          // Dark Turquoise (no blue)
    background: { default: '#0a1929', paper: '#1a2744' },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
