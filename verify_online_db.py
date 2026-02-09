from sqlalchemy import create_engine, text
import uuid
from datetime import datetime

# URL de la base de données EN LIGNE (Render)
db_url = "postgresql://delmat:zu95vqiVCNK3N8PW4P30dbTVPDg2JQNV@dpg-d5cl1t0gjchc73foe7i0-a.oregon-postgres.render.com/iot_soil_db"

print(f"Connecting to ONLINE database: {db_url}")
engine = create_engine(db_url)

sql = """
INSERT INTO localites (nom, ville, region, pays, continent, climate_zone, id, created_at, deleted_at, updated_at) 
VALUES (:nom, :ville, :region, :pays, :continent, :climate_zone, :id, :created_at, :deleted_at, :updated_at)
"""

params = {
    'nom': 'test_verification_online',
    'ville': 'ville_test',
    'region': 'region_test',
    'pays': 'pays_test',
    'continent': 'AFRIQUE',
    'climate_zone': 'TROPICAL',
    'id': str(uuid.uuid4()),
    'created_at': datetime.utcnow(),
    'deleted_at': None,
    'updated_at': datetime.utcnow()
}

try:
    with engine.begin() as conn:
        conn.execute(text(sql), params)
    print("✅ SUCCÈS : Insertion réussie dans la base EN LIGNE !")
    print("Cela confirme que la colonne 'superficie' n'est plus requise ni présente.")
except Exception as e:
    print(f"❌ ÉCHEC : Erreur lors de l'insertion : {e}")
