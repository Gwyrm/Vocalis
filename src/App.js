import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import frLocale from 'date-fns/locale/fr';

// Context
import { UserProvider } from './contexts/UserContext';

// Layout
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Chip,
} from '@mui/material';
import {
  AccountCircle,
  Logout,
  RecordVoiceOver,
  AutoAwesome,
} from '@mui/icons-material';

// Components
import Dashboard from './components/Dashboard';
import VoiceReportCreator from './components/VoiceReportCreator';
import ReportHistory from './components/ReportHistory';
import UserProfile from './components/UserProfile';

// Create French theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={frLocale}>
        <UserProvider>
          <Router>
            <Box sx={{ flexGrow: 1 }}>
              <AppBar position="fixed" elevation={2}>
                <Toolbar>
                  <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
                    Vocalis - Système de Dictée Médicale
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Chip
                      icon={<RecordVoiceOver />}
                      label="Dictée vocale"
                      color="primary"
                      variant="outlined"
                      sx={{ 
                        color: 'white',
                        borderColor: 'rgba(255,255,255,0.5)',
                        '& .MuiChip-icon': { color: 'white' }
                      }}
                    />
                    <Chip
                      icon={<AutoAwesome />}
                      label="IA"
                      color="secondary"
                      variant="outlined"
                      sx={{ 
                        color: 'white',
                        borderColor: 'rgba(255,255,255,0.5)',
                        '& .MuiChip-icon': { color: 'white' }
                      }}
                    />
                    
                    <IconButton
                      size="large"
                      aria-label="compte utilisateur"
                      aria-controls="menu-appbar"
                      aria-haspopup="true"
                      onClick={handleMenu}
                      color="inherit"
                    >
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <AccountCircle />
                      </Avatar>
                    </IconButton>
                    <Menu
                      id="menu-appbar"
                      anchorEl={anchorEl}
                      anchorOrigin={{
                        vertical: 'top',
                        horizontal: 'right',
                      }}
                      keepMounted
                      transformOrigin={{
                        vertical: 'top',
                        horizontal: 'right',
                      }}
                      open={Boolean(anchorEl)}
                      onClose={handleClose}
                    >
                      <MenuItem onClick={handleClose}>
                        <AccountCircle sx={{ mr: 1 }} />
                        Profil
                      </MenuItem>
                      <MenuItem onClick={handleClose}>
                        <Logout sx={{ mr: 1 }} />
                        Déconnexion
                      </MenuItem>
                    </Menu>
                  </Box>
                </Toolbar>
              </AppBar>
              
              <Toolbar /> {/* Spacer for fixed AppBar */}
              
              <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/new-report/:reportType" element={<VoiceReportCreator />} />
                  <Route path="/history" element={<ReportHistory />} />
                  <Route path="/profile" element={<UserProfile />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Container>
              
              <Box
                component="footer"
                sx={{
                  py: 3,
                  px: 2,
                  mt: 'auto',
                  backgroundColor: (theme) =>
                    theme.palette.mode === 'light'
                      ? theme.palette.grey[200]
                      : theme.palette.grey[800],
                  textAlign: 'center',
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  © 2024 Vocalis - Système de Dictée Médicale avec IA
                </Typography>
              </Box>
            </Box>
          </Router>
        </UserProvider>
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;