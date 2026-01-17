import pytest
from fastapi.testclient import TestClient
from app.models.location import Localite, Continent, ClimateZone
from app.models.terrain import Terrain
from app.models.parcelle import Parcelle


@pytest.fixture
def test_localite(db):
    """Créer une localité de test"""
    localite = Localite(
        nom="Yaoundé",
        ville="Yaoundé",
        pays="Cameroun",
        continent=Continent.AFRIQUE,
        climate_zone=ClimateZone.TROPICAL
    )
    db.add(localite)
    db.commit()
    db.refresh(localite)
    return localite


@pytest.fixture
def test_terrain(db, test_user, test_localite):
    """Créer un terrain de test"""
    terrain = Terrain(
        nom="Terrain Test",
        description="Terrain pour les tests unitaires",
        localite_id=test_localite.id,
        user_id=test_user.id
    )
    db.add(terrain)
    db.commit()
    db.refresh(terrain)
    return terrain


@pytest.fixture
def test_parcelle(db, test_terrain):
    """Créer une parcelle de test"""
    parcelle = Parcelle(
        nom="Parcelle Test",
        code="TEST-001",
        terrain_id=test_terrain.id,
        superficie=2.5
    )
    db.add(parcelle)
    db.commit()
    db.refresh(parcelle)
    return parcelle


def test_create_capteur(client: TestClient, auth_headers, test_parcelle):
    """Test de création d'un capteur"""
    response = client.post(
        "/api/v1/capteurs",
        headers=auth_headers,
        json={
            "nom": "Capteur Humidité Sol 1",
            "code": "CAPT-001",
            "type_capteur": "humidite_sol",
            "modele": "SoilWatch Pro",
            "fabricant": "AgriTech",
            "dev_eui": "0123456789ABCDEF",
            "application_id": "app-001",
            "parcelle_id": test_parcelle.id,
            "latitude": 3.8505,
            "longitude": 11.5035,
            "profondeur_installation": 20,
            "date_installation": "2024-01-15T10:00:00",
            "interval_transmission": 15
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nom"] == "Capteur Humidité Sol 1"
    assert data["dev_eui"] == "0123456789ABCDEF"
    assert data["statut"] == "offline"


def test_create_capteur_duplicate_dev_eui(
    client: TestClient,
    auth_headers,
    test_parcelle,
    db
):
    """Test de création avec DevEUI existant"""
    from app.models.capteur import Capteur, TypeCapteur
    
    # Créer un capteur existant
    existing_capteur = Capteur(
        nom="Capteur Existant",
        code="EXIST-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(existing_capteur)
    db.commit()
    
    # Essayer de créer avec le même DevEUI
    response = client.post(
        "/api/v1/capteurs",
        headers=auth_headers,
        json={
            "nom": "Nouveau Capteur",
            "code": "NEW-001",
            "type_capteur": "temperature",
            "modele": "TempSensor",
            "dev_eui": "0123456789ABCDEF",  # Même DevEUI
            "application_id": "app-001",
            "parcelle_id": test_parcelle.id,
            "latitude": 3.8505,
            "longitude": 11.5035,
            "date_installation": "2024-01-15T10:00:00"
        }
    )
    
    assert response.status_code == 400
    assert "deveui" in response.json()["detail"].lower()


def test_get_capteurs(client: TestClient, auth_headers, test_parcelle, db):
    """Test de récupération de la liste des capteurs"""
    from app.models.capteur import Capteur, TypeCapteur, StatutCapteur
    
    # Créer plusieurs capteurs
    capteurs = [
        Capteur(
            nom=f"Capteur {i}",
            code=f"CAPT-00{i}",
            type_capteur=TypeCapteur.HUMIDITE_SOL,
            modele="Model X",
            dev_eui=f"000000000000000{i}",
            application_id="app-001",
            parcelle_id=test_parcelle.id,
            latitude=3.8505,
            longitude=11.5035,
            date_installation="2024-01-01T00:00:00",
            statut=StatutCapteur.ONLINE if i % 2 == 0 else StatutCapteur.OFFLINE
        )
        for i in range(1, 6)
    ]
    
    for capteur in capteurs:
        db.add(capteur)
    db.commit()
    
    # Récupérer tous les capteurs
    response = client.get(
        "/api/v1/capteurs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5


def test_get_capteurs_filter_by_status(
    client: TestClient,
    auth_headers,
    test_parcelle,
    db
):
    """Test de filtrage des capteurs par statut"""
    from app.models.capteur import Capteur, TypeCapteur, StatutCapteur
    
    # Créer capteurs online et offline
    capteurs = [
        Capteur(
            nom=f"Capteur {i}",
            code=f"CAPT-00{i}",
            type_capteur=TypeCapteur.HUMIDITE_SOL,
            modele="Model X",
            dev_eui=f"000000000000000{i}",
            application_id="app-001",
            parcelle_id=test_parcelle.id,
            latitude=3.8505,
            longitude=11.5035,
            date_installation="2024-01-01T00:00:00",
            statut=StatutCapteur.ONLINE if i <= 2 else StatutCapteur.OFFLINE
        )
        for i in range(1, 6)
    ]
    
    for capteur in capteurs:
        db.add(capteur)
    db.commit()
    
    # Filtrer par statut ONLINE
    response = client.get(
        "/api/v1/capteurs?statut=online",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert all(c["statut"] == "online" for c in data["data"])


def test_get_capteur_by_id(client: TestClient, auth_headers, test_parcelle, db):
    """Test de récupération d'un capteur par ID"""
    from app.models.capteur import Capteur, TypeCapteur
    
    capteur = Capteur(
        nom="Capteur Test",
        code="TEST-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(capteur)
    db.commit()
    db.refresh(capteur)
    
    response = client.get(
        f"/api/v1/capteurs/{capteur.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == capteur.id
    assert data["nom"] == "Capteur Test"


def test_update_capteur(client: TestClient, auth_headers, test_parcelle, db):
    """Test de mise à jour d'un capteur"""
    from app.models.capteur import Capteur, TypeCapteur
    
    capteur = Capteur(
        nom="Capteur Original",
        code="ORIG-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(capteur)
    db.commit()
    db.refresh(capteur)
    
    response = client.put(
        f"/api/v1/capteurs/{capteur.id}",
        headers=auth_headers,
        json={
            "nom": "Capteur Modifié",
            "description": "Description mise à jour"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "Capteur Modifié"
    assert data["description"] == "Description mise à jour"


def test_delete_capteur(client: TestClient, auth_headers, test_parcelle, db):
    """Test de suppression d'un capteur"""
    from app.models.capteur import Capteur, TypeCapteur
    
    capteur = Capteur(
        nom="Capteur à Supprimer",
        code="DEL-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(capteur)
    db.commit()
    db.refresh(capteur)
    
    response = client.delete(
        f"/api/v1/capteurs/{capteur.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Vérifier que le capteur est supprimé
    response = client.get(
        f"/api/v1/capteurs/{capteur.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_get_capteur_statistics(
    client: TestClient,
    auth_headers,
    test_parcelle,
    db
):
    """Test des statistiques des capteurs"""
    from app.models.capteur import Capteur, TypeCapteur, StatutCapteur
    
    # Créer capteurs avec différents statuts
    capteurs_data = [
        {"statut": StatutCapteur.ONLINE, "battery": 80},
        {"statut": StatutCapteur.ONLINE, "battery": 90},
        {"statut": StatutCapteur.OFFLINE, "battery": 50},
        {"statut": StatutCapteur.BATTERIE_FAIBLE, "battery": 15},
        {"statut": StatutCapteur.MAINTENANCE, "battery": 60},
    ]
    
    for i, data in enumerate(capteurs_data, 1):
        capteur = Capteur(
            nom=f"Capteur {i}",
            code=f"STAT-00{i}",
            type_capteur=TypeCapteur.MULTIFONCTION,
            modele="Model X",
            dev_eui=f"000000000000000{i}",
            application_id="app-001",
            parcelle_id=test_parcelle.id,
            latitude=3.8505,
            longitude=11.5035,
            date_installation="2024-01-01T00:00:00",
            statut=data["statut"],
            battery_level=data["battery"]
        )
        db.add(capteur)
    db.commit()
    
    response = client.get(
        "/api/v1/capteurs/statistics",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["online"] == 2
    assert data["offline"] == 1
    assert data["maintenance"] == 1
    assert data["low_battery"] == 1

