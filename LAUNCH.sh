#!/bin/bash

# Vocalis - Script de lancement rapide
# Usage: ./LAUNCH.sh

set -e

echo ""
echo "=========================================="
echo "   Vocalis - Script de Lancement"
echo "=========================================="
echo ""

# Vérifier les prérequis
check_prerequisites() {
    echo "[1/3] Verification des prerequis..."
    echo ""

    # Python
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 non trouve"
        echo "Installez Python 3.11+ depuis https://www.python.org"
        exit 1
    fi
    echo "OK: Python 3 trouve"

    # Flutter
    if ! command -v flutter &> /dev/null; then
        echo "ERROR: Flutter non trouve"
        echo "Installez Flutter depuis https://flutter.dev"
        exit 1
    fi
    echo "OK: Flutter trouve"

    # Modèle TinyLlama
    if [ ! -f "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
        echo ""
        echo "WARNING: Modèle TinyLlama non trouve"
        echo "Télécharger depuis:"
        echo "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
        echo ""
        read -p "Continuer sans modèle? [y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "OK: Modèle TinyLlama trouve"
    fi

    echo ""
}

# Lancer le backend
launch_backend() {
    echo "[2/3] Lancement du backend..."
    echo ""

    cd backend

    # Créer venv si nécessaire
    if [ ! -d "venv" ]; then
        echo "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi

    # Installer dépendances
    echo "Installation des dépendances..."
    source venv/bin/activate
    pip install -q -r requirements.txt

    # Lancer le serveur
    echo "Démarrage du serveur..."
    echo ""
    python main.py &
    BACKEND_PID=$!

    # Attendre que le serveur démarre
    sleep 3

    # Vérifier la santé
    if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        echo ""
        echo "OK: Backend prêt (PID: $BACKEND_PID)"
        echo "    Accessible sur: http://localhost:8080"
        echo ""
        cd ..
        return 0
    else
        echo ""
        echo "ERROR: Backend n'a pas démarré"
        kill $BACKEND_PID 2>/dev/null || true
        cd ..
        exit 1
    fi
}

# Lancer le frontend
launch_frontend() {
    echo "[3/3] Lancement du frontend..."
    echo ""

    cd frontend

    # Obtenir les dépendances
    echo "Installation des dépendances Flutter..."
    flutter pub get -q

    echo ""
    echo "Démarrage de l'application..."
    echo "(L'application s'ouvrira dans Chrome)"
    echo ""

    # Lancer l'app
    flutter run -d chrome

    cd ..
}

# Menu principal
show_menu() {
    echo ""
    echo "Que voulez-vous faire?"
    echo ""
    echo "1) Lancer backend + frontend (complet)"
    echo "2) Lancer backend uniquement"
    echo "3) Lancer frontend uniquement"
    echo "4) Verifier les prerequis"
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
            echo ""
            echo "Backend lance! Pour arreter, appuyez sur Ctrl+C"
            echo ""
            wait
            ;;
        3)
            cd frontend
            flutter pub get -q
            echo "Lancement de l'application..."
            flutter run -d chrome
            cd ..
            ;;
        4)
            check_prerequisites
            echo "OK: Tous les prerequis sont satisfaits!"
            echo ""
            ;;
        5)
            echo "Lancement des tests..."
            echo ""
            cd backend
            if [ ! -d "venv" ]; then
                python3 -m venv venv
            fi
            source venv/bin/activate
            pip install -q -r requirements.txt
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
