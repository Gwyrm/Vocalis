import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  Scanner,
  CameraAlt,
  Mic,
  TrendingUp,
  Description,
  AccessTime,
  AddCircle,
  ArrowForward,
  FolderOpen,
  FolderSpecial,
} from '@mui/icons-material';
import { useReports } from '../contexts/ReportContext';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const reportTypeIcons = {
  scanner: <Scanner />,
  irm: <CameraAlt />,
  echographie: <Mic />,
};

const reportTypeColors = {
  scanner: '#2196f3',
  irm: '#4caf50',
  echographie: '#ff9800',
};

function Dashboard() {
  const navigate = useNavigate();
  const { getRecentReports, getStatistics } = useReports();
  
  const recentReports = getRecentReports(5);
  const stats = getStatistics();

  const handleNewReport = (type) => {
    navigate(`/new-report?type=${type}`);
  };

  const handleViewReport = (reportId) => {
    navigate(`/reports/${reportId}`);
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 'bold' }}>
        Tableau de bord
      </Typography>

      {/* Quick Actions */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
              },
            }}
            onClick={() => handleNewReport('scanner')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Scanner sx={{ fontSize: 40, mr: 2 }} />
                <Typography variant="h5" fontWeight="bold">
                  Scanner
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Créer un compte-rendu de scanner
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
              },
            }}
            onClick={() => handleNewReport('irm')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CameraAlt sx={{ fontSize: 40, mr: 2 }} />
                <Typography variant="h5" fontWeight="bold">
                  IRM
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Créer un compte-rendu d'IRM
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
              },
            }}
            onClick={() => handleNewReport('echographie')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Mic sx={{ fontSize: 40, mr: 2 }} />
                <Typography variant="h5" fontWeight="bold">
                  Échographie
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Créer un compte-rendu d'échographie
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Description sx={{ color: 'primary.main', mr: 1 }} />
              <Typography variant="h6">Total rapports</Typography>
            </Box>
            <Typography variant="h3" fontWeight="bold">
              {stats.total}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
              <Typography variant="h6">Cette semaine</Typography>
            </Box>
            <Typography variant="h3" fontWeight="bold">
              {stats.lastWeek}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AccessTime sx={{ color: 'warning.main', mr: 1 }} />
              <Typography variant="h6">Ce mois</Typography>
            </Box>
            <Typography variant="h3" fontWeight="bold">
              {stats.lastMonth}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Par type
            </Typography>
            {Object.entries(stats.byType).map(([type, count]) => (
              <Box key={type} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ flexGrow: 1, mr: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(count / stats.total) * 100}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'grey.300',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: reportTypeColors[type] || '#2196f3',
                      },
                    }}
                  />
                </Box>
                <Typography variant="body2" fontWeight="bold">
                  {count}
                </Typography>
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Reports */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Rapports récents</Typography>
              <Button
                endIcon={<ArrowForward />}
                onClick={() => navigate('/reports')}
              >
                Voir tout
              </Button>
            </Box>
            
            {recentReports.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <FolderOpen sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography color="text.secondary">
                  Aucun rapport créé pour le moment
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddCircle />}
                  sx={{ mt: 2 }}
                  onClick={() => navigate('/new-report')}
                >
                  Créer un rapport
                </Button>
              </Box>
            ) : (
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
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => handleViewReport(report.id)}
                  >
                    <ListItemIcon>
                      {reportTypeIcons[report.type] || <Description />}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1">
                            {report.patientName || 'Patient anonyme'}
                          </Typography>
                          <Chip
                            label={report.type}
                            size="small"
                            sx={{
                              backgroundColor: reportTypeColors[report.type] || '#2196f3',
                              color: 'white',
                            }}
                          />
                          <Chip
                            label={report.status === 'completed' ? 'Complété' : 'Brouillon'}
                            size="small"
                            color={report.status === 'completed' ? 'success' : 'default'}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {report.indication || 'Pas d\'indication'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(report.updatedAt), 'PPpp', { locale: fr })}
                          </Typography>
                        </Box>
                      }
                    />
                    <IconButton>
                      <ArrowForward />
                    </IconButton>
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Actions rapides
            </Typography>
            <List>
              <ListItem>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<AddCircle />}
                  onClick={() => navigate('/new-report')}
                  sx={{ mb: 1 }}
                >
                  Nouveau rapport
                </Button>
              </ListItem>
              <ListItem>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<FolderSpecial />}
                  onClick={() => navigate('/templates')}
                  sx={{ mb: 1 }}
                >
                  Gérer les templates
                </Button>
              </ListItem>
              <ListItem>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Description />}
                  onClick={() => navigate('/reports')}
                >
                  Consulter les rapports
                </Button>
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;