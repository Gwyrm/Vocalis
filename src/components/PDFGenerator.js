import React, { useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Divider,
  Grid,
} from '@mui/material';
import { PictureAsPdf, Download } from '@mui/icons-material';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

function PDFGenerator({ report }) {
  const printRef = useRef();

  const handleDownloadPdf = async () => {
    const element = printRef.current;
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
    });
    
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });
    
    const imgWidth = 210; // A4 width in mm
    const pageHeight = 297; // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    const fileName = `compte-rendu-${report.patientName || 'patient'}-${format(new Date(), 'yyyy-MM-dd')}.pdf`;
    pdf.save(fileName);
  };

  const reportTypeLabels = {
    scanner: 'Scanner',
    irm: 'IRM',
    echographie: 'Échographie',
  };

  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<Download />}
          onClick={handleDownloadPdf}
        >
          Télécharger PDF
        </Button>
      </Box>

      <Paper
        ref={printRef}
        sx={{
          p: 4,
          backgroundColor: 'white',
          minHeight: '297mm',
          width: '210mm',
          margin: 'auto',
        }}
      >
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            COMPTE-RENDU D'IMAGERIE MÉDICALE
          </Typography>
          <Typography variant="h5" color="primary">
            {reportTypeLabels[report.type] || report.type}
          </Typography>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Patient Information */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            INFORMATIONS PATIENT
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body1">
                <strong>Nom :</strong> {report.patientName || 'Non renseigné'}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body1">
                <strong>ID Patient :</strong> {report.patientId || 'Non renseigné'}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body1">
                <strong>Date de l'examen :</strong> {
                  report.examDate 
                    ? format(new Date(report.examDate), 'PPP', { locale: fr })
                    : 'Non renseignée'
                }
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body1">
                <strong>Date du rapport :</strong> {
                  format(new Date(), 'PPP', { locale: fr })
                }
              </Typography>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Report Content */}
        {report.indication && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              INDICATION
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {report.indication}
            </Typography>
          </Box>
        )}

        {report.technique && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              TECHNIQUE
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {report.technique}
            </Typography>
          </Box>
        )}

        {report.findings && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              RÉSULTATS
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {report.findings}
            </Typography>
          </Box>
        )}

        {report.conclusion && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              CONCLUSION
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {report.conclusion}
            </Typography>
          </Box>
        )}

        {report.recommendations && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              RECOMMANDATIONS
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {report.recommendations}
            </Typography>
          </Box>
        )}

        {/* Footer */}
        <Box sx={{ mt: 6, pt: 4, borderTop: '1px solid #ccc' }}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Généré par Vocalis - Système de Dictée Médicale avec IA
              </Typography>
            </Grid>
            <Grid item xs={6} sx={{ textAlign: 'right' }}>
              <Typography variant="body2" color="text.secondary">
                {format(new Date(), 'PPPpp', { locale: fr })}
              </Typography>
            </Grid>
          </Grid>
        </Box>

        {/* Signature Area */}
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
          <Box sx={{ width: '45%' }}>
            <Box sx={{ borderBottom: '1px solid #000', mb: 1, height: 40 }}></Box>
            <Typography variant="body2">Signature du praticien</Typography>
          </Box>
          <Box sx={{ width: '45%' }}>
            <Box sx={{ borderBottom: '1px solid #000', mb: 1, height: 40 }}></Box>
            <Typography variant="body2">Date et cachet</Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}

export default PDFGenerator;