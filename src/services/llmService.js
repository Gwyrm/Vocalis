// Service pour l'intégration avec un LLM (ex: OpenAI, Claude, ou un modèle local)
// Ce service gère le traitement des dictées vocales et la génération de rapports structurés

import axios from 'axios';

const LLM_API_URL = process.env.REACT_APP_LLM_API_URL || 'http://localhost:5000/api/llm';
const LLM_API_KEY = process.env.REACT_APP_LLM_API_KEY;

export class LLMService {
  constructor() {
    this.apiUrl = LLM_API_URL;
    this.apiKey = LLM_API_KEY;
    this.llmType = process.env.REACT_APP_LLM_TYPE || 'openai';
  }

  /**
   * Traite une dictée vocale et extrait les informations structurées
   * @param {string} transcript - La transcription vocale brute
   * @param {string} examType - Le type d'examen (scanner, mri, echo)
   * @param {Object} requiredFields - Les champs obligatoires selon le type d'examen
   * @returns {Object} Les données structurées extraites
   */
  static async processTranscript(transcript, examType, requiredFields) {
    try {
      const response = await fetch(`${LLM_API_URL}/process-transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${LLM_API_KEY}`
        },
        body: JSON.stringify({
          transcript,
          examType,
          requiredFields,
          systemPrompt: this.generateSystemPrompt(examType, requiredFields)
        })
      });

      if (!response.ok) {
        throw new Error(`LLM API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error processing transcript:', error);
      throw error;
    }
  }

  /**
   * Génère le prompt système pour le LLM basé sur le type d'examen
   */
  static generateSystemPrompt(examType, requiredFields) {
    return `Tu es un assistant médical spécialisé dans la rédaction de comptes-rendus radiologiques.
    
Tu dois extraire et structurer les informations d'une dictée vocale pour un examen de type ${examType}.

INSTRUCTIONS IMPORTANTES:
1. Identifie et extrait toutes les informations pertinentes de la dictée
2. Structure les informations selon les sections standard d'un compte-rendu radiologique
3. Corrige automatiquement les erreurs de transcription évidentes
4. Utilise la terminologie médicale appropriée
5. Assure-toi que tous les champs obligatoires sont remplis: ${JSON.stringify(requiredFields)}
6. Si une information obligatoire manque, indique-le clairement avec le marqueur [MANQUANT]

Format de sortie attendu (JSON):
{
  "patientInfo": {
    "patientName": "string",
    "patientId": "string",
    "birthDate": "date",
    "examDate": "date"
  },
  "examInfo": {
    "examType": "string",
    "indication": "string",
    "contrast": "string"
  },
  "technique": "string",
  "results": {
    "findings": "string",
    "measurements": "string"
  },
  "conclusion": "string",
  "missingFields": ["liste des champs manquants"],
  "suggestions": ["suggestions d'amélioration"]
}`;
  }

  /**
   * Corrige et améliore un texte médical
   */
  static async correctAndEnhance(text, context) {
    try {
      const response = await fetch(`${LLM_API_URL}/correct-enhance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${LLM_API_KEY}`
        },
        body: JSON.stringify({
          text,
          context,
          systemPrompt: `Corrige et améliore ce texte médical en gardant le sens original.
          Assure-toi que:
          - La terminologie médicale est correcte
          - La grammaire et l'orthographe sont parfaites
          - Le style est professionnel et adapté à un compte-rendu médical
          - Les abréviations médicales standards sont utilisées correctement`
        })
      });

      if (!response.ok) {
        throw new Error(`LLM API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.correctedText;
    } catch (error) {
      console.error('Error correcting text:', error);
      return text; // Retourne le texte original en cas d'erreur
    }
  }

  /**
   * Génère des suggestions basées sur le contexte
   */
  static async generateSuggestions(partialData, examType) {
    try {
      const response = await fetch(`${LLM_API_URL}/generate-suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${LLM_API_KEY}`
        },
        body: JSON.stringify({
          partialData,
          examType,
          systemPrompt: `Génère des suggestions pertinentes pour compléter ce compte-rendu radiologique.
          Basé sur les informations déjà fournies, suggère:
          - Des éléments à vérifier
          - Des mesures typiques à effectuer
          - Des observations courantes à ne pas oublier
          - La terminologie appropriée`
        })
      });

      if (!response.ok) {
        throw new Error(`LLM API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.suggestions;
    } catch (error) {
      console.error('Error generating suggestions:', error);
      return [];
    }
  }

  // Process dictation and structure it into a report
  async processDictation(dictationText, reportType, template = null) {
    try {
      const prompt = this.buildPrompt(dictationText, reportType, template);
      
      const response = await axios.post(`${this.apiUrl}/process`, {
        prompt,
        reportType,
        llmType: this.llmType,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Error processing dictation:', error);
      // Fallback to local processing if API fails
      return this.localProcessDictation(dictationText, reportType, template);
    }
  }

  // Build prompt for LLM
  buildPrompt(dictationText, reportType, template) {
    const typeInstructions = {
      scanner: "Structurez ce compte-rendu de scanner en incluant: indication, technique, résultats, conclusion",
      irm: "Structurez ce compte-rendu d'IRM en incluant: indication clinique, protocole, description des séquences, résultats, conclusion",
      echographie: "Structurez ce compte-rendu d'échographie en incluant: indication, technique, mesures, description, conclusion",
      general: "Structurez ce compte-rendu médical de manière claire et professionnelle"
    };

    const instruction = typeInstructions[reportType] || typeInstructions.general;
    
    let prompt = `${instruction}\n\nDictée: ${dictationText}`;
    
    if (template) {
      prompt += `\n\nUtilisez ce template comme guide:\n${JSON.stringify(template, null, 2)}`;
    }

    return prompt;
  }

  // Local fallback processing
  localProcessDictation(dictationText, reportType, template) {
    const sections = this.extractSections(dictationText, reportType);
    const corrections = this.applyMedicalCorrections(sections);
    
    return {
      success: true,
      report: corrections,
      metadata: {
        processedBy: 'local',
        reportType,
        timestamp: new Date().toISOString(),
      }
    };
  }

  // Extract sections from dictation
  extractSections(text, reportType) {
    const sections = {
      patientInfo: {},
      indication: '',
      technique: '',
      findings: '',
      conclusion: '',
      recommendations: ''
    };

    // Simple keyword-based extraction
    const keywords = {
      indication: ['indication', 'motif', 'raison', 'pour'],
      technique: ['technique', 'protocole', 'séquence', 'acquisition'],
      findings: ['résultat', 'constat', 'observation', 'mesure', 'retrouve', 'montre'],
      conclusion: ['conclusion', 'en conclusion', 'diagnostic', 'impression'],
      recommendations: ['recommand', 'suivi', 'contrôle', 'proposé']
    };

    // Split text into sentences
    const sentences = text.split(/[.!?]+/).filter(s => s.trim());
    
    sentences.forEach(sentence => {
      const lowerSentence = sentence.toLowerCase();
      
      for (const [section, words] of Object.entries(keywords)) {
        if (words.some(word => lowerSentence.includes(word))) {
          sections[section] += sentence.trim() + '. ';
          break;
        }
      }
    });

    // If no specific sections found, put all in findings
    if (!sections.findings && !sections.conclusion) {
      sections.findings = text;
    }

    return sections;
  }

  // Apply medical terminology corrections
  applyMedicalCorrections(sections) {
    const corrections = {
      // Common medical terms
      'irm': 'IRM',
      'scanner': 'Scanner',
      'echo': 'échographie',
      'ecographie': 'échographie',
      'mm': 'mm',
      'cm': 'cm',
      'ml': 'mL',
      'l': 'L',
      // Anatomical terms
      'foi': 'foie',
      'rein': 'rein',
      'reins': 'reins',
      'vesicule': 'vésicule',
      'rate': 'rate',
      'pancreas': 'pancréas',
      // Common corrections
      'pas de': 'absence de',
      'normal': 'de morphologie normale',
      'rien': 'absence d\'anomalie',
    };

    const correctedSections = {};
    
    for (const [key, value] of Object.entries(sections)) {
      if (typeof value === 'string') {
        let corrected = value;
        
        // Apply corrections
        for (const [wrong, right] of Object.entries(corrections)) {
          const regex = new RegExp(`\\b${wrong}\\b`, 'gi');
          corrected = corrected.replace(regex, right);
        }
        
        // Capitalize first letter of sentences
        corrected = corrected.replace(/(^|\. )([a-z])/g, (match, p1, p2) => p1 + p2.toUpperCase());
        
        correctedSections[key] = corrected;
      } else {
        correctedSections[key] = value;
      }
    }

    return correctedSections;
  }

  // Get report suggestions
  async getReportSuggestions(partialText, reportType) {
    try {
      const response = await axios.post(`${this.apiUrl}/suggest`, {
        text: partialText,
        reportType,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });

      return response.data.suggestions || [];
    } catch (error) {
      console.error('Error getting suggestions:', error);
      return [];
    }
  }

  // Validate report completeness
  validateReport(report, reportType) {
    const requiredFields = {
      scanner: ['indication', 'technique', 'findings', 'conclusion'],
      irm: ['indication', 'technique', 'findings', 'conclusion'],
      echographie: ['indication', 'technique', 'findings', 'conclusion'],
      general: ['findings', 'conclusion']
    };

    const required = requiredFields[reportType] || requiredFields.general;
    const missing = [];
    
    required.forEach(field => {
      if (!report[field] || report[field].trim() === '') {
        missing.push(field);
      }
    });

    return {
      isValid: missing.length === 0,
      missingFields: missing,
      completeness: ((required.length - missing.length) / required.length) * 100
    };
  }
}

// Fonction utilitaire pour utiliser un LLM local via Ollama ou similaire
export async function processWithLocalLLM(transcript, examType) {
  // Si pas d'API configurée, utilise un traitement local basique
  if (!LLM_API_URL || LLM_API_URL.includes('localhost')) {
    return processTranscriptLocally(transcript, examType);
  }
  
  return LLMService.processTranscript(transcript, examType);
}

// Traitement local basique si pas de LLM disponible
function processTranscriptLocally(transcript, examType) {
  // Extraction basique d'informations par patterns
  const result = {
    patientInfo: {
      patientName: extractPattern(transcript, /patient[e]?\s+(?:nommé[e]?\s+)?([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)/i),
      patientId: extractPattern(transcript, /dossier\s+(?:numéro\s+)?(\d+)/i),
      birthDate: extractPattern(transcript, /né[e]?\s+le\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})/i),
      examDate: new Date().toISOString().split('T')[0]
    },
    examInfo: {
      examType: examType,
      indication: extractPattern(transcript, /indication[s]?\s*:?\s*([^.]+)/i),
      contrast: extractPattern(transcript, /(?:avec|sans)\s+(?:injection\s+de\s+)?produit\s+de\s+contraste/i) || 'Aucun'
    },
    technique: extractPattern(transcript, /technique[s]?\s*:?\s*([^.]+(?:\.[^.]+)*)/i),
    results: {
      findings: extractPattern(transcript, /(?:constatation[s]?|résultat[s]?)\s*:?\s*([^.]+(?:\.[^.]+)*)/i),
      measurements: extractPattern(transcript, /mesure[s]?\s*:?\s*([^.]+(?:\.[^.]+)*)/i)
    },
    conclusion: extractPattern(transcript, /conclusion[s]?\s*:?\s*([^.]+(?:\.[^.]+)*)/i),
    missingFields: [],
    suggestions: []
  };

  // Identifier les champs manquants
  const checkMissingFields = (obj, path = '') => {
    Object.entries(obj).forEach(([key, value]) => {
      const currentPath = path ? `${path}.${key}` : key;
      if (typeof value === 'object' && value !== null) {
        checkMissingFields(value, currentPath);
      } else if (!value || value === '[MANQUANT]') {
        result.missingFields.push(currentPath);
      }
    });
  };

  checkMissingFields(result);

  return result;
}

function extractPattern(text, pattern) {
  const match = text.match(pattern);
  return match ? match[1].trim() : '[MANQUANT]';
}

export default new LLMService();