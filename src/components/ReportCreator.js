import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Chip,
  Card,
  CardContent,
} from '@mui/material';
import {
  ExpandMore,
  Mic,
  MicOff,
  Save,
  Print,
  ArrowBack,
  VolumeUp,
  Clear,
  PlayArrow,
  Stop,
  Pause,
} from '@mui/icons-material';
import { getTemplate, createEmptyReport } from '../templates/reportTemplates';
import { useUser } from '../contexts/UserContext';
import useSpeechRecognition from '../hooks/useSpeechRecognition';
import jsPDF from 'jspdf';

const ReportCreator = ({ reportType }) => {
  const navigate = useNavigate();
  const { currentUser } = useUser();
  const [template, setTemplate] = useState(null);
  const [reportData, setReportData] = useState({});
  const [activeField, setActiveField] = useState(null);
  const [saveDialog, setSaveDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const {
    transcript,
    isListening,
    isSupported,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechRecognition();

  useEffect(() => {
    const reportTemplate = getTemplate(reportType);
    if (reportTemplate) {
      setTemplate(reportTemplate);
      const newReport = createEmptyReport(reportType, currentUser?.id);
      setReportData(newReport.data);
    }
  }, [reportType, currentUser]);

  useEffect(() => {
    // Update the active field with speech transcript
    if (transcript && activeField) {
      const [sectionId, fieldId] = activeField.split('.');
      if (sectionId && fieldId) {
        setReportData(prev => ({
          ...prev,
          [sectionId]: {
            ...prev[sectionId],
            [fieldId]: prev[sectionId]?.[fieldId] + transcript
          }
        }));
      } else {
        setReportData(prev => ({
          ...prev,
          [activeField]: prev[activeField] + transcript
        }));
      }
      resetTranscript();
    }
  }, [transcript, activeField, resetTranscript]);

  const handleFieldChange = (fieldPath, value) => {
    const [sectionId, fieldId] = fieldPath.split('.');
    if (sectionId && fieldId) {
      setReportData(prev => ({
        ...prev,
        [sectionId]: {
          ...prev[sectionId],
          [fieldId]: value
        }
      }));
    } else {
      setReportData(prev => ({
        ...prev,
        [fieldPath]: value
      }));
    }
  };

  const getFieldValue = (fieldPath) => {
    const [sectionId, fieldId] = fieldPath.split('.');
    if (sectionId && fieldId) {
      return reportData[sectionId]?.[fieldId] || '';
    }
    return reportData[fieldPath] || '';
  };

  const handleSpeechToggle = (fieldPath) => {
    if (isListening && activeField === fieldPath) {
      stopListening();
      setActiveField(null);
    } else {
      setActiveField(fieldPath);
      startListening();
    }
  };

  const clearField = (fieldPath) => {
    handleFieldChange(fieldPath, '');
  };

  const renderField = (field, sectionId = null) => {
    const fieldPath = sectionId ? `${sectionId}.${field.id}` : field.id;
    const value = getFieldValue(fieldPath);
    const isActive = activeField === fieldPath && isListening;

    switch (field.type) {
      case 'text':
        return (
          <Box key={fieldPath} sx={{ mb: 2 }}>
            <TextField
              fullWidth
              label={field.label}
              value={value}
              onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
              required={field.required}
              InputProps={{
                endAdornment: (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {value && (
                      <IconButton size="small" onClick={() => clearField(fieldPath)}>
                        <Clear />
                      </IconButton>
                    )}
                    {isSupported && (
                      <Tooltip title={isActive ? "Arrêter l'enregistrement" : "Démarrer l'enregistrement"}>
                        <IconButton
                          size="small"
                          color={isActive ? "secondary" : "default"}
                          onClick={() => handleSpeechToggle(fieldPath)}
                        >
                          {isActive ? <MicOff /> : <Mic />}
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                )
              }}
            />
            {isActive && (
              <Typography variant="caption" color="secondary" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <VolumeUp sx={{ fontSize: 16, mr: 0.5 }} />
                Écoute en cours...
              </Typography>
            )}
          </Box>
        );

      case 'textarea':
        return (
          <Box key={fieldPath} sx={{ mb: 2 }}>
            <TextField
              fullWidth
              multiline
              rows={field.rows || 4}
              label={field.label}
              value={value}
              onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
              required={field.required}
              InputProps={{
                endAdornment: (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignSelf: 'flex-start', mt: 1 }}>
                    {value && (
                      <IconButton size="small" onClick={() => clearField(fieldPath)}>
                        <Clear />
                      </IconButton>
                    )}
                    {isSupported && (
                      <Tooltip title={isActive ? "Arrêter l'enregistrement" : "Démarrer l'enregistrement"}>
                        <IconButton
                          size="small"
                          color={isActive ? "secondary" : "default"}
                          onClick={() => handleSpeechToggle(fieldPath)}
                        >
                          {isActive ? <MicOff /> : <Mic />}
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                )
              }}
            />
            {isActive && (
              <Typography variant="caption" color="secondary" sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <VolumeUp sx={{ fontSize: 16, mr: 0.5 }} />
                Écoute en cours...
              </Typography>
            )}
          </Box>
        );

      case 'select':
        return (
          <FormControl fullWidth key={fieldPath} sx={{ mb: 2 }}>
            <InputLabel required={field.required}>{field.label}</InputLabel>
            <Select
              value={value}
              label={field.label}
              onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
              required={field.required}
            >
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'date':
        return (
          <TextField
            key={fieldPath}
            fullWidth
            type="date"
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(fieldPath, e.target.value)}
            required={field.required}
            sx={{ mb: 2 }}
            InputLabelProps={{
              shrink: true,
            }}
          />
        );

      case 'section':
        return (
          <Accordion key={fieldPath} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6">{field.label}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {field.fields?.map((subField) => (
                  <Grid item xs={12} md={subField.type === 'textarea' ? 12 : 6} key={subField.id}>
                    {renderField(subField, field.id)}
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );

      default:
        return null;
    }
  };

  const handleSave = () => {
    setIsLoading(true);
    // Simulate save operation
    setTimeout(() => {
      setIsLoading(false);
      setSaveDialog(true);
    }, 1000);
  };

  const handlePrint = () => {
    // Create PDF
    const doc = new jsPDF();
    let yPosition = 20;
    
    // Title
    doc.setFontSize(18);
    doc.text(template.title, 20, yPosition);
    yPosition += 20;
    
    // Add content (simplified)
    doc.setFontSize(12);
    const text = `Patient: ${getFieldValue('patientInfo.patientName')}
Date: ${getFieldValue('patientInfo.examDate')}
Type: ${getFieldValue('examInfo.examType')}

Technique:
${getFieldValue('technique')}

Constatations:
${getFieldValue('results.findings')}

Conclusion:
${getFieldValue('conclusion')}`;
    
    const lines = doc.splitTextToSize(text, 170);
    lines.forEach((line) => {
      doc.text(line, 20, yPosition);
      yPosition += 7;
    });
    
    doc.save(`rapport-${reportType}-${Date.now()}.pdf`);
  };

  if (!template) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography>Chargement du template...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          {template.title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={isLoading}
          >
            Sauvegarder
          </Button>
          <Button
            variant="contained"
            startIcon={<Print />}
            onClick={handlePrint}
          >
            Exporter PDF
          </Button>
        </Box>
      </Box>

      {/* Speech Recognition Status */}
      {!isSupported && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          La reconnaissance vocale n'est pas supportée par votre navigateur. 
          Veuillez utiliser Chrome, Firefox ou Safari pour profiter de cette fonctionnalité.
        </Alert>
      )}

      {speechError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Erreur de reconnaissance vocale: {speechError}
        </Alert>
      )}

      {isListening && (
        <Card sx={{ mb: 2, backgroundColor: 'action.hover' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                icon={<Mic />}
                label="Enregistrement en cours"
                color="secondary"
                variant="filled"
              />
              <Typography variant="body2">
                Champ actif: {activeField ? template.fields.find(f => f.id === activeField.split('.')[0])?.label : 'Aucun'}
              </Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={stopListening}
                startIcon={<Stop />}
              >
                Arrêter
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Form */}
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {template.fields.map((field) => (
            <Grid item xs={12} key={field.id}>
              {renderField(field)}
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Save Dialog */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)}>
        <DialogTitle>Rapport sauvegardé</DialogTitle>
        <DialogContent>
          <Typography>
            Le rapport a été sauvegardé avec succès. Vous pouvez le retrouver dans l'historique.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialog(false)}>OK</Button>
          <Button onClick={() => navigate('/history')} variant="contained">
            Voir l'historique
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportCreator;