import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Search,
  FilterList,
  Visibility,
  Edit,
  Delete,
  PictureAsPdf,
  MoreVert,
  FileDownload,
  FileUpload,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useReports } from '../contexts/ReportContext';
import PDFGenerator from './PDFGenerator';

function ReportList() {
  const navigate = useNavigate();
  const { 
    reports, 
    deleteReport, 
    searchReports,
    exportReportAsJSON,
    importReportsFromJSON,
  } = useReports();
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [pdfDialog, setPdfDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);

  // Filter reports based on search
  const filteredReports = searchQuery ? searchReports(searchQuery) : reports;

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleMenuOpen = (event, report) => {
    setAnchorEl(event.currentTarget);
    setSelectedReport(report);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleViewReport = (report) => {
    navigate(`/reports/${report.id}`);
    handleMenuClose();
  };

  const handleEditReport = (report) => {
    navigate(`/new-report?id=${report.id}`);
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    setDeleteDialog(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (selectedReport) {
      deleteReport(selectedReport.id);
    }
    setDeleteDialog(false);
    setSelectedReport(null);
  };

  const handleExportPDF = () => {
    setPdfDialog(true);
    handleMenuClose();
  };

  const handleExportJSON = () => {
    if (selectedReport) {
      exportReportAsJSON(selectedReport.id);
    }
    handleMenuClose();
  };

  const handleImportFile = async (event) => {
    const file = event.target.files[0];
    if (file) {
      try {
        await importReportsFromJSON(file);
        setImportDialog(false);
      } catch (error) {
        console.error('Error importing file:', error);
      }
    }
  };

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
        return 'Complété';
      case 'draft':
        return 'Brouillon';
      default:
        return status;
    }
  };

  const reportTypeLabels = {
    scanner: 'Scanner',
    irm: 'IRM',
    echographie: 'Échographie',
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight="bold">
          Mes Rapports
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<FileUpload />}
            onClick={() => setImportDialog(true)}
          >
            Importer
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate('/new-report')}
          >
            Nouveau rapport
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        {/* Search Bar */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Rechercher par nom de patient, ID, type d'examen..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {/* Reports Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Patient</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Statut</TableCell>
                <TableCell>Indication</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredReports
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((report) => (
                  <TableRow
                    key={report.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleViewReport(report)}
                  >
                    <TableCell>
                      <Box>
                        <Typography variant="body1">
                          {report.patientName || 'Patient anonyme'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {report.patientId || 'N/A'}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={reportTypeLabels[report.type] || report.type}
                        size="small"
                        color="primary"
                      />
                    </TableCell>
                    <TableCell>
                      {format(new Date(report.updatedAt), 'PP', { locale: fr })}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(report.status)}
                        size="small"
                        color={getStatusColor(report.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {report.indication || 'Non renseigné'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMenuOpen(e, report);
                        }}
                      >
                        <MoreVert />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              
              {filteredReports.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      Aucun rapport trouvé
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
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
          labelRowsPerPage="Lignes par page"
        />
      </Paper>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleViewReport(selectedReport)}>
          <Visibility sx={{ mr: 1 }} />
          Voir
        </MenuItem>
        <MenuItem onClick={() => handleEditReport(selectedReport)}>
          <Edit sx={{ mr: 1 }} />
          Modifier
        </MenuItem>
        <MenuItem onClick={handleExportPDF}>
          <PictureAsPdf sx={{ mr: 1 }} />
          Exporter PDF
        </MenuItem>
        <MenuItem onClick={handleExportJSON}>
          <FileDownload sx={{ mr: 1 }} />
          Exporter JSON
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Supprimer
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir supprimer ce rapport ? Cette action est irréversible.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>
            Annuler
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>

      {/* PDF Export Dialog */}
      <Dialog
        open={pdfDialog}
        onClose={() => setPdfDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Aperçu PDF</DialogTitle>
        <DialogContent>
          {selectedReport && <PDFGenerator report={selectedReport} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPdfDialog(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={importDialog} onClose={() => setImportDialog(false)}>
        <DialogTitle>Importer des rapports</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Sélectionnez un fichier JSON contenant les rapports à importer.
          </Typography>
          <input
            type="file"
            accept=".json"
            onChange={handleImportFile}
            style={{ marginTop: 16 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialog(false)}>
            Annuler
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ReportList;