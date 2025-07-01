# Vocalis - Système de Dictée Médicale avec IA

Vocalis est une application web moderne qui révolutionne la création de comptes-rendus médicaux en utilisant la reconnaissance vocale et l'intelligence artificielle.

## 🎯 Fonctionnalités principales

- **🎤 Dictée vocale** : Plus besoin de remplir des formulaires ! Dictez simplement votre compte-rendu
- **🤖 Traitement par IA** : Un LLM analyse et structure automatiquement vos dictées
- **📋 RAG intégré** : Détection automatique des champs obligatoires selon le type d'examen
- **✨ Corrections automatiques** : L'IA corrige et améliore la terminologie médicale
- **📄 Export PDF** : Génération de rapports professionnels en un clic

## 🚀 Démarrage rapide

### Prérequis

- Node.js 14+ et npm
- Navigateur moderne supportant la reconnaissance vocale (Chrome, Edge, Safari)

### Installation

1. **Cloner le projet**
```bash
git clone https://github.com/votre-username/vocalis.git
cd vocalis
```

2. **Installer les dépendances du client**
```bash
npm install
```

3. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditez .env avec vos paramètres
```

4. **(Optionnel) Installer le serveur de développement**
```bash
cd server
npm install
```

### Lancement

**Client React :**
```bash
npm start
```

**Serveur de développement (optionnel) :**
```bash
cd server
npm start
```

L'application sera accessible sur http://localhost:3000

## � Comment ça marche ?

1. **Choisissez le type d'examen** (Scanner, IRM, Échographie)
2. **Cliquez sur le microphone** et commencez à dicter
3. **L'IA structure automatiquement** votre dictée en temps réel
4. **Vérifiez et ajustez** si nécessaire (édition possible de chaque champ)
5. **Exportez en PDF** ou sauvegardez pour plus tard

## 🏗️ Architecture

```
vocalis/
├── src/
│   ├── components/
│   │   ├── VoiceReportCreator.js  # Interface de dictée vocale
│   │   ├── Dashboard.js           # Tableau de bord
│   │   └── ...
│   ├── services/
│   │   ├── llmService.js          # Intégration avec le LLM
│   │   └── ragService.js          # Base de connaissances médicales
│   ├── hooks/
│   │   └── useSpeechRecognition.js # Hook pour la reconnaissance vocale
│   └── contexts/
│       └── UserContext.js         # Gestion de l'utilisateur
├── server/                        # Serveur de développement (optionnel)
└── public/
```

## 🤖 Intégration LLM

Le système peut être configuré pour utiliser différents LLM :

- **OpenAI GPT** : Configurez `REACT_APP_LLM_API_KEY` avec votre clé OpenAI
- **Claude (Anthropic)** : Compatible avec l'API Claude
- **Modèles locaux** : Via Ollama ou similaire
- **Serveur de développement** : Inclus pour tester sans API externe

## 📚 Base de connaissances RAG

Le système RAG intégré contient :
- Champs obligatoires par type d'examen
- Terminologie médicale standard
- Modèles de formulation
- Valeurs normales pour les mesures

## 🔧 Configuration avancée

### Variables d'environnement

```env
# API du LLM
REACT_APP_LLM_API_URL=http://localhost:5000/api/llm
REACT_APP_LLM_API_KEY=votre_cle_api

# Base de connaissances RAG (optionnel)
REACT_APP_RAG_API_URL=http://localhost:5001/api/rag
REACT_APP_RAG_API_KEY=votre_cle_rag

# Langue de reconnaissance vocale
REACT_APP_SPEECH_LANG=fr-FR
```

### Personnalisation des templates

Modifiez `src/services/ragService.js` pour :
- Ajouter de nouveaux types d'examens
- Personnaliser les champs obligatoires
- Enrichir la terminologie médicale
- Adapter les modèles de formulation

## 📱 Compatibilité

- **Navigateurs** : Chrome 90+, Edge 90+, Safari 14+
- **Systèmes** : Windows, macOS, Linux
- **Mobile** : Support tactile et reconnaissance vocale mobile

## 🛡️ Sécurité et confidentialité

- Les données restent locales par défaut
- Possibilité de déployer votre propre LLM
- Pas de stockage cloud sans configuration explicite
- Chiffrement des communications API

## � Roadmap

- [ ] Support multi-langues
- [ ] Mode hors-ligne avec LLM embarqué
- [ ] Intégration PACS/RIS
- [ ] Templates personnalisables par spécialité
- [ ] Apprentissage des préférences utilisateur

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

Développé avec ❤️ pour simplifier le travail des professionnels de santé
