#!/bin/bash

echo "🧪 Test d'inscription d'un utilisateur"
echo "======================================="
echo ""

curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "password": "MotDePasseSecurise123!",
    "telephone": "+237123456789"
  }' | python3 -m json.tool

echo ""
echo "✅ Test terminé"
