import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import SecurityDashboard from './components/SecurityDashboard';

const theme = createTheme({ palette: { mode: 'dark', primary: { main: '#2196f3' } } });

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SecurityDashboard />
    </ThemeProvider>
  );
}

export default App;
