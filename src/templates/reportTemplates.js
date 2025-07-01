export const reportTemplates = {
  scanner: {
    title: 'Compte-Rendu de Scanner',
    icon: 'scanner',
    fields: [
      {
        id: 'patientInfo',
        label: 'Informations Patient',
        type: 'section',
        fields: [
          { id: 'patientName', label: 'Nom du patient', type: 'text', required: true },
          { id: 'patientId', label: 'Numéro de dossier', type: 'text', required: true },
          { id: 'birthDate', label: 'Date de naissance', type: 'date', required: true },
          { id: 'examDate', label: 'Date de l\'examen', type: 'date', required: true, defaultValue: new Date().toISOString().split('T')[0] },
        ]
      },
      {
        id: 'examInfo',
        label: 'Informations de l\'Examen',
        type: 'section',
        fields: [
          { id: 'examType', label: 'Type d\'examen', type: 'select', options: ['Scanner thoracique', 'Scanner abdomino-pelvien', 'Scanner cérébral', 'Scanner des membres', 'Scanner rachis'], required: true },
          { id: 'indication', label: 'Indication clinique', type: 'textarea', required: true },
          { id: 'contrast', label: 'Produit de contraste', type: 'select', options: ['Aucun', 'Iodé IV', 'Iodé per os', 'Iodé IV + per os'] },
        ]
      },
      {
        id: 'technique',
        label: 'Technique',
        type: 'textarea',
        defaultValue: 'Examen réalisé en coupes axiales jointives de [région] sans puis avec injection de produit de contraste iodé par voie intraveineuse (sauf contre-indication).\nReconstructions multiplanaires.'
      },
      {
        id: 'results',
        label: 'Résultats',
        type: 'section',
        fields: [
          { id: 'findings', label: 'Constatations', type: 'textarea', required: true, rows: 8 },
          { id: 'measurements', label: 'Mesures', type: 'textarea', rows: 4 },
        ]
      },
      {
        id: 'conclusion',
        label: 'Conclusion',
        type: 'textarea',
        required: true,
        rows: 4
      }
    ]
  },

  mri: {
    title: 'Compte-Rendu d\'IRM',
    icon: 'mri',
    fields: [
      {
        id: 'patientInfo',
        label: 'Informations Patient',
        type: 'section',
        fields: [
          { id: 'patientName', label: 'Nom du patient', type: 'text', required: true },
          { id: 'patientId', label: 'Numéro de dossier', type: 'text', required: true },
          { id: 'birthDate', label: 'Date de naissance', type: 'date', required: true },
          { id: 'examDate', label: 'Date de l\'examen', type: 'date', required: true, defaultValue: new Date().toISOString().split('T')[0] },
        ]
      },
      {
        id: 'examInfo',
        label: 'Informations de l\'Examen',
        type: 'section',
        fields: [
          { id: 'examType', label: 'Type d\'examen', type: 'select', options: ['IRM cérébrale', 'IRM médullaire', 'IRM ostéo-articulaire', 'IRM abdomino-pelvienne', 'IRM cardiaque'], required: true },
          { id: 'indication', label: 'Indication clinique', type: 'textarea', required: true },
          { id: 'contrast', label: 'Produit de contraste', type: 'select', options: ['Aucun', 'Gadolinium IV'] },
          { id: 'fieldStrength', label: 'Champ magnétique', type: 'select', options: ['1.5 Tesla', '3 Tesla'], defaultValue: '1.5 Tesla' },
        ]
      },
      {
        id: 'technique',
        label: 'Technique',
        type: 'textarea',
        defaultValue: 'Examen IRM [champ] Tesla réalisé en séquences :\n- T1\n- T2\n- FLAIR\n- Diffusion\n- T1 avec injection de Gadolinium (si nécessaire)\n\nCoupes dans les trois plans de l\'espace.'
      },
      {
        id: 'results',
        label: 'Résultats',
        type: 'section',
        fields: [
          { id: 'findings', label: 'Constatations', type: 'textarea', required: true, rows: 10 },
          { id: 'sequences', label: 'Analyse par séquence', type: 'textarea', rows: 6 },
          { id: 'measurements', label: 'Mesures', type: 'textarea', rows: 4 },
        ]
      },
      {
        id: 'conclusion',
        label: 'Conclusion',
        type: 'textarea',
        required: true,
        rows: 4
      }
    ]
  },

  echo: {
    title: 'Compte-Rendu d\'Échographie',
    icon: 'echo',
    fields: [
      {
        id: 'patientInfo',
        label: 'Informations Patient',
        type: 'section',
        fields: [
          { id: 'patientName', label: 'Nom du patient', type: 'text', required: true },
          { id: 'patientId', label: 'Numéro de dossier', type: 'text', required: true },
          { id: 'birthDate', label: 'Date de naissance', type: 'date', required: true },
          { id: 'examDate', label: 'Date de l\'examen', type: 'date', required: true, defaultValue: new Date().toISOString().split('T')[0] },
        ]
      },
      {
        id: 'examInfo',
        label: 'Informations de l\'Examen',
        type: 'section',
        fields: [
          { id: 'examType', label: 'Type d\'examen', type: 'select', options: ['Échographie abdominale', 'Échographie pelvienne', 'Échographie cardiaque', 'Échographie thyroïdienne', 'Échographie obstétricale', 'Échographie doppler'], required: true },
          { id: 'indication', label: 'Indication clinique', type: 'textarea', required: true },
          { id: 'probe', label: 'Sonde utilisée', type: 'select', options: ['Sonde convexe', 'Sonde linéaire', 'Sonde endocavitaire', 'Sonde cardiaque'] },
        ]
      },
      {
        id: 'technique',
        label: 'Technique',
        type: 'textarea',
        defaultValue: 'Examen échographique réalisé avec sonde [type de sonde] en conditions techniques satisfaisantes.\nPatient à jeun (si applicable).\nExploration systématique des organes demandés.'
      },
      {
        id: 'results',
        label: 'Résultats',
        type: 'section',
        fields: [
          { id: 'findings', label: 'Constatations', type: 'textarea', required: true, rows: 8 },
          { id: 'measurements', label: 'Mesures et biométrie', type: 'textarea', rows: 6 },
          { id: 'doppler', label: 'Analyse Doppler', type: 'textarea', rows: 4 },
        ]
      },
      {
        id: 'conclusion',
        label: 'Conclusion',
        type: 'textarea',
        required: true,
        rows: 4
      }
    ]
  }
};

export const getTemplate = (reportType) => {
  return reportTemplates[reportType] || null;
};

export const createEmptyReport = (reportType, userId) => {
  const template = getTemplate(reportType);
  if (!template) return null;

  const report = {
    id: Date.now().toString(),
    type: reportType,
    title: template.title,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    createdBy: userId,
    status: 'draft',
    data: {}
  };

  // Initialize empty data structure based on template
  const initializeFields = (fields) => {
    const data = {};
    fields.forEach(field => {
      if (field.type === 'section' && field.fields) {
        data[field.id] = initializeFields(field.fields);
      } else {
        data[field.id] = field.defaultValue || '';
      }
    });
    return data;
  };

  report.data = initializeFields(template.fields);
  
  return report;
};