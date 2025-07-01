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
  Avatar,
} from '@mui/material';
import {
  Scanner,
  MedicalServices,
  MonitorHeart,
  Add,
  History,
  Description,
  AccessTime,
  LocalHospital,
  TrendingUp,
  RecordVoiceOver,
  AutoAwesome,
} from '@mui/icons-material';
import { useUser } from '../contexts/UserContext';
import { format } from 'date-fns';

const Dashboard = () => {
  const navigate = useNavigate();
  const { currentUser } = useUser();

  const reportTypes = [
    {
      id: 'scanner',
      title: 'Scanner',
      icon: <Scanner sx={{ fontSize: 48 }} />,
      description: 'Création de compte-rendu de scanner',
      color: '#2196f3',
      stats: '12 cette semaine',
    },
    {
      id: 'mri',
      title: 'IRM',
      icon: <MedicalServices sx={{ fontSize: 48 }} />,
      description: 'Création de compte-rendu d\'IRM',
      color: '#4caf50',
      stats: '8 cette semaine',
    },
    {
      id: 'echo',
      title: 'Échographie',
      icon: <LocalHospital sx={{ fontSize: 48 }} />,
      description: 'Création de compte-rendu d\'échographie',
      color: '#ff9800',
      stats: '15 cette semaine',
    },
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
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Tableau de Bord
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Bienvenue, Dr. {currentUser?.name}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
          <Chip
            icon={<RecordVoiceOver />}
            label="Interface vocale activée"
            color="primary"
            variant="outlined"
          />
          <Chip
            icon={<AutoAwesome />}
            label="IA intégrée"
            color="secondary"
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">Rapports aujourd'hui</Typography>
                  <Typography variant="h3">7</Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 48, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">Cette semaine</Typography>
                  <Typography variant="h3">35</Typography>
                </Box>
                <Description sx={{ fontSize: 48, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">Temps moyen</Typography>
                  <Typography variant="h3">4 min</Typography>
                </Box>
                <RecordVoiceOver sx={{ fontSize: 48, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Report Types */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Créer un nouveau compte-rendu
      </Typography>
      <Grid container spacing={3}>
        {reportTypes.map((type) => (
          <Grid item xs={12} md={4} key={type.id}>
            <Card 
              sx={{ 
                height: '100%',
                transition: 'all 0.3s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                }
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Avatar
                  sx={{
                    bgcolor: type.color,
                    width: 80,
                    height: 80,
                    mx: 'auto',
                    mb: 2,
                  }}
                >
                  {type.icon}
                </Avatar>
                <Typography variant="h6" gutterBottom>
                  {type.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {type.description}
                </Typography>
                <Chip
                  label="Dictée vocale"
                  size="small"
                  icon={<RecordVoiceOver />}
                  color="primary"
                  sx={{ mt: 1 }}
                />
                <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                  {type.stats}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => navigate(`/new-report/${type.id}`)}
                  startIcon={<RecordVoiceOver />}
                >
                  Commencer la dictée
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Activité récente
        </Typography>
        <Card>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Les rapports récents apparaîtront ici...
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Dashboard;