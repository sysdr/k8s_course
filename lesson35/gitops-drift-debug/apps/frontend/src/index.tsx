// @ts-nocheck - Type definitions available in Docker build (node_modules installed during build)
import React from 'react';
// @ts-ignore - Types available in Docker build
import ReactDOM from 'react-dom/client';
// @ts-ignore - Types available in Docker build
import { ThemeProvider, createTheme } from '@mui/material/styles';
// @ts-ignore - Types available in Docker build
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// @ts-ignore - JSX runtime available in Docker build
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
