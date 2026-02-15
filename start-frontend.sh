#!/bin/bash

# Vocalis - Start Frontend Only

echo "Starting Vocalis Frontend..."
echo ""

cd frontend

echo "[1/2] Getting dependencies..."
flutter pub get -q

echo "[2/2] Running application..."
echo ""
flutter run -d chrome
