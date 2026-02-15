#!/bin/bash

# Vocalis - Script de lancement rapide

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Vocalis - Script de Lancement Rapide               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier les prérequis
check_prerequisites() {
    echo "📋 Vérification des prérequis..."
    
    # Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 non trouvé${NC}"
        echo "  Installez Python 3.11+ depuis https://www.python.org"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 trouvé$(python3 --version)${NC}"
    
    # Flutter
    if ! command -v flutter &> /dev/null; then
        echo -e "${RED}✗ Flutter non trouvé${NC}"
        echo "  Installez Flutter depuis https://flutter.dev/docs/get-started/install"
        exit 1
    fi
    echo -e "${GREEN}✓ Flutter trouvé$(flutter --version | head -1)${NC}"
    
    # Modèle TinyLlama
    if [ ! -f "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
        echo -e "${YELLOW}⚠ Modèle TinyLlama non trouvé${NC}"
        echo "  Télécharger depuis: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
        read -p "  Continuer sans modèle? (backend sera en erreur) [y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        SIZE=$(du -h "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" | cut -f1)
        echo -e "${GREEN}✓ Modèle trouvé ($SIZE)${NC}"
    fi
    
    echo ""
}

# Lancer le backend
launch_backend() {
    echo "🚀 Lancement du backend..."
    echo "   Port: http://localhost:8080"
    echo ""
    
    cd backend
    
    # Créer venv si nécessaire
    if [ ! -d "venv" ]; then
        echo "📦 Création de l'environnement virtuel..."
        python3 -m venv venv
    fi
    
    # Activer venv
    source venv/bin/activate
    
    # Installer dépendances
    echo "📦 Installation des dépendances..."
    pip install -q -r requirements.txt
    
    # Lancer le serveur
    echo -e "${GREEN}▶ Serveur démarrage...${NC}"
    echo ""
    python main.py &
    BACKEND_PID=$!
    
    # Attendre que le serveur démarre
    sleep 3
    
    # Vérifier la santé
    if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend prêt (PID: $BACKEND_PID)${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Backend n'a pas démarré correctement${NC}"
        exit 1
    fi
    
    cd ..
}

# Lancer le frontend
launch_frontend() {
    echo "🎨 Lancement du frontend..."
    echo ""
    
    cd frontend
    
    # Obtenir les dépendances
    echo "📦 Obtention des dépendances Flutter..."
    flutter pub get -q
    
    # Lancer l'app
    echo -e "${GREEN}▶ Application démarre...${NC}"
    echo ""
    flutter run -d chrome
    
    cd ..
}

# Menu principal
show_menu() {
    echo ""
    echo "Que voulez-vous faire?"
    echo "1) Lancer backend + frontend (complet)"
    echo "2) Lancer backend uniquement"
    echo "3) Lancer frontend uniquement"
    echo "4) Vérifier les prérequis"
    echo "5) Lancer les tests"
    echo "6) Quitter"
    echo ""
    read -p "Choisissez (1-6): " choice
    
    case $choice in
        1)
            check_prerequisites
            launch_backend
            launch_frontend
            ;;
        2)
            check_prerequisites
            launch_backend
            wait
            ;;
        3)
            launch_frontend
            ;;
        4)
            check_prerequisites
            echo -e "${GREEN}✓ Tous les prérequis sont OK${NC}"
            ;;
        5)
            echo "🧪 Lancement des tests..."
            cd backend
            source venv/bin/activate 2>/dev/null || true
            pytest test_main.py test_advanced.py -v
            cd ..
            ;;
        6)
            echo "Au revoir!"
            exit 0
            ;;
        *)
            echo "Choix invalide"
            show_menu
            ;;
    esac
}

# Exécuter
show_menu
