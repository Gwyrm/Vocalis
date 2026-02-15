# Vocalis - Quick Start Guide

Guide pour lancer le projet Vocalis en développement et production.

## 📋 Prérequis

### Backend
- Python 3.11+
- pip (gestionnaire de paquets Python)
- Connexion internet (pour télécharger les dépendances)

### Frontend
- Flutter SDK 3.11+
- Dart 3.11+
- Un navigateur moderne (pour web) ou un émulateur/device (pour mobile)

### Modèle LLM
- TinyLlama 1.1B GGUF (~2GB téléchargé, ~1.5GB utilisé)
- Accès à Ollama (optionnel, voir section Ollama)

---

## 🚀 Lancement Rapide (Local)

### Étape 1: Lancer le Backend

```bash
# Naviguer vers le répertoire backend
cd backend

# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle TinyLlama (si pas déjà présent)
# Voir section "Télécharger le Modèle LLM" ci-dessous

# Lancer le serveur
python main.py
```

**Résultat attendu:**
```
INFO:vocalis-backend:Loading model from backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf...
INFO:vocalis-backend:Model loaded successfully!
INFO uvicorn.server - Application startup complete [production mode]
```

Le backend est maintenant accessible sur `http://localhost:8080`

### Étape 2: Lancer le Frontend (Web)

Dans un **nouveau terminal**:

```bash
# Naviguer vers le répertoire frontend
cd frontend

# Obtenir les dépendances Flutter
flutter pub get

# Lancer en mode web (pointant vers localhost:8080)
flutter run -d chrome
```

**Résultat attendu:**
- Une fenêtre Chrome s'ouvre automatiquement
- Application Vocalis accessible sur `http://localhost:53781` (port variable)

---

## 🎯 Accès à l'Application

Une fois le backend et frontend lancés:

1. **Ouvrir l'application** (URL affichée dans le terminal Flutter)
2. **Voir le message de bienvenue** "Bonjour! Pour rédiger une ordonnance..."
3. **Commencer à converser** pour collecter les informations du patient

### Workflow d'Utilisation

1. **Collecte d'informations** (chat)
   - Entrez les informations du patient
   - L'IA demande les champs manquants
   - Le bouton "✓" apparaît quand toutes les infos sont collectées

2. **Génération d'ordonnance**
   - Cliquez sur "✓" pour générer l'ordonnance
   - Passez à l'écran de révision

3. **Révision et édition**
   - Lisez l'ordonnance générée
   - Éditez si nécessaire
   - Cliquez "Proceed to Signature"

4. **Signature et PDF**
   - Signez sur le pad
   - Cliquez "Generate & Download PDF"
   - Le PDF est généré et téléchargé

---

## 📱 Lancer sur Différentes Plateformes

### Web (Chrome/Firefox/Safari)

```bash
cd frontend
flutter run -d chrome     # Chrome (recommandé)
flutter run -d firefox    # Firefox
# Pour Safari: ouvrir dans Xcode
```

### Android (Émulateur)

```bash
# Démarrer un émulateur Android depuis Android Studio
# Ou: emulator -avd <avd_name>

cd frontend
flutter run -d android-emulator
```

### iOS (Simulateur Mac)

```bash
# Démarrer le simulateur iOS
open /Applications/Xcode.app/Contents/Developer/Applications/Simulator.app

cd frontend
flutter run -d ios
```

### macOS/Linux/Windows (Desktop)

```bash
cd frontend

# macOS
flutter run -d macos

# Linux
flutter run -d linux

# Windows
flutter run -d windows
```

---

## 🐳 Lancer avec Docker (Optionnel)

### Backend avec Docker

```bash
# Construire l'image
docker build -t vocalis-backend ./backend

# Lancer le container
docker run -p 8080:8080 \
  -v $(pwd)/backend/models:/app/models \
  vocalis-backend
```

---

## 🧠 Télécharger le Modèle LLM

Le modèle TinyLlama est requis pour le fonctionnement du backend.

### Option 1: Téléchargement Manuel

```bash
cd backend/models

# Télécharger depuis Hugging Face
# Taille: ~2GB
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Ou avec curl
curl -L -o tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Option 2: Avec Ollama

Ollama simplifie le téléchargement et la gestion des modèles.

```bash
# Installer Ollama (https://ollama.ai)

# Télécharger le modèle
ollama pull tinyllama

# Le modèle est maintenant disponible via Ollama
# Voir: backend/ollama_setup.sh pour l'intégration
```

---

## 🔧 Configuration Avancée

### Variables d'Environnement Backend

```bash
# Chemin du modèle personnalisé
export MODEL_PATH=/chemin/vers/modele.gguf

# Timeout pour les réponses (secondes)
export OLLAMA_TIMEOUT=120

# Port du backend
export BACKEND_PORT=8080

# Lancer le backend
python main.py
```

### Configuration Frontend pour Production

Pour déployer le frontend en production:

```bash
# Build web pour production (example avec API externe)
flutter build web --dart-define=API_URL=https://api.example.com:8080 --release

# Résultat dans: frontend/build/web/
# Déployer les fichiers sur un serveur web (Nginx, Apache, etc.)
```

---

## 🧪 Tester les Endpoints

### Via curl

```bash
# Health check
curl http://localhost:8080/api/health

# Chat simple
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour"}'

# Collecter des infos
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {},
    "userInput": "Patient Jean Dupont, 45 ans"
  }'
```

Pour plus d'exemples: voir `backend/API_TEST_EXAMPLES.md`

### Via Tests Automatisés

```bash
cd backend

# Tous les tests
pytest test_main.py test_advanced.py -v

# Tests spécifiques
pytest test_main.py::TestPrescriptionDataModel -v
```

---

## 🐛 Dépannage

### Le modèle ne charge pas

**Symptôme:** `Failed to load model` au démarrage du backend

**Solutions:**
1. Vérifier que le fichier existe: `backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`
2. Vérifier les permissions: `ls -l backend/models/`
3. Augmenter le timeout dans le code ou via `OLLAMA_TIMEOUT`
4. Réessayer avec le modèle téléchargé via Ollama

### Frontend ne peut pas se connecter au backend

**Symptôme:** Erreur "Failed to connect" ou "Connection refused"

**Solutions:**
1. Vérifier que le backend tourne: `curl http://localhost:8080/api/health`
2. Vérifier les ports (backend: 8080, frontend: variable)
3. Vérifier la configuration API dans `frontend/lib/api_service.dart`
4. Sur web, vérifier les CORS du backend (déjà configurés)

### Flutter build échoue

**Solutions:**
```bash
# Nettoyer et reconstruire
flutter clean
flutter pub get
flutter run -d chrome

# Ou en mode debug verbose
flutter run -d chrome -v
```

### Erreur "Module 'llama_cpp' not found"

```bash
# Réinstaller les dépendances
cd backend
pip install --upgrade -r requirements.txt
```

---

## 📊 Architecture du Système

```
┌─────────────────────────────────────────────────────┐
│            Vocalis Application                      │
├──────────────────────┬──────────────────────────────┤
│   Frontend (Flutter) │   Backend (FastAPI)          │
│                      │                              │
│ • Web (Chrome)       │ • REST API                   │
│ • iOS/Android        │ • TinyLlama LLM              │
│ • macOS/Linux        │ • PDF Generation             │
│ • Windows            │ • Data Validation            │
│                      │                              │
│   Ports:             │   Port: 8080                 │
│   • Web: ~53781      │   • http://localhost:8080    │
│   • Mobile: Device   │                              │
└──────────────────────┴──────────────────────────────┘

Communication: HTTP REST (JSON)
CORS: Enabled for all origins
Authentication: None (local/trusted network)
```

---

## 📈 Performance

### Temps de Démarrage

| Composant | Temps |
|-----------|-------|
| Backend (sans modèle) | ~2s |
| Chargement modèle TinyLlama | ~30-60s (1ère fois) |
| Frontend (web) | ~5-10s |
| **Total (1ère fois)** | **~1-2 minutes** |

### Temps de Réponse (Avec Modèle Chargé)

| Action | Temps |
|--------|-------|
| Chat simple | ~2-5s |
| Collecte info | ~2-5s |
| Génération ordonnance | ~3-8s |
| Génération PDF | ~1-2s |

---

## 🔐 Sécurité en Développement

⚠️ **Important pour le développement local uniquement:**

- CORS: Accepte toutes les origines
- Authentication: Aucune (supposant un réseau de confiance)
- API: HTTP sans TLS
- Modèle: Chargé en mémoire

**Pour la production:**
- Ajouter l'authentification (JWT, OAuth, etc.)
- Utiliser HTTPS/TLS
- Configurer CORS approprié
- Ajouter rate limiting
- Valider toutes les entrées

---

## 📚 Documentation Supplémentaire

- **CLAUDE.md** - Décisions d'architecture et configuration
- **backend/TEST_REPORT.md** - Résultats des tests
- **backend/API_TEST_EXAMPLES.md** - Exemples API curl
- **frontend/README.md** - Instructions Flutter

---

## 🚀 Déploiement en Production

### Backend

```bash
# Build production
pip install gunicorn

# Lancer avec Gunicorn (production-ready)
gunicorn -w 4 -b 0.0.0.0:8080 main:app
```

### Frontend

```bash
# Build web production
flutter build web --dart-define=API_URL=https://api.example.com:8080 --release

# Déployer sur Vercel, Netlify, or AWS S3 + CloudFront
# Copier le contenu de build/web/ vers votre serveur
```

---

## ✅ Checklist de Lancement

- [ ] Python 3.11+ installé
- [ ] Flutter SDK installé
- [ ] Modèle TinyLlama téléchargé (2GB)
- [ ] Dépendances backend installées (`pip install -r requirements.txt`)
- [ ] Dépendances frontend installées (`flutter pub get`)
- [ ] Backend lancé (`python main.py`)
- [ ] Frontend lancé (`flutter run -d chrome`)
- [ ] Application accessible et fonctionnelle
- [ ] Tests passent (`pytest test_main.py test_advanced.py -v`)

---

## 💡 Tips & Tricks

### Accélérer le développement

```bash
# Frontend: Hot reload automatique
flutter run -d chrome --fast-start

# Backend: Auto-reload avec watchdog
pip install watchdog
python main.py  # Déjà configuré avec reload=True
```

### Déboguer les requêtes API

```bash
# Voir les requêtes HTTP détaillées
curl -v http://localhost:8080/api/health

# Ou dans le code frontend:
# Activer les logs dans ApiService
```

### Réinitialiser tout

```bash
# Backend
cd backend
rm -rf venv __pycache__ *.pyc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
flutter clean
flutter pub get
```

---

**Besoin d'aide?** Consultez les fichiers de documentation ou réexécutez les tests.

**Status**: ✅ Prêt à lancer!

---

Generated: 2026-02-15
