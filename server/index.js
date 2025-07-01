// Serveur de développement pour simuler les appels LLM
// Ce serveur peut être remplacé par une vraie API LLM en production

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Simulation de traitement LLM
app.post('/api/llm/process-transcript', async (req, res) => {
  const { transcript, examType, requiredFields } = req.body;
  
  // Simulation d'un délai de traitement
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Extraction basique d'informations (en production, cela serait fait par un vrai LLM)
  const extractedData = {
    patientInfo: {
      patientName: extractFromTranscript(transcript, /patient[e]?\s+(?:nommé[e]?\s+)?([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)/i) || '[MANQUANT]',
      patientId: extractFromTranscript(transcript, /dossier\s+(?:numéro\s+)?(\d+)/i) || '[MANQUANT]',
      birthDate: extractFromTranscript(transcript, /né[e]?\s+le\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})/i) || '[MANQUANT]',
      examDate: new Date().toISOString().split('T')[0]
    },
    examInfo: {
      examType: examType,
      indication: extractFromTranscript(transcript, /indication[s]?\s*:?\s*([^.]+)/i) || '[MANQUANT]',
      contrast: transcript.toLowerCase().includes('avec contraste') ? 'Iodé IV' : 'Aucun'
    },
    technique: generateTechnique(examType, transcript),
    results: {
      findings: extractFromTranscript(transcript, /(?:constatation[s]?|résultat[s]?|on\s+observe)\s*:?\s*(.+)/is) || '[MANQUANT]',
      measurements: extractFromTranscript(transcript, /mesure[s]?\s*:?\s*([^.]+(?:\.[^.]+)*)/i) || ''
    },
    conclusion: extractFromTranscript(transcript, /(?:conclusion[s]?|en\s+conclusion)\s*:?\s*(.+)/is) || '[MANQUANT]',
    missingFields: [],
    suggestions: generateSuggestions(examType)
  };
  
  // Identifier les champs manquants
  Object.entries(requiredFields).forEach(([field, def]) => {
    const value = getValueByPath(extractedData, field);
    if (!value || value === '[MANQUANT]') {
      extractedData.missingFields.push(field);
    }
  });
  
  res.json(extractedData);
});

// Correction et amélioration de texte
app.post('/api/llm/correct-enhance', async (req, res) => {
  const { text, context } = req.body;
  
  // Simulation d'un délai
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Corrections simples (en production, utiliser un vrai LLM)
  let correctedText = text;
  
  // Corrections orthographiques basiques
  correctedText = correctedText
    .replace(/\s+/g, ' ')
    .replace(/([.!?])\s*([a-z])/g, (match, p1, p2) => `${p1} ${p2.toUpperCase()}`)
    .trim();
  
  // S'assurer que la première lettre est en majuscule
  correctedText = correctedText.charAt(0).toUpperCase() + correctedText.slice(1);
  
  res.json({ correctedText });
});

// Génération de suggestions
app.post('/api/llm/generate-suggestions', async (req, res) => {
  const { partialData, examType } = req.body;
  
  await new Promise(resolve => setTimeout(resolve, 300));
  
  const suggestions = generateSuggestions(examType);
  
  res.json({ suggestions });
});

// Fonctions utilitaires
function extractFromTranscript(transcript, pattern) {
  const match = transcript.match(pattern);
  return match ? match[1].trim() : null;
}

function getValueByPath(obj, path) {
  return path.split('.').reduce((acc, part) => acc && acc[part], obj);
}

function generateTechnique(examType, transcript) {
  const techniques = {
    scanner: 'Examen réalisé en coupes axiales jointives sans puis avec injection de produit de contraste iodé par voie intraveineuse. Reconstructions multiplanaires.',
    mri: 'IRM 1.5 Tesla réalisée en séquences T1, T2, FLAIR, diffusion, T1 après gadolinium. Coupes dans les trois plans de l\'espace.',
    echo: 'Examen échographique réalisé avec sonde convexe en conditions techniques satisfaisantes.'
  };
  
  return techniques[examType] || 'Technique standard.';
}

function generateSuggestions(examType) {
  const suggestions = {
    scanner: [
      'Vérifier la mention du produit de contraste',
      'Préciser la région anatomique examinée',
      'Mentionner les reconstructions réalisées'
    ],
    mri: [
      'Préciser le champ magnétique (1.5T ou 3T)',
      'Lister toutes les séquences réalisées',
      'Mentionner l\'injection de gadolinium si applicable'
    ],
    echo: [
      'Préciser le type de sonde utilisée',
      'Mentionner si le patient était à jeun',
      'Inclure les mesures biométriques'
    ]
  };
  
  return suggestions[examType] || [];
}

// Démarrer le serveur
app.listen(PORT, () => {
  console.log(`Serveur de développement LLM démarré sur http://localhost:${PORT}`);
  console.log('Ce serveur simule les appels LLM pour le développement.');
  console.log('En production, remplacez par une vraie API LLM (OpenAI, Claude, etc.)');
});

module.exports = app;