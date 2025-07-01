import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Fab,
  Alert,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  ContentCopy,
  Scanner,
  CameraAlt,
  WifiTethering,
  Save,
  Cancel,
} from '@mui/icons-material';
import ragService from '../services/ragService';

const typeIcons = {
  scanner: <Scanner />,
  irm: <CameraAlt />,
  echographie: <WifiTethering />,
};

function TemplateManager() {
  const [templates, setTemplates] = useState([]);
  const [editDialog, setEditDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'scanner',
    sections: {},
    requiredFields: [],
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const allTemplates = await ragService.getAllTemplates();
      const localTemplates = ragService.getLocalTemplates();
      setTemplates([...allTemplates, ...localTemplates]);
    } catch (error) {
      console.error('Error loading templates:', error);
      setError('Erreur lors du chargement des templates');
    }
  };

  const handleNewTemplate = () => {
    setCurrentTemplate(null);
    setFormData({
      name: '',
      type: 'scanner',
      sections: {
        indication: '',
        technique: '',
        findings: '',
        conclusion: '',
        recommendations: '',
      },
      requiredFields: ['indication', 'technique', 'findings', 'conclusion'],
    });
    setEditDialog(true);
  };

  const handleEditTemplate = (template) => {
    setCurrentTemplate(template);
    setFormData(template);
    setEditDialog(true);
  };

  const handleDuplicateTemplate = (template) => {
    const newTemplate = {
      ...template,
      name: `${template.name} (Copie)`,
      id: undefined,
    };
    setCurrentTemplate(null);
    setFormData(newTemplate);
    setEditDialog(true);
  };

  const handleDeleteClick = (template) => {
    setCurrentTemplate(template);
    setDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    // For now, we can only delete local templates
    if (currentTemplate?.local) {
      const localTemplates = ragService.getLocalTemplates()
        .filter(t => t.id !== currentTemplate.id);
      localStorage.setItem('customTemplates', JSON.stringify(localTemplates));
      await loadTemplates();
      setSuccess('Template supprimé avec succès');
    }
    setDeleteDialog(false);
    setCurrentTemplate(null);
  };

  const handleSaveTemplate = async () => {
    try {
      setError('');
      
      if (!formData.name) {
        setError('Le nom du template est obligatoire');
        return;
      }

      await ragService.saveCustomTemplate(formData);
      await loadTemplates();
      setEditDialog(false);
      setSuccess('Template sauvegardé avec succès');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error saving template:', error);
      setError('Erreur lors de la sauvegarde du template');
    }
  };

  const handleFieldChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSectionChange = (section, value) => {
    setFormData(prev => ({
      ...prev,
      sections: {
        ...prev.sections,
        [section]: value,
      },
    }));
  };

  const toggleRequiredField = (field) => {
    setFormData(prev => ({
      ...prev,
      requiredFields: prev.requiredFields.includes(field)
        ? prev.requiredFields.filter(f => f !== field)
        : [...prev.requiredFields, field],
    }));
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight="bold">
          Gestion des Templates
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleNewTemplate}
        >
          Nouveau template
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id || template.name}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ mr: 2 }}>
                    {typeIcons[template.type] || <Scanner />}
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">
                      {template.name}
                    </Typography>
                    <Chip
                      label={template.type}
                      size="small"
                      color="primary"
                    />
                    {template.local && (
                      <Chip
                        label="Local"
                        size="small"
                        color="secondary"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  Champs obligatoires:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {template.requiredFields?.map(field => (
                    <Chip
                      key={field}
                      label={field}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<Edit />}
                  onClick={() => handleEditTemplate(template)}
                >
                  Modifier
                </Button>
                <Button
                  size="small"
                  startIcon={<ContentCopy />}
                  onClick={() => handleDuplicateTemplate(template)}
                >
                  Dupliquer
                </Button>
                {template.local && (
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteClick(template)}
                  >
                    <Delete />
                  </IconButton>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}

        {templates.length === 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Aucun template disponible
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleNewTemplate}
                sx={{ mt: 2 }}
              >
                Créer votre premier template
              </Button>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Edit Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {currentTemplate ? 'Modifier le template' : 'Nouveau template'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Nom du template"
                  value={formData.name}
                  onChange={(e) => handleFieldChange('name', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Type d'examen"
                  value={formData.type}
                  onChange={(e) => handleFieldChange('type', e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="scanner">Scanner</option>
                  <option value="irm">IRM</option>
                  <option value="echographie">Échographie</option>
                </TextField>
              </Grid>
            </Grid>

            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
              Sections du rapport
            </Typography>
            
            {Object.entries(formData.sections || {}).map(([section, value]) => (
              <Box key={section} sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label={section.charAt(0).toUpperCase() + section.slice(1)}
                  value={value}
                  onChange={(e) => handleSectionChange(section, e.target.value)}
                  multiline
                  rows={2}
                />
                <Chip
                  label="Obligatoire"
                  size="small"
                  color={formData.requiredFields?.includes(section) ? 'primary' : 'default'}
                  onClick={() => toggleRequiredField(section)}
                  sx={{ mt: 1, cursor: 'pointer' }}
                />
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>
            Annuler
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveTemplate}
            startIcon={<Save />}
          >
            Sauvegarder
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir supprimer le template "{currentTemplate?.name}" ?
            Cette action est irréversible.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>
            Annuler
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default TemplateManager;