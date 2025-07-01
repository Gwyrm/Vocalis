// Service RAG (Retrieval-Augmented Generation) pour la gestion des connaissances médicales
// Ce service maintient une base de connaissances sur les exigences spécifiques à chaque type d'examen

import axios from 'axios';

export class RAGService {
  constructor() {
    this.apiUrl = process.env.REACT_APP_RAG_API_URL || 'http://localhost:5001/api/rag';
    this.apiKey = process.env.REACT_APP_RAG_API_KEY || '';
    
    // Templates prédéfinis par type d'examen
    this.defaultTemplates = {
      scanner: {
        name: 'Scanner Standard',
        type: 'scanner',
        sections: {
          indication: 'Indication de l\'examen',
          technique: 'Technique d\'acquisition (avec ou sans injection, protocole)',
          findings: {
            thorax: '',
            abdomen: '',
            pelvis: '',
            autres: ''
          },
          conclusion: 'Synthèse et conclusion',
          recommendations: 'Recommandations de suivi'
        },
        requiredFields: ['indication', 'technique', 'findings', 'conclusion'],
        terminology: {
          normal: ['sans particularité', 'de morphologie normale', 'sans anomalie décelable'],
          pathologique: ['anomalie', 'lésion', 'masse', 'nodule', 'infiltrat']
        }
      },
      irm: {
        name: 'IRM Standard',
        type: 'irm',
        sections: {
          indication: 'Indication clinique',
          technique: 'Protocole et séquences réalisées',
          findings: {
            t1: 'Séquences T1',
            t2: 'Séquences T2',
            diffusion: 'Séquences de diffusion',
            gadolinium: 'Après injection de gadolinium'
          },
          conclusion: 'Conclusion',
          recommendations: 'Recommandations'
        },
        requiredFields: ['indication', 'technique', 'findings', 'conclusion'],
        terminology: {
          sequences: ['T1', 'T2', 'FLAIR', 'DWI', 'ADC', 'T1 Gado'],
          normal: ['signal normal', 'pas d\'anomalie de signal', 'morphologie conservée']
        }
      },
      echographie: {
        name: 'Échographie Standard',
        type: 'echographie',
        sections: {
          indication: 'Indication',
          technique: 'Technique d\'examen',
          findings: {
            foie: 'Foie',
            vesiculeBiliaire: 'Vésicule biliaire',
            voiesBiliaires: 'Voies biliaires',
            pancreas: 'Pancréas',
            rate: 'Rate',
            reins: 'Reins',
            autres: 'Autres'
          },
          measurements: {
            foie: { size: '', echogenicity: '' },
            rate: { size: '' },
            reins: { 
              droit: { size: '', cortex: '' },
              gauche: { size: '', cortex: '' }
            }
          },
          conclusion: 'Conclusion',
          recommendations: 'Recommandations'
        },
        requiredFields: ['indication', 'findings', 'conclusion'],
        normalValues: {
          foie: { size: '15-17 cm', echogenicity: 'homogène' },
          rate: { size: '< 12 cm' },
          reins: { size: '10-12 cm', cortex: '15-20 mm' }
        }
      }
    };
  }

  // Récupérer un template par type
  async getTemplate(reportType) {
    try {
      // Essayer d'abord l'API
      const response = await axios.get(`${this.apiUrl}/template/${reportType}`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });
      
      return response.data.template;
    } catch (error) {
      console.log('Using default template:', reportType);
      // Utiliser le template par défaut en cas d'erreur
      return this.defaultTemplates[reportType] || this.defaultTemplates.scanner;
    }
  }

  // Récupérer tous les templates disponibles
  async getAllTemplates() {
    try {
      const response = await axios.get(`${this.apiUrl}/templates`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });
      
      return response.data.templates;
    } catch (error) {
      console.log('Using default templates');
      return Object.values(this.defaultTemplates);
    }
  }

  // Sauvegarder un template personnalisé
  async saveCustomTemplate(template) {
    try {
      const response = await axios.post(`${this.apiUrl}/template`, template, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Error saving template:', error);
      // Sauvegarder localement en cas d'erreur
      const templates = this.getLocalTemplates();
      templates.push({ ...template, id: Date.now(), local: true });
      localStorage.setItem('customTemplates', JSON.stringify(templates));
      return { success: true, local: true };
    }
  }

  // Récupérer les templates locaux
  getLocalTemplates() {
    const stored = localStorage.getItem('customTemplates');
    return stored ? JSON.parse(stored) : [];
  }

  // Enrichir un rapport avec des informations contextuelles
  async enrichReport(report, reportType) {
    try {
      const response = await axios.post(`${this.apiUrl}/enrich`, {
        report,
        reportType,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });
      
      return response.data.enrichedReport;
    } catch (error) {
      console.log('Local enrichment fallback');
      return this.localEnrichReport(report, reportType);
    }
  }

  // Enrichissement local du rapport
  localEnrichReport(report, reportType) {
    const template = this.defaultTemplates[reportType];
    if (!template) return report;

    const enriched = { ...report };

    // Ajouter les valeurs normales pour référence
    if (template.normalValues && report.measurements) {
      enriched.normalValues = template.normalValues;
    }

    // Ajouter la terminologie médicale appropriée
    if (template.terminology) {
      enriched.terminology = template.terminology;
    }

    // Vérifier la complétude
    const missingFields = [];
    template.requiredFields.forEach(field => {
      if (!report[field] || report[field].trim() === '') {
        missingFields.push(field);
      }
    });

    enriched.validation = {
      complete: missingFields.length === 0,
      missingFields,
      completeness: ((template.requiredFields.length - missingFields.length) / template.requiredFields.length) * 100
    };

    return enriched;
  }

  // Rechercher des documents similaires
  async searchSimilarReports(query, reportType, limit = 5) {
    try {
      const response = await axios.post(`${this.apiUrl}/search`, {
        query,
        reportType,
        limit,
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
      });
      
      return response.data.results;
    } catch (error) {
      console.error('Error searching similar reports:', error);
      return [];
    }
  }

  // Télécharger des documents de référence
  async uploadReferenceDocument(file, metadata) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify(metadata));

      const response = await axios.post(`${this.apiUrl}/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  // Obtenir les champs obligatoires pour un type de rapport
  getRequiredFields(reportType) {
    const template = this.defaultTemplates[reportType];
    return template ? template.requiredFields : ['indication', 'findings', 'conclusion'];
  }

  // Obtenir les valeurs normales pour un type de rapport
  getNormalValues(reportType) {
    const template = this.defaultTemplates[reportType];
    return template ? template.normalValues : {};
  }

  // Valider un rapport selon le template
  validateReportAgainstTemplate(report, reportType) {
    const template = this.defaultTemplates[reportType];
    if (!template) return { isValid: true, errors: [] };

    const errors = [];
    const warnings = [];

    // Vérifier les champs obligatoires
    template.requiredFields.forEach(field => {
      if (!report[field] || report[field].trim() === '') {
        errors.push(`Le champ "${field}" est obligatoire`);
      }
    });

    // Vérifier les mesures si applicable
    if (template.normalValues && report.measurements) {
      Object.entries(template.normalValues).forEach(([organ, normalValue]) => {
        if (report.measurements[organ]) {
          // Ici on pourrait faire une vérification plus sophistiquée
          warnings.push(`Vérifier les mesures de ${organ} (valeurs normales: ${JSON.stringify(normalValue)})`);
        }
      });
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      completeness: ((template.requiredFields.length - errors.length) / template.requiredFields.length) * 100
    };
  }

  // Base de connaissances des champs obligatoires par type d'examen
  static knowledgeBase = {
    scanner: {
      requiredFields: {
        'patientInfo.patientName': {
          label: 'Nom du patient',
          importance: 'critique',
          format: 'Nom Prénom',
          validation: /^[A-Za-zÀ-ÿ\s-]+$/
        },
        'patientInfo.patientId': {
          label: 'Numéro de dossier',
          importance: 'critique',
          format: 'Numérique ou alphanumérique',
          validation: /^[A-Z0-9]+$/
        },
        'patientInfo.birthDate': {
          label: 'Date de naissance',
          importance: 'critique',
          format: 'JJ/MM/AAAA',
          validation: /^\d{2}\/\d{2}\/\d{4}$/
        },
        'examInfo.indication': {
          label: 'Indication clinique',
          importance: 'critique',
          format: 'Texte libre',
          examples: ['Contrôle post-opératoire', 'Bilan d\'extension', 'Recherche de lésion']
        },
        'technique': {
          label: 'Technique d\'examen',
          importance: 'haute',
          format: 'Description technique',
          template: 'Examen réalisé en coupes axiales jointives de [région] sans puis avec injection de produit de contraste iodé par voie intraveineuse.'
        },
        'results.findings': {
          label: 'Constatations',
          importance: 'critique',
          format: 'Description détaillée des observations',
          structure: ['Organe/région examiné', 'Aspect normal/pathologique', 'Dimensions si pertinent', 'Comparaison si disponible']
        },
        'conclusion': {
          label: 'Conclusion',
          importance: 'critique',
          format: 'Synthèse concise',
          guidelines: ['Répondre à la question clinique', 'Être clair et sans ambiguïté', 'Proposer une CAT si pertinent']
        }
      },
      commonFindings: {
        thoracique: [
          'Parenchyme pulmonaire de densité normale',
          'Absence de foyer de condensation parenchymateuse',
          'Médiastin de morphologie normale',
          'Absence d\'adénopathie médiastinale significative',
          'Absence d\'épanchement pleural'
        ],
        abdominopelvien: [
          'Foie de taille normale, de contours réguliers, de densité homogène',
          'Voies biliaires intra et extra-hépatiques non dilatées',
          'Vésicule biliaire alithiasique',
          'Pancréas de morphologie normale',
          'Rate de taille normale',
          'Reins de taille et de morphologie normales'
        ],
        cerebral: [
          'Pas d\'anomalie de densité du parenchyme cérébral',
          'Système ventriculaire de taille normale',
          'Espaces sous-arachnoïdiens de taille normale',
          'Ligne médiane en place',
          'Structures de la fosse postérieure sans particularité'
        ]
      },
      terminology: {
        densité: ['hypodense', 'isodense', 'hyperdense', 'spontanément hyperdense'],
        rehaussement: ['rehaussement homogène', 'rehaussement hétérogène', 'prise de contraste périphérique', 'absence de rehaussement'],
        contours: ['contours réguliers', 'contours irréguliers', 'contours lobulés', 'contours spiculés'],
        taille: ['augmenté de volume', 'diminué de volume', 'de taille normale', 'mesurant X mm/cm']
      }
    },
    
    mri: {
      requiredFields: {
        'patientInfo.patientName': {
          label: 'Nom du patient',
          importance: 'critique',
          format: 'Nom Prénom'
        },
        'patientInfo.patientId': {
          label: 'Numéro de dossier',
          importance: 'critique',
          format: 'Numérique ou alphanumérique'
        },
        'examInfo.indication': {
          label: 'Indication clinique',
          importance: 'critique',
          format: 'Texte libre'
        },
        'examInfo.fieldStrength': {
          label: 'Champ magnétique',
          importance: 'haute',
          format: '1.5T ou 3T',
          default: '1.5 Tesla'
        },
        'technique': {
          label: 'Séquences réalisées',
          importance: 'haute',
          format: 'Liste des séquences',
          template: 'IRM [champ] réalisée en séquences T1, T2, FLAIR, diffusion, T1 après gadolinium'
        },
        'results.findings': {
          label: 'Constatations',
          importance: 'critique',
          format: 'Description par séquence et par structure'
        },
        'conclusion': {
          label: 'Conclusion',
          importance: 'critique',
          format: 'Synthèse avec corrélation clinique'
        }
      },
      sequences: {
        T1: 'Analyse du signal T1 (graisse hyperintense, liquide hypointense)',
        T2: 'Analyse du signal T2 (liquide hyperintense, graisse hyperintense)',
        FLAIR: 'Suppression du signal du LCS, détection des lésions périventriculaires',
        Diffusion: 'Détection de restriction de diffusion (AVC aigu, abcès, tumeur)',
        'T1 Gado': 'Recherche de prise de contraste (rupture BHE, processus actif)'
      },
      terminology: {
        signal: ['hyposignal', 'isosignal', 'hypersignal', 'signal hétérogène'],
        rehaussement: ['rehaussement homogène', 'rehaussement hétérogène', 'rehaussement annulaire', 'absence de rehaussement'],
        diffusion: ['restriction de la diffusion', 'facilitation de la diffusion', 'ADC diminué', 'ADC augmenté']
      }
    },
    
    echo: {
      requiredFields: {
        'patientInfo.patientName': {
          label: 'Nom du patient',
          importance: 'critique'
        },
        'examInfo.indication': {
          label: 'Indication',
          importance: 'critique'
        },
        'examInfo.probe': {
          label: 'Type de sonde',
          importance: 'moyenne',
          options: ['Sonde convexe', 'Sonde linéaire', 'Sonde endocavitaire']
        },
        'results.findings': {
          label: 'Constatations',
          importance: 'critique'
        },
        'results.measurements': {
          label: 'Mesures',
          importance: 'haute',
          format: 'Biométrie avec unités'
        },
        'conclusion': {
          label: 'Conclusion',
          importance: 'critique'
        }
      },
      measurements: {
        foie: { normal: '< 15 cm sur la ligne médio-claviculaire' },
        vésiculeBiliaire: { paroi: '< 3 mm', dimensions: '< 10 x 4 cm' },
        rate: { normal: '< 12 cm grand axe' },
        rein: { normal: '9-12 cm longueur, cortex > 1.5 cm' },
        aorte: { normal: '< 3 cm' },
        thyroide: { lobe: '4-6 x 1-2 x 1.5-2 cm' }
      },
      terminology: {
        echogenicite: ['hyperéchogène', 'hypoéchogène', 'anéchogène', 'isoéchogène'],
        structure: ['homogène', 'hétérogène', 'nodulaire', 'kystique'],
        contours: ['réguliers', 'irréguliers', 'lobulés'],
        vascularisation: ['hypervascularisé', 'hypovascularisé', 'flux normal au Doppler']
      }
    }
  };

  /**
   * Récupère les champs obligatoires pour un type d'examen
   */
  static getRequiredFields(examType) {
    const kb = this.knowledgeBase[examType];
    if (!kb) return {};
    
    return Object.entries(kb.requiredFields)
      .filter(([_, field]) => field.importance === 'critique')
      .reduce((acc, [key, field]) => {
        acc[key] = field;
        return acc;
      }, {});
  }

  /**
   * Valide les données extraites contre les exigences
   */
  static validateExtractedData(data, examType) {
    const kb = this.knowledgeBase[examType];
    if (!kb) return { isValid: true, errors: [] };

    const errors = [];
    const warnings = [];

    Object.entries(kb.requiredFields).forEach(([fieldPath, fieldDef]) => {
      const value = this.getValueByPath(data, fieldPath);
      
      if (!value || value === '[MANQUANT]') {
        if (fieldDef.importance === 'critique') {
          errors.push({
            field: fieldPath,
            message: `${fieldDef.label} est obligatoire`,
            severity: 'error'
          });
        } else if (fieldDef.importance === 'haute') {
          warnings.push({
            field: fieldPath,
            message: `${fieldDef.label} est recommandé`,
            severity: 'warning'
          });
        }
      } else if (fieldDef.validation && !fieldDef.validation.test(value)) {
        errors.push({
          field: fieldPath,
          message: `${fieldDef.label} n'est pas au bon format (attendu: ${fieldDef.format})`,
          severity: 'error'
        });
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Génère des suggestions contextuelles basées sur le type d'examen et les données partielles
   */
  static generateContextualSuggestions(examType, partialData, currentSection) {
    const kb = this.knowledgeBase[examType];
    if (!kb) return [];

    const suggestions = [];

    // Suggestions de formulations standards
    if (currentSection === 'findings' && kb.commonFindings) {
      const region = this.detectRegion(partialData);
      if (region && kb.commonFindings[region]) {
        suggestions.push({
          type: 'template',
          title: 'Formulations standards',
          items: kb.commonFindings[region]
        });
      }
    }

    // Suggestions de terminologie
    if (kb.terminology) {
      suggestions.push({
        type: 'terminology',
        title: 'Terminologie recommandée',
        items: kb.terminology
      });
    }

    // Suggestions de mesures
    if (examType === 'echo' && currentSection === 'measurements' && kb.measurements) {
      suggestions.push({
        type: 'measurements',
        title: 'Valeurs normales',
        items: kb.measurements
      });
    }

    return suggestions;
  }

  /**
   * Enrichit le prompt LLM avec les connaissances spécifiques
   */
  static enrichPromptWithKnowledge(basePrompt, examType) {
    const kb = this.knowledgeBase[examType];
    if (!kb) return basePrompt;

    let enrichedPrompt = basePrompt + '\n\nCONNAISSANCES SPÉCIFIQUES:\n';
    
    // Ajouter les champs obligatoires
    enrichedPrompt += '\nChamps obligatoires:\n';
    Object.entries(kb.requiredFields).forEach(([field, def]) => {
      if (def.importance === 'critique') {
        enrichedPrompt += `- ${field}: ${def.label} (${def.format || 'texte libre'})\n`;
      }
    });

    // Ajouter les templates
    if (kb.commonFindings) {
      enrichedPrompt += '\nFormulations types disponibles pour référence.\n';
    }

    // Ajouter la terminologie
    if (kb.terminology) {
      enrichedPrompt += '\nUtilise la terminologie médicale appropriée selon le contexte.\n';
    }

    return enrichedPrompt;
  }

  // Méthodes utilitaires
  static getValueByPath(obj, path) {
    return path.split('.').reduce((acc, part) => acc && acc[part], obj);
  }

  static detectRegion(data) {
    const text = JSON.stringify(data).toLowerCase();
    if (text.includes('thorax') || text.includes('poumon') || text.includes('thoracique')) return 'thoracique';
    if (text.includes('abdomen') || text.includes('abdomino') || text.includes('foie')) return 'abdominopelvien';
    if (text.includes('cerveau') || text.includes('cérébr') || text.includes('crân')) return 'cerebral';
    return null;
  }

  /**
   * Recherche dans la base de connaissances
   */
  static async searchKnowledge(query, examType) {
    // Simulation d'une recherche vectorielle dans une base RAG
    // En production, cela pourrait être connecté à un service comme Pinecone, Weaviate, ou ChromaDB
    const kb = this.knowledgeBase[examType];
    if (!kb) return [];

    const results = [];
    const queryLower = query.toLowerCase();

    // Recherche dans les formulations communes
    if (kb.commonFindings) {
      Object.entries(kb.commonFindings).forEach(([region, findings]) => {
        findings.forEach(finding => {
          if (finding.toLowerCase().includes(queryLower)) {
            results.push({
              type: 'finding',
              content: finding,
              relevance: 0.8
            });
          }
        });
      });
    }

    // Recherche dans la terminologie
    if (kb.terminology) {
      Object.entries(kb.terminology).forEach(([category, terms]) => {
        terms.forEach(term => {
          if (term.toLowerCase().includes(queryLower)) {
            results.push({
              type: 'terminology',
              category,
              content: term,
              relevance: 0.7
            });
          }
        });
      });
    }

    return results.sort((a, b) => b.relevance - a.relevance).slice(0, 5);
  }
}

export default new RAGService();