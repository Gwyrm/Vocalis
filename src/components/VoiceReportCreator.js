import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Button,
  LinearProgress,
  Chip,
  Alert,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Fab,
  Fade,
  Zoom,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Mic,
  MicOff,
  Stop,
  PlayArrow,
  Save,
  Print,
  ArrowBack,
  CheckCircle,
  Warning,
  Error,
  Lightbulb,
  AutoAwesome,
  RecordVoiceOver,
  Description,
  ExpandMore,
  Edit,
  Refresh,
  Check,
  Scanner,
  CameraAlt,
  WifiTethering,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import useSpeechRecognition from '../hooks/useSpeechRecognition';
import { useUser } from '../contexts/UserContext';
import LLMService from '../services/llmService';
import RAGService from '../services/ragService';
import jsPDF from 'jspdf';
import PDFGenerator from './PDFGenerator';
import { useReports } from '../contexts/ReportContext';

// Styled components
const PulsingMic = styled(Box)(({ theme }) => ({
  '@keyframes pulse': {
    '0%': {
      boxShadow: '0 0 0 0 rgba(244, 67, 54, 0.7)',
      transform: 'scale(1)',
    },
    '70%': {
      boxShadow: '0 0 0 30px rgba(244, 67, 54, 0)',
      transform: 'scale(1.05)',
    },
    '100%': {
      boxShadow: '0 0 0 0 rgba(244, 67, 54, 0)',
      transform: 'scale(1)',
    },
  },
  animation: 'pulse 2s infinite',
  borderRadius: '50%',
  display: 'inline-flex',
}));

const TranscriptBox = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  minHeight: 200,
  maxHeight: 400,
  overflowY: 'auto',
  backgroundColor: theme.palette.grey[50],
  border: `2px dashed ${theme.palette.grey[300]}`,
  position: 'relative',
}));

const reportTypeConfig = {
  scanner: {
    icon: <Scanner />,
    color: '#2196f3',
    label: 'Scanner',
  },
  irm: {
    icon: <CameraAlt />,
    color: '#4caf50',
    label: 'IRM',
  },
  echographie: {
    icon: <WifiTethering />,
    color: '#ff9800',
    label: 'Échographie',
  },
};

const VoiceReportCreator = () => {
  const navigate = useNavigate();
  const { reportType } = useParams();
  const [searchParams] = useSearchParams();
  const { currentUser } = useUser();
  const { createReport, updateReport } = useReports();
  const transcriptEndRef = useRef(null);
  
  // États
  const [reportData, setReportData] = useState({});
  const [fullTranscript, setFullTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  const [validationWarnings, setValidationWarnings] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  const [saveDialog, setSaveDialog] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [processingStep, setProcessingStep] = useState('');
  const [template, setTemplate] = useState(null);
  const [report, setReport] = useState({
    type: reportType,
    patientName: '',
    patientId: '',
    examDate: new Date().toISOString().split('T')[0],
    indication: '',
    technique: '',
    findings: '',
    conclusion: '',
    recommendations: '',
  });
  const [saveStatus, setSaveStatus] = useState(null);
  const [showPdfDialog, setShowPdfDialog] = useState(false);

  const {
    transcript,
    interimTranscript,
    isListening,
    isSupported,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript,
    getFullTranscript,
  } = useSpeechRecognition({
    language: currentUser?.language || 'fr-FR',
    continuous: true,
    interimResults: true,
  });

  // Load template when report type changes
  useEffect(() => {
    const loadTemplate = async () => {
      const templateData = await RAGService.getTemplate(reportType);
      setTemplate(templateData);
    };
    loadTemplate();
  }, [reportType]);

  // Auto-save functionality
  useEffect(() => {
    if (!currentUser?.autoSave || !report.id) return;

    const autoSaveTimer = setTimeout(() => {
      saveReport(true);
    }, currentUser?.autoSaveInterval || 30000); // 30 seconds default

    return () => clearTimeout(autoSaveTimer);
  }, [report, currentUser]);

  // Effet pour scroller automatiquement le transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, fullTranscript]);

  // Effet pour accumuler le transcript
  useEffect(() => {
    if (transcript && !isListening) {
      const newFullTranscript = fullTranscript + ' ' + transcript;
      setFullTranscript(newFullTranscript.trim());
      resetTranscript();
      
      // Traiter automatiquement après chaque pause
      if (newFullTranscript.length > 50) {
        processTranscript(newFullTranscript);
      }
    }
  }, [transcript, isListening]);

  // Traitement du transcript avec LLM et RAG
  const processTranscript = async (transcriptText) => {
    setIsProcessing(true);
    setProcessingStep('Analyse de la dictée...');

    try {
      // Obtenir les champs obligatoires via RAG
      const requiredFields = RAGService.getRequiredFields(reportType);
      
      // Enrichir le prompt avec les connaissances RAG
      const basePrompt = LLMService.generateSystemPrompt(reportType, requiredFields);
      const enrichedPrompt = RAGService.enrichPromptWithKnowledge(basePrompt, reportType);
      
      setProcessingStep('Extraction des informations...');
      
      // Traiter avec le LLM
      const extractedData = await LLMService.processTranscript(
        transcriptText,
        reportType,
        requiredFields
      );
      
      setProcessingStep('Validation des données...');
      
      // Valider les données extraites
      const validation = RAGService.validateExtractedData(extractedData, reportType);
      setValidationErrors(validation.errors);
      setValidationWarnings(validation.warnings);
      
      // Mettre à jour les données du rapport
      setReportData(extractedData);
      
      // Générer des suggestions contextuelles
      const contextSuggestions = RAGService.generateContextualSuggestions(
        reportType,
        extractedData,
        'general'
      );
      setSuggestions(contextSuggestions);
      
      // Afficher l'aperçu si les données sont valides
      if (validation.isValid) {
        setShowPreview(true);
      }
      
      setProcessingStep('');
    } catch (error) {
      console.error('Erreur lors du traitement:', error);
      setValidationErrors([{
        field: 'general',
        message: 'Erreur lors du traitement de la dictée',
        severity: 'error'
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Gestion de l'enregistrement
  const handleRecordToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Réinitialiser la dictée
  const handleReset = () => {
    setFullTranscript('');
    setReportData({});
    setValidationErrors([]);
    setValidationWarnings([]);
    setSuggestions([]);
    setShowPreview(false);
    resetTranscript();
  };

  // Sauvegarder le rapport
  const handleSave = async () => {
    if (validationErrors.length > 0) {
      alert('Veuillez corriger les erreurs avant de sauvegarder');
      return;
    }

    setIsProcessing(true);
    try {
      // Simulation de sauvegarde
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaveDialog(true);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Générer le PDF
  const handlePrint = () => {
    const doc = new jsPDF();
    let yPosition = 20;
    
    // Titre
    doc.setFontSize(18);
    doc.text(`Compte-Rendu ${reportType.toUpperCase()}`, 20, yPosition);
    yPosition += 20;
    
    // Contenu structuré
    doc.setFontSize(12);
    
    // Patient
    doc.setFontSize(14);
    doc.text('Informations Patient', 20, yPosition);
    yPosition += 10;
    doc.setFontSize(11);
    doc.text(`Nom: ${reportData.patientInfo?.patientName || ''}`, 25, yPosition);
    yPosition += 7;
    doc.text(`Dossier: ${reportData.patientInfo?.patientId || ''}`, 25, yPosition);
    yPosition += 7;
    doc.text(`Date de naissance: ${reportData.patientInfo?.birthDate || ''}`, 25, yPosition);
    yPosition += 7;
    doc.text(`Date d'examen: ${reportData.patientInfo?.examDate || ''}`, 25, yPosition);
    yPosition += 15;
    
    // Indication
    doc.setFontSize(14);
    doc.text('Indication', 20, yPosition);
    yPosition += 10;
    doc.setFontSize(11);
    const indicationLines = doc.splitTextToSize(reportData.examInfo?.indication || '', 160);
    indicationLines.forEach(line => {
      doc.text(line, 25, yPosition);
      yPosition += 7;
    });
    yPosition += 10;
    
    // Technique
    doc.setFontSize(14);
    doc.text('Technique', 20, yPosition);
    yPosition += 10;
    doc.setFontSize(11);
    const techniqueLines = doc.splitTextToSize(reportData.technique || '', 160);
    techniqueLines.forEach(line => {
      doc.text(line, 25, yPosition);
      yPosition += 7;
    });
    yPosition += 10;
    
    // Constatations
    if (yPosition > 250) {
      doc.addPage();
      yPosition = 20;
    }
    doc.setFontSize(14);
    doc.text('Constatations', 20, yPosition);
    yPosition += 10;
    doc.setFontSize(11);
    const findingsLines = doc.splitTextToSize(reportData.results?.findings || '', 160);
    findingsLines.forEach(line => {
      if (yPosition > 270) {
        doc.addPage();
        yPosition = 20;
      }
      doc.text(line, 25, yPosition);
      yPosition += 7;
    });
    yPosition += 10;
    
    // Conclusion
    if (yPosition > 250) {
      doc.addPage();
      yPosition = 20;
    }
    doc.setFontSize(14);
    doc.text('Conclusion', 20, yPosition);
    yPosition += 10;
    doc.setFontSize(11);
    const conclusionLines = doc.splitTextToSize(reportData.conclusion || '', 160);
    conclusionLines.forEach(line => {
      doc.text(line, 25, yPosition);
      yPosition += 7;
    });
    
    // Signature
    yPosition += 20;
    doc.text(`Dr. ${currentUser?.name || 'Médecin'}`, 20, yPosition);
    yPosition += 7;
    doc.text(new Date().toLocaleDateString('fr-FR'), 20, yPosition);
    
    doc.save(`rapport-${reportType}-${Date.now()}.pdf`);
  };

  // Éditer un champ spécifique
  const handleEditField = async (fieldPath, newValue) => {
    // Corriger avec le LLM
    const correctedValue = await LLMService.correctAndEnhance(newValue, {
      fieldPath,
      examType: reportType,
      currentData: reportData
    });
    
    // Mettre à jour les données
    const updatedData = { ...reportData };
    const pathParts = fieldPath.split('.');
    let current = updatedData;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      if (!current[pathParts[i]]) {
        current[pathParts[i]] = {};
      }
      current = current[pathParts[i]];
    }
    
    current[pathParts[pathParts.length - 1]] = correctedValue;
    setReportData(updatedData);
    
    // Revalider
    const validation = RAGService.validateExtractedData(updatedData, reportType);
    setValidationErrors(validation.errors);
    setValidationWarnings(validation.warnings);
    
    setEditingField(null);
  };

  // Process dictation with LLM
  const processDictation = async () => {
    if (!transcript) return;

    setIsProcessing(true);
    try {
      const result = await LLMService.processDictation(transcript, reportType, template);
      
      if (result.success) {
        const processedReport = {
          ...report,
          ...result.report,
          rawTranscript: transcript,
        };
        
        // Enrich with RAG data
        const enrichedReport = await RAGService.enrichReport(processedReport, reportType);
        
        setReport(enrichedReport);
        
        // Validate report
        const validation = RAGService.validateReportAgainstTemplate(enrichedReport, reportType);
        setValidationErrors(validation.errors);
      }
    } catch (error) {
      console.error('Error processing dictation:', error);
      Alert('Erreur lors du traitement de la dictée');
    } finally {
      setIsProcessing(false);
    }
  };

  // Save report
  const saveReport = async (isAutoSave = false) => {
    setSaveStatus('saving');
    
    try {
      let savedReport;
      if (report.id) {
        updateReport(report.id, report);
        savedReport = report;
      } else {
        savedReport = createReport(report);
        setReport(savedReport);
      }
      
      setSaveStatus('saved');
      if (!isAutoSave) {
        setTimeout(() => setSaveStatus(null), 3000);
      }
      
      return savedReport;
    } catch (error) {
      console.error('Error saving report:', error);
      setSaveStatus('error');
    }
  };

  // Handle field change
  const handleFieldChange = (field, value) => {
    setReport(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Toggle field editing
  const toggleFieldEdit = (field) => {
    if (editingField === field) {
      setEditingField(null);
    } else {
      setEditingField(field);
    }
  };

  // Export as PDF
  const exportPDF = async () => {
    const savedReport = await saveReport();
    if (savedReport) {
      setShowPdfDialog(true);
    }
  };

  const fieldLabels = {
    patientName: 'Nom du patient',
    patientId: 'ID patient',
    examDate: 'Date de l\'examen',
    indication: 'Indication',
    technique: 'Technique',
    findings: 'Résultats',
    conclusion: 'Conclusion',
    recommendations: 'Recommandations',
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* En-tête */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          Nouveau Compte-Rendu {reportType.toUpperCase()}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleReset}
            disabled={isProcessing}
          >
            Réinitialiser
          </Button>
          <Button
            variant="outlined"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={isProcessing || validationErrors.length > 0}
          >
            Sauvegarder
          </Button>
          <Button
            variant="contained"
            startIcon={<Print />}
            onClick={handlePrint}
            disabled={!showPreview || validationErrors.length > 0}
          >
            Exporter PDF
          </Button>
        </Box>
      </Box>

      {/* Alertes */}
      {!isSupported && (
        <Alert severity="error" sx={{ mb: 2 }}>
          La reconnaissance vocale n'est pas supportée par votre navigateur.
          Veuillez utiliser Chrome, Edge ou Safari.
        </Alert>
      )}

      {speechError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Erreur de reconnaissance vocale: {speechError}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Colonne de gauche: Interface vocale */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <RecordVoiceOver sx={{ mr: 1, verticalAlign: 'middle' }} />
              Dictée Vocale
            </Typography>
            
            {/* Zone de transcript */}
            <TranscriptBox elevation={0} sx={{ mb: 3 }}>
              {fullTranscript ? (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {fullTranscript}
                  {interimTranscript && (
                    <span style={{ color: 'primary.main', fontStyle: 'italic' }}>
                      {' '}{interimTranscript}
                    </span>
                  )}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 8 }}>
                  Cliquez sur le microphone pour commencer la dictée...
                </Typography>
              )}
              <div ref={transcriptEndRef} />
            </TranscriptBox>

            {/* Contrôles d'enregistrement */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              {isListening ? (
                <PulsingMic>
                  <Fab
                    color="secondary"
                    size="large"
                    onClick={handleRecordToggle}
                    sx={{ boxShadow: 3 }}
                  >
                    <Stop />
                  </Fab>
                </PulsingMic>
              ) : (
                <Fab
                  color="primary"
                  size="large"
                  onClick={handleRecordToggle}
                  sx={{ boxShadow: 3 }}
                >
                  <Mic />
                </Fab>
              )}
              
              <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                {isListening ? 'Enregistrement en cours... Cliquez pour arrêter' : 'Cliquez pour commencer'}
              </Typography>
            </Box>

            {/* Barre de progression */}
            {isProcessing && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress />
                <Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mt: 1 }}>
                  {processingStep}
                </Typography>
              </Box>
            )}

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <Card variant="outlined" sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    <Lightbulb sx={{ fontSize: 16, verticalAlign: 'middle', mr: 0.5 }} />
                    Suggestions
                  </Typography>
                  {suggestions.map((suggestion, idx) => (
                    <Box key={idx} sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {suggestion.title}
                      </Typography>
                      {suggestion.items && typeof suggestion.items === 'object' && (
                        <Box sx={{ ml: 2 }}>
                          {Object.entries(suggestion.items).map(([key, values]) => (
                            <Box key={key}>
                              <Typography variant="caption" fontWeight="bold">
                                {key}:
                              </Typography>
                              {Array.isArray(values) ? (
                                values.map((v, i) => (
                                  <Chip 
                                    key={i} 
                                    label={v} 
                                    size="small" 
                                    sx={{ m: 0.25 }}
                                    onClick={() => {
                                      setFullTranscript(prev => prev + ' ' + v);
                                    }}
                                  />
                                ))
                              ) : (
                                <Typography variant="caption"> {values}</Typography>
                              )}
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Box>
                  ))}
                </CardContent>
              </Card>
            )}
          </Paper>
        </Grid>

        {/* Colonne de droite: Aperçu et validation */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <Description sx={{ mr: 1, verticalAlign: 'middle' }} />
              Aperçu du Rapport
            </Typography>

            {/* Erreurs et avertissements */}
            {(validationErrors.length > 0 || validationWarnings.length > 0) && (
              <Box sx={{ mb: 2 }}>
                {validationErrors.map((error, idx) => (
                  <Alert key={idx} severity="error" sx={{ mb: 1 }}>
                    <strong>{error.field}:</strong> {error.message}
                  </Alert>
                ))}
                {validationWarnings.map((warning, idx) => (
                  <Alert key={idx} severity="warning" sx={{ mb: 1 }}>
                    <strong>{warning.field}:</strong> {warning.message}
                  </Alert>
                ))}
              </Box>
            )}

            {/* Aperçu structuré */}
            {showPreview && reportData && (
              <Box>
                {/* Informations patient */}
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>Informations Patient</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Nom du patient"
                          secondary={reportData.patientInfo?.patientName || '[MANQUANT]'}
                        />
                        <IconButton 
                          size="small"
                          onClick={() => setEditingField('patientInfo.patientName')}
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Numéro de dossier"
                          secondary={reportData.patientInfo?.patientId || '[MANQUANT]'}
                        />
                        <IconButton 
                          size="small"
                          onClick={() => setEditingField('patientInfo.patientId')}
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Date de naissance"
                          secondary={reportData.patientInfo?.birthDate || '[MANQUANT]'}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Date d'examen"
                          secondary={reportData.patientInfo?.examDate || new Date().toLocaleDateString('fr-FR')}
                        />
                      </ListItem>
                    </List>
                  </AccordionDetails>
                </Accordion>

                {/* Examen */}
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>Informations de l'Examen</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Type d'examen"
                          secondary={reportData.examInfo?.examType || reportType}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Indication"
                          secondary={reportData.examInfo?.indication || '[MANQUANT]'}
                        />
                        <IconButton 
                          size="small"
                          onClick={() => setEditingField('examInfo.indication')}
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                      </ListItem>
                      {reportData.examInfo?.contrast && (
                        <ListItem>
                          <ListItemText 
                            primary="Produit de contraste"
                            secondary={reportData.examInfo.contrast}
                          />
                        </ListItem>
                      )}
                    </List>
                  </AccordionDetails>
                </Accordion>

                {/* Technique */}
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>Technique</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {reportData.technique || '[MANQUANT]'}
                    </Typography>
                    <IconButton 
                      size="small"
                      onClick={() => setEditingField('technique')}
                      sx={{ mt: 1 }}
                    >
                      <Edit fontSize="small" />
                    </IconButton>
                  </AccordionDetails>
                </Accordion>

                {/* Résultats */}
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>Résultats</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Constatations
                      </Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                        {reportData.results?.findings || '[MANQUANT]'}
                      </Typography>
                      <IconButton 
                        size="small"
                        onClick={() => setEditingField('results.findings')}
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                      
                      {reportData.results?.measurements && (
                        <>
                          <Divider sx={{ my: 2 }} />
                          <Typography variant="subtitle2" gutterBottom>
                            Mesures
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {reportData.results.measurements}
                          </Typography>
                        </>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>

                {/* Conclusion */}
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>Conclusion</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {reportData.conclusion || '[MANQUANT]'}
                    </Typography>
                    <IconButton 
                      size="small"
                      onClick={() => setEditingField('conclusion')}
                      sx={{ mt: 1 }}
                    >
                      <Edit fontSize="small" />
                    </IconButton>
                  </AccordionDetails>
                </Accordion>
              </Box>
            )}

            {!showPreview && fullTranscript && (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <AutoAwesome sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Commencez à dicter pour voir l'aperçu du rapport...
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Dialogue de sauvegarde */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)}>
        <DialogTitle>
          <CheckCircle color="success" sx={{ verticalAlign: 'middle', mr: 1 }} />
          Rapport sauvegardé
        </DialogTitle>
        <DialogContent>
          <Typography>
            Le rapport a été sauvegardé avec succès. 
            Vous pouvez le retrouver dans l'historique des rapports.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialog(false)}>Fermer</Button>
          <Button onClick={() => navigate('/history')} variant="contained">
            Voir l'historique
          </Button>
        </DialogActions>
      </Dialog>

      {/* PDF Dialog */}
      <Dialog
        open={showPdfDialog}
        onClose={() => setShowPdfDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Aperçu PDF</DialogTitle>
        <DialogContent>
          <PDFGenerator report={report} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPdfDialog(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VoiceReportCreator;