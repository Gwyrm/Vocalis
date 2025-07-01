import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  Scanner,
  MedicalServices,
  MonitorHeart,
  Add,
  History,
  Description,
  AccessTime,
} from '@mui/icons-material';
import { useUser } from '../contexts/UserContext';
import { format } from 'date-fns';

const Dashboard = () => {
  const navigate = useNavigate();
  const { currentUser } = useUser();

  const reportTypes = [
    {
      type: 'scanner',
      title: 'Scanner',
      description: 'Créer un compte-rendu de scanner (CT)',
      icon: <Scanner sx={{ fontSize: 48 }} />,
      color: '#1976d2',
      path: '/create/scanner'
    },
    {
      type: 'mri',
      title: 'IRM',
      description: 'Créer un compte-rendu d\'IRM',
      icon: <MedicalServices sx={{ fontSize: 48 }} />,
      color: '#9c27b0',
      path: '/create/mri'
    },
    {
      type: 'echo',
      title: 'Échographie',
      description: 'Créer un compte-rendu d\'échographie',
      icon: <MonitorHeart sx={{ fontSize: 48 }} />,
      color: '#f57c00',
      path: '/create/echo'
    }
  ];

  // Mock recent reports for demo
  const recentReports = [
    {
      id: '1',
      type: 'scanner',
      patientName: 'Martin Dubois',
      examType: 'Scanner thoracique',
      date: new Date(Date.now() - 86400000), // Yesterday
      status: 'completed'
    },
    {
      id: '2',
      type: 'mri',
      patientName: 'Sophie Laurent',
      examType: 'IRM cérébrale',
      date: new Date(Date.now() - 172800000), // 2 days ago
      status: 'draft'
    },
    {
      id: '3',
      type: 'echo',
      patientName: 'Jean Moreau',
      examType: 'Échographie abdominale',
      date: new Date(Date.now() - 259200000), // 3 days ago
      status: 'completed'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'draft':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed':
        return 'Terminé';
      case 'draft':
        return 'Brouillon';
      default:
        return 'Inconnu';
    }
  };

  const getReportIcon = (type) => {
    switch (type) {
      case 'scanner':
        return <Scanner />;
      case 'mri':
        return <MedicalServices />;
      case 'echo':
        return <MonitorHeart />;
      default:
        return <Description />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Tableau de bord
      </Typography>
      
      {currentUser && (
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Bienvenue, {currentUser.name}
        </Typography>
      )}

      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
            Créer un nouveau rapport
          </Typography>
        </Grid>
        
        {reportTypes.map((reportType) => (
          <Grid item xs={12} md={4} key={reportType.type}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                }
              }}
              onClick={() => navigate(reportType.path)}
            >
              <CardContent sx={{ textAlign: 'center', pb: 1 }}>
                <Box sx={{ color: reportType.color, mb: 2 }}>
                  {reportType.icon}
                </Box>
                <Typography variant="h6" component="h2" gutterBottom>
                  {reportType.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {reportType.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pt: 0 }}>
                <Button 
                  size="medium" 
                  startIcon={<Add />}
                  sx={{ color: reportType.color }}
                >
                  Créer
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}

        {/* Recent Reports */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, mt: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <History sx={{ mr: 1 }} />
              Rapports récents
            </Typography>
            <List>
              {recentReports.map((report) => (
                <ListItem 
                  key={report.id}
                  sx={{ 
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'action.hover'
                    }
                  }}
                >
                  <ListItemIcon>
                    {getReportIcon(report.type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1">
                          {report.patientName}
                        </Typography>
                        <Chip 
                          label={getStatusLabel(report.status)}
                          color={getStatusColor(report.status)}
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {report.examType}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                          <AccessTime sx={{ fontSize: 16, mr: 0.5 }} />
                          <Typography variant="caption" color="text.secondary">
                            {format(report.date, 'dd MMMM yyyy')}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/history')}
              >
                Voir tous les rapports
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Statistiques
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Rapports ce mois:</Typography>
                <Typography variant="h6" color="primary">12</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Brouillons:</Typography>
                <Typography variant="h6" color="warning.main">3</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Terminés:</Typography>
                <Typography variant="h6" color="success.main">9</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;