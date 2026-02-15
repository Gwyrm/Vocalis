# Vocalis - Commandes Courantes

Référence rapide des commandes pour développer et lancer Vocalis.

## 🚀 Lancement Rapide

### Lancement Complet (Backend + Frontend)

```bash
# Terminal 1: Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Terminal 2: Frontend
cd frontend
flutter run -d chrome
```

### Lancement Interactif

```bash
./LAUNCH.sh
```

## 🔧 Backend

### Setup Initial

```bash
cd backend
python3 -m venv venv
source venv/bin/activate           # macOS/Linux
# venv\Scripts\activate            # Windows

pip install -r requirements.txt
```

### Lancer le Serveur

```bash
cd backend
source venv/bin/activate
python main.py

# Avec rechargement automatique (défaut)
# Accessible sur http://localhost:8080
```

### Tester le Backend

```bash
cd backend
source venv/bin/activate

# Tous les tests
pytest test_main.py test_advanced.py -v

# Tests spécifiques
pytest test_main.py -v
pytest test_advanced.py -v
pytest test_main.py::TestPrescriptionDataModel -v

# Avec couverture
pip install pytest-cov
pytest --cov=main --cov-report=html
```

### Vérifier la Santé du Backend

```bash
# Health check
curl http://localhost:8080/api/health

# Chat test
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour"}'
```

### Réinstaller les Dépendances

```bash
cd backend
pip install --upgrade -r requirements.txt
```

## 🎨 Frontend

### Setup Initial

```bash
cd frontend
flutter pub get
```

### Lancer l'Application

```bash
cd frontend

# Web (Chrome)
flutter run -d chrome

# Web (Firefox)
flutter run -d firefox

# Android
flutter run -d android-emulator

# iOS
flutter run -d ios

# macOS
flutter run -d macos

# Linux
flutter run -d linux

# Windows
flutter run -d windows
```

### Build Production

```bash
cd frontend

# Web pour production (avec API personnalisée)
flutter build web \
  --dart-define=API_URL=https://api.example.com:8080 \
  --release

# Résultat dans: build/web/
```

### Lancer les Tests Flutter

```bash
cd frontend
flutter test
```

### Nettoyer et Reconstruire

```bash
cd frontend
flutter clean
flutter pub get
flutter run -d chrome
```

## 🧪 Tests

### Tous les Tests

```bash
cd backend
pytest test_main.py test_advanced.py -v
```

### Tests Spécifiques

```bash
# Tests de modèles
pytest test_main.py::TestPrescriptionDataModel -v

# Tests d'endpoints
pytest test_main.py::TestCollectPrescriptionInfoEndpoint -v
pytest test_main.py::TestGeneratePrescriptionEndpoint -v

# Tests avancés
pytest test_advanced.py::TestIntegrationFlow -v
pytest test_advanced.py::TestDataValidation -v
```

### Couverture de Code

```bash
cd backend
pip install pytest-cov
pytest --cov=main --cov-report=html

# Voir la couverture
open htmlcov/index.html  # macOS
# ou: start htmlcov\index.html  # Windows
```

## 🧠 Modèle LLM

### Télécharger le Modèle

```bash
cd backend/models

# Avec wget
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# Ou avec curl
curl -L -o tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Avec Ollama (Alternative)

```bash
# Installer Ollama depuis https://ollama.ai

# Télécharger le modèle
ollama pull tinyllama

# Le modèle est maintenant disponible localement
```

## 📦 Gestion des Dépendances

### Backend

```bash
# Ajouter une nouvelle dépendance
cd backend
pip install <package-name>
pip freeze > requirements.txt

# Mettre à jour une dépendance
pip install --upgrade <package-name>

# Vérifier les dépendances installées
pip list
```

### Frontend

```bash
# Ajouter une nouvelle dépendance
cd frontend
flutter pub add <package-name>

# Mettre à jour les dépendances
flutter pub upgrade

# Vérifier les dépendances
flutter pub outdated
```

## 🔍 Debugging

### Backend Logs

```bash
# Voir les logs en détail
cd backend
PYTHONUNBUFFERED=1 python main.py

# Voir les logs avec timestamps
python main.py 2>&1 | tee backend.log
```

### Frontend Logs

```bash
cd frontend

# Mode verbose
flutter run -d chrome -v

# Voir les logs de l'app
flutter logs
```

### Tester une Requête API

```bash
# Health check
curl http://localhost:8080/api/health | jq .

# Chat
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour"}' | jq .

# Collecter des infos
curl -X POST http://localhost:8080/api/collect-prescription-info \
  -H "Content-Type: application/json" \
  -d '{
    "currentData": {},
    "userInput": "Patient: Jean, 45 ans"
  }' | jq .
```

## 🧹 Nettoyage

### Backend

```bash
cd backend

# Supprimer l'environnement virtuel
rm -rf venv

# Supprimer les fichiers compilés
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Réinitialiser complètement
rm -rf venv __pycache__ *.pyc .pytest_cache
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend

# Nettoyer
flutter clean

# Réinitialiser complètement
flutter clean
rm -rf pubspec.lock
flutter pub get
```

## 🚀 Production

### Backend

```bash
# Build production
pip install gunicorn

# Lancer avec Gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 main:app

# Avec fichier de configuration
gunicorn -c gunicorn_config.py main:app
```

### Frontend

```bash
# Build web production
flutter build web --release

# Déployer sur un serveur
scp -r build/web/* user@server:/var/www/vocalis/

# Ou sur Vercel, Netlify, etc.
# netlify deploy --prod --dir=build/web
```

## 📋 Checklist de Développement

- [ ] Python 3.11+ installé
- [ ] Flutter SDK installé
- [ ] Modèle TinyLlama téléchargé (~2GB)
- [ ] Backend dépendances installées
- [ ] Frontend dépendances installées
- [ ] Backend lance sans erreurs
- [ ] Frontend peut se connecter au backend
- [ ] Tests passent 100%
- [ ] Application fonctionne end-to-end

## 💾 Git

### Commits Courants

```bash
# Voir le statut
git status

# Voir les différences
git diff

# Ajouter des fichiers
git add .
git add backend/
git add frontend/

# Faire un commit
git commit -m "feat: description courte"

# Voir les logs
git log --oneline -10

# Pousser vers remote
git push origin main
```

## 🆘 Troubleshooting

### Le backend ne démarre pas

```bash
# Vérifier le modèle
ls -lh backend/models/tinyllama*.gguf

# Réinstaller les dépendances
cd backend
pip install --upgrade -r requirements.txt

# Relancer avec logs détaillés
PYTHONUNBUFFERED=1 python main.py
```

### Le frontend ne peut pas se connecter au backend

```bash
# Vérifier que le backend tourne
curl http://localhost:8080/api/health

# Vérifier les ports
lsof -i :8080      # Backend
lsof -i :53781     # Frontend web (port variable)

# Vérifier la configuration
cat frontend/lib/api_service.dart | grep baseUrl
```

### Flutter build échoue

```bash
cd frontend
flutter clean
flutter pub get
flutter run -d chrome -v
```

## 📚 Documentation

- **QUICKSTART.md** - Guide complet de lancement
- **CLAUDE.md** - Architecture et décisions
- **backend/TEST_REPORT.md** - Résultats des tests
- **backend/API_TEST_EXAMPLES.md** - Exemples API

---

Generated: 2026-02-15
