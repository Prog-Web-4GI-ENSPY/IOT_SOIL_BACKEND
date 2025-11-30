#!/bin/bash

# Script pour exécuter les tests de l'API d'authentification

echo "========================================="
echo "Tests de l'API d'authentification"
echo "========================================="
echo ""

# Vérifier si pytest est installé
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest n'est pas installé. Installation..."
    pip install pytest pytest-asyncio httpx
fi

# Fonction pour afficher l'aide
show_help() {
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all            Exécuter tous les tests (défaut)"
    echo "  security       Tests des utilitaires de sécurité"
    echo "  service        Tests du service utilisateur"
    echo "  auth           Tests des endpoints d'authentification"
    echo "  users          Tests des endpoints utilisateur"
    echo "  coverage       Exécuter avec rapport de couverture"
    echo "  help           Afficher cette aide"
    echo ""
}

# Traiter les arguments
case "${1:-all}" in
    all)
        echo "▶ Exécution de tous les tests..."
        pytest -v
        ;;
    security)
        echo "▶ Exécution des tests de sécurité..."
        pytest tests/test_security.py -v
        ;;
    service)
        echo "▶ Exécution des tests du service utilisateur..."
        pytest tests/test_user_service.py -v
        ;;
    auth)
        echo "▶ Exécution des tests des endpoints d'authentification..."
        pytest tests/test_auth_endpoints.py -v
        ;;
    users)
        echo "▶ Exécution des tests des endpoints utilisateur..."
        pytest tests/test_user_endpoints.py -v
        ;;
    coverage)
        echo "▶ Exécution avec rapport de couverture..."
        if ! command -v pytest-cov &> /dev/null; then
            echo "❌ pytest-cov n'est pas installé. Installation..."
            pip install pytest-cov
        fi
        pytest --cov=app --cov-report=html --cov-report=term
        echo ""
        echo "✅ Rapport de couverture généré dans htmlcov/index.html"
        ;;
    help)
        show_help
        ;;
    *)
        echo "❌ Option invalide: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Tests terminés avec succès"
else
    echo "❌ Des tests ont échoué"
fi

exit $exit_code
