# Vocalis - Système de Dictée de Comptes-Rendus Médicaux

Vocalis est une application web moderne conçue pour faciliter la création de comptes-rendus médicaux par dictée vocale. Elle supporte trois types d'examens : Scanner (CT), IRM et Échographie, avec des templates personnalisables et une interface utilisateur intuitive.

## 🎯 Fonctionnalités

### 📋 Templates de Rapports
- **Scanner (CT)** : Templates pour scanners thoraciques, abdominaux, cérébraux, etc.
- **IRM** : Templates pour IRM cérébrales, médullaires, ostéo-articulaires, etc.
- **Échographie** : Templates pour échographies abdominales, cardiaques, obstétricales, etc.

### 🎤 Reconnaissance Vocale
- Dictée en temps réel en français
- Support des navigateurs modernes (Chrome, Firefox, Safari)
- Activation/désactivation par champ
- Transcription automatique dans les champs de texte

### 👤 Gestion Utilisateur
- Profils personnalisables par praticien
- Préférences utilisateur (langue, templates par défaut, etc.)
- Templates personnalisés par utilisateur
- Signature automatique des rapports

### 📊 Interface Moderne
- Design responsive avec Material-UI
- Navigation intuitive avec sidebar
- Tableau de bord avec statistiques
- Historique des rapports avec filtres et recherche

### 📄 Export et Impression
- Export PDF des rapports
- Templates PDF personnalisables
- Impression directe
- Sauvegarde automatique

## 🚀 Installation et Démarrage

### Prérequis
- Node.js (version 14 ou supérieure)
- npm ou yarn

### Installation
```bash
# Installer les dépendances
npm install

# Démarrer l'application en mode développement
npm start

# Construire pour la production
npm run build
```

### Accès à l'application
L'application sera accessible à l'adresse : `http://localhost:3000`

## 🛠️ Technologies Utilisées

- **Frontend** : React 18, Material-UI 5
- **Routage** : React Router DOM
- **Reconnaissance vocale** : Web Speech API
- **Export PDF** : jsPDF
- **Icônes** : Material Icons
- **Styling** : Emotion/styled-components

## 📱 Compatibilité

### Navigateurs supportés
- Chrome (recommandé pour la reconnaissance vocale)
- Firefox
- Safari
- Edge

### Fonctionnalités de reconnaissance vocale
La reconnaissance vocale nécessite :
- Un navigateur compatible avec l'API Web Speech
- Une connexion HTTPS (en production)
- L'autorisation d'accès au microphone

## 🎯 Utilisation

### Créer un nouveau rapport
1. Accédez au tableau de bord
2. Choisissez le type d'examen (Scanner, IRM, Échographie)
3. Remplissez les informations patient
4. Utilisez la dictée vocale ou la saisie manuelle
5. Sauvegardez et exportez en PDF

### Utiliser la reconnaissance vocale
1. Cliquez sur l'icône microphone à côté d'un champ
2. Autorisez l'accès au microphone si demandé
3. Parlez clairement en français
4. Le texte apparaît automatiquement dans le champ
5. Cliquez à nouveau pour arrêter l'enregistrement

### Gérer les templates
1. Accédez au profil utilisateur
2. Onglet "Templates personnalisés"
3. Créez, modifiez ou supprimez vos templates
4. Définissez des templates par défaut

## 🔧 Configuration

### Variables d'environnement
Créez un fichier `.env` à la racine du projet :
```env
REACT_APP_API_URL=http://localhost:3001
REACT_APP_ENV=development
```

### Personnalisation
- Modifiez les templates dans `src/templates/reportTemplates.js`
- Ajustez les thèmes dans `src/index.js`
- Configurez les préférences par défaut dans les composants

## 📋 Structure du Projet

```
vocalis/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── Dashboard.js
│   │   ├── ReportCreator.js
│   │   ├── ReportHistory.js
│   │   └── UserProfile.js
│   ├── contexts/
│   │   └── UserContext.js
│   ├── hooks/
│   │   └── useSpeechRecognition.js
│   ├── templates/
│   │   └── reportTemplates.js
│   ├── App.js
│   └── index.js
├── package.json
└── README.md
```

## 🛡️ Sécurité et Confidentialité

- Aucune donnée vocale n'est stockée
- Les rapports restent locaux (pour cette version démo)
- Chiffrement recommandé pour les versions production
- Conformité RGPD pour les données médicales

## 🎓 Formation et Support

### Raccourcis clavier
- `Ctrl + S` : Sauvegarder le rapport
- `Ctrl + P` : Exporter en PDF
- `Esc` : Arrêter la reconnaissance vocale

### Conseils d'utilisation
- Parlez clairement et à un rythme normal
- Utilisez la ponctuation vocale ("point", "virgule")
- Vérifiez toujours le texte transcrit
- Sauvegardez régulièrement vos rapports

## 🔄 Roadmap

- [ ] Intégration avec systèmes PACS
- [ ] API backend pour stockage sécurisé
- [ ] Application mobile
- [ ] Templates HL7/DICOM
- [ ] Collaboration multi-utilisateur
- [ ] Intelligence artificielle pour aide au diagnostic

## 📞 Support

Pour toute question ou problème :
- Consultez la documentation en ligne
- Contactez l'équipe de support technique
- Signalez les bugs via les issues GitHub

---

**Vocalis** - Simplifiez la création de vos comptes-rendus médicaux avec la puissance de la reconnaissance vocale.
