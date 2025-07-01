import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Search,
  Edit,
  Delete,
  Print,
  Scanner,
  MedicalServices,
  MonitorHeart,
  FilterList,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useUser } from '../contexts/UserContext';

const ReportHistory = () => {
  const navigate = useNavigate();
  const { currentUser } = useUser();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Mock data for demonstration
  const [reports] = useState([
    {
      id: '1',
      type: 'scanner',
      patientName: 'Martin Dubois',
      patientId: 'P123456',
      examType: 'Scanner thoracique',
      date: new Date(Date.now() - 86400000),
      status: 'completed',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '2',
      type: 'mri',
      patientName: 'Sophie Laurent',
      patientId: 'P123457',
      examType: 'IRM cérébrale',
      date: new Date(Date.now() - 172800000),
      status: 'draft',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '3',
      type: 'echo',
      patientName: 'Jean Moreau',
      patientId: 'P123458',
      examType: 'Échographie abdominale',
      date: new Date(Date.now() - 259200000),
      status: 'completed',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '4',
      type: 'scanner',
      patientName: 'Marie Durand',
      patientId: 'P123459',
      examType: 'Scanner cérébral',
      date: new Date(Date.now() - 345600000),
      status: 'completed',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '5',
      type: 'mri',
      patientName: 'Pierre Bernard',
      patientId: 'P123460',
      examType: 'IRM ostéo-articulaire',
      date: new Date(Date.now() - 432000000),
      status: 'draft',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '6',
      type: 'echo',
      patientName: 'Claire Petit',
      patientId: 'P123461',
      examType: 'Échographie cardiaque',
      date: new Date(Date.now() - 518400000),
      status: 'completed',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '7',
      type: 'scanner',
      patientName: 'Antoine Martin',
      patientId: 'P123462',
      examType: 'Scanner abdomino-pelvien',
      date: new Date(Date.now() - 604800000),
      status: 'completed',
      createdBy: 'Dr. Martin Dupont'
    },
    {
      id: '8',
      type: 'mri',
      patientName: 'Isabelle Roux',
      patientId: 'P123463',
      examType: 'IRM médullaire',
      date: new Date(Date.now() - 691200000),
      status: 'draft',
      createdBy: 'Dr. Martin Dupont'
    }
  ]);

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
        return <Scanner color="primary" />;
      case 'mri':
        return <MedicalServices color="secondary" />;
      case 'echo':
        return <MonitorHeart sx={{ color: '#f57c00' }} />;
      default:
        return null;
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'scanner':
        return 'Scanner';
      case 'mri':
        return 'IRM';
      case 'echo':
        return 'Échographie';
      default:
        return type;
    }
  };

  const filteredReports = reports.filter(report => {
    const matchesSearch = 
      report.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.patientId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.examType.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || report.type === filterType;
    const matchesStatus = filterStatus === 'all' || report.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleEdit = (reportId) => {
    // In a real app, you would navigate to edit mode
    console.log('Edit report:', reportId);
  };

  const handleDelete = (reportId) => {
    // In a real app, you would show a confirmation dialog
    console.log('Delete report:', reportId);
  };

  const handlePrint = (reportId) => {
    // In a real app, you would generate and print the report
    console.log('Print report:', reportId);
  };

  // Calculate statistics
  const stats = {
    total: reports.length,
    completed: reports.filter(r => r.status === 'completed').length,
    drafts: reports.filter(r => r.status === 'draft').length,
    thisMonth: reports.filter(r => {
      const reportDate = new Date(r.date);
      const now = new Date();
      return reportDate.getMonth() === now.getMonth() && reportDate.getFullYear() === now.getFullYear();
    }).length
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Historique des Rapports
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total
              </Typography>
              <Typography variant="h5" component="div">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Terminés
              </Typography>
              <Typography variant="h5" component="div" color="success.main">
                {stats.completed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Brouillons
              </Typography>
              <Typography variant="h5" component="div" color="warning.main">
                {stats.drafts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Ce mois
              </Typography>
              <Typography variant="h5" component="div" color="primary.main">
                {stats.thisMonth}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Rechercher un patient, dossier, ou examen..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Type d'examen</InputLabel>
              <Select
                value={filterType}
                label="Type d'examen"
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="all">Tous les types</MenuItem>
                <MenuItem value="scanner">Scanner</MenuItem>
                <MenuItem value="mri">IRM</MenuItem>
                <MenuItem value="echo">Échographie</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Statut</InputLabel>
              <Select
                value={filterStatus}
                label="Statut"
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="all">Tous les statuts</MenuItem>
                <MenuItem value="completed">Terminé</MenuItem>
                <MenuItem value="draft">Brouillon</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => {
                setSearchTerm('');
                setFilterType('all');
                setFilterStatus('all');
              }}
            >
              Réinitialiser
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Reports Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Patient</TableCell>
                <TableCell>N° Dossier</TableCell>
                <TableCell>Examen</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Statut</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredReports
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((report) => (
                  <TableRow key={report.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getReportIcon(report.type)}
                        {getTypeLabel(report.type)}
                      </Box>
                    </TableCell>
                    <TableCell>{report.patientName}</TableCell>
                    <TableCell>{report.patientId}</TableCell>
                    <TableCell>{report.examType}</TableCell>
                    <TableCell>
                      {format(report.date, 'dd/MM/yyyy')}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(report.status)}
                        color={getStatusColor(report.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(report.id)}
                          title="Modifier"
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handlePrint(report.id)}
                          title="Imprimer"
                        >
                          <Print />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(report.id)}
                          title="Supprimer"
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredReports.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Lignes par page:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} sur ${count !== -1 ? count : `plus de ${to}`}`
          }
        />
      </Paper>
    </Box>
  );
};

export default ReportHistory;