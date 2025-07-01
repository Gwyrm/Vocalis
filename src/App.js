import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Scanner,
  MedicalServices,
  MonitorHeart,
  Person,
  ExitToApp,
  Add,
  History,
} from '@mui/icons-material';

import Dashboard from './components/Dashboard';
import ReportCreator from './components/ReportCreator';
import ReportHistory from './components/ReportHistory';
import UserProfile from './components/UserProfile';
import { UserProvider } from './contexts/UserContext';

const drawerWidth = 240;

function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Initialize with a default user
    const defaultUser = {
      id: '1',
      name: 'Dr. Martin Dupont',
      specialty: 'Radiologie',
      hospital: 'CHU de Paris',
      email: 'martin.dupont@chu-paris.fr'
    };
    setCurrentUser(defaultUser);
  }, []);

  const menuItems = [
    { text: 'Tableau de bord', icon: <MonitorHeart />, path: '/' },
    { text: 'Nouveau rapport', icon: <Add />, path: '/create' },
    { text: 'Historique', icon: <History />, path: '/history' },
    { text: 'Profil', icon: <Person />, path: '/profile' },
  ];

  const reportTypes = [
    { text: 'Scanner', icon: <Scanner />, path: '/create/scanner', type: 'scanner' },
    { text: 'IRM', icon: <MedicalServices />, path: '/create/mri', type: 'mri' },
    { text: 'Échographie', icon: <MonitorHeart />, path: '/create/echo', type: 'echo' },
  ];

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setAnchorEl(null);
    navigate('/');
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Vocalis
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setDrawerOpen(false);
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      {location.pathname === '/create' && (
        <>
          <Typography variant="subtitle2" sx={{ px: 2, py: 1, color: 'text.secondary' }}>
            Types de rapports
          </Typography>
          <List>
            {reportTypes.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  onClick={() => {
                    navigate(item.path);
                    setDrawerOpen(false);
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  );

  return (
    <UserProvider value={{ currentUser, setCurrentUser }}>
      <Box sx={{ display: 'flex' }}>
        <AppBar
          position="fixed"
          sx={{
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            ml: { sm: `${drawerWidth}px` },
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              Vocalis - Dictée de Comptes-Rendus Médicaux
            </Typography>
            {currentUser && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ mr: 2 }}>
                  {currentUser.name}
                </Typography>
                <IconButton
                  size="large"
                  aria-label="account of current user"
                  aria-controls="profile-menu"
                  aria-haspopup="true"
                  onClick={handleProfileMenuOpen}
                  color="inherit"
                >
                  <Avatar sx={{ width: 32, height: 32 }}>
                    {currentUser.name.charAt(0)}
                  </Avatar>
                </IconButton>
                <Menu
                  id="profile-menu"
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleProfileMenuClose}
                  onClick={handleProfileMenuClose}
                >
                  <MenuItem onClick={() => navigate('/profile')}>
                    <ListItemIcon>
                      <Person />
                    </ListItemIcon>
                    Profil
                  </MenuItem>
                  <MenuItem onClick={handleLogout}>
                    <ListItemIcon>
                      <ExitToApp />
                    </ListItemIcon>
                    Déconnexion
                  </MenuItem>
                </Menu>
              </Box>
            )}
          </Toolbar>
        </AppBar>

        <Box
          component="nav"
          sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        >
          <Drawer
            variant="temporary"
            open={drawerOpen}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true,
            }}
            sx={{
              display: { xs: 'block', sm: 'none' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
          >
            {drawer}
          </Drawer>
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', sm: 'block' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
            }}
            open
          >
            {drawer}
          </Drawer>
        </Box>

        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: `calc(100% - ${drawerWidth}px)` },
          }}
        >
          <Toolbar />
          <Container maxWidth="lg">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/create" element={<Dashboard />} />
              <Route path="/create/scanner" element={<ReportCreator reportType="scanner" />} />
              <Route path="/create/mri" element={<ReportCreator reportType="mri" />} />
              <Route path="/create/echo" element={<ReportCreator reportType="echo" />} />
              <Route path="/history" element={<ReportHistory />} />
              <Route path="/profile" element={<UserProfile />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </UserProvider>
  );
}

export default App;