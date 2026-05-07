# Guide de Déploiement AgroPredict Backend (Docker)

Ce guide explique comment déployer l'API AgroPredict sur votre VPS Contabo en utilisant Docker.

## 1. Préparer le code sur GitHub

Puisque nous avons ajouté des fichiers (`Dockerfile`, `docker-compose.yml`, `.dockerignore`), vous devez d'abord les envoyer sur votre dépôt GitHub.

Depuis votre machine locale :
```bash
git add Dockerfile docker-compose.yml .dockerignore DEPLOYMENT.md .github/workflows/deploy.yml
git commit -m "Add Docker deployment and CI/CD workflow"
git push origin main
```

## 2. Configurer les Secrets GitHub

Pour que l'automatisation fonctionne, vous devez ajouter les secrets suivants dans votre dépôt GitHub (**Settings > Secrets and variables > Actions**) :

| Secret | Valeur |
|--------|--------|
| `VPS_IP` | `109.199.105.251` |
| `VPS_USERNAME` | `root` |
| `VPS_SSH_KEY` | Le contenu de votre clé privée (souvent dans `~/.ssh/id_ed25519`) |

> [!IMPORTANT]
> Assurez-vous que la clé publique correspondante est bien présente dans le fichier `/root/.ssh/authorized_keys` sur le VPS.

## 3. Récupérer le code sur le VPS

Connectez-vous à votre VPS :
```bash
ssh root@109.199.105.251
```

Si le projet n'est pas encore sur le VPS :
```bash
git clone https://github.com/Prog-Web-4GI-ENSPY/IOT_SOIL_BACKEND.git
cd IOT_SOIL_BACKEND
```

S'il est déjà là, récupérez les mises à jour :
```bash
cd IOT_SOIL_BACKEND
git pull origin main
```

## 4. Configuration sur le VPS

Connectez-vous à votre VPS :
```bash
ssh root@109.199.105.251
cd /root/IOT_SOIL_BACKEND
```

### Créer le fichier .env
Copiez le fichier d'exemple et modifiez-le avec vos valeurs de production :
```bash
cp .env.example .env
nano .env
```

**Paramètres importants à modifier dans `.env` :**
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `SECRET_KEY` (générez une clé sécurisée)
- `DATABASE_URL` (doit être : `postgresql://user:password@db:5432/db_name`)
- `CHIRPSTACK_API_TOKEN`, etc.

## 5. Lancement avec Docker

Lancez les conteneurs en arrière-plan :
```bash
docker compose up -d --build
```

### Vérifier les logs
```bash
docker compose logs -f api
```

## 6. Initialisation de la Base de Données

Une fois les conteneurs lancés, appliquez les migrations et créez l'utilisateur admin.

### Appliquer les migrations Alembic
```bash
docker compose exec api alembic upgrade head
```

### Créer l'utilisateur Admin
```bash
docker compose exec api python scripts/init_db.py
```

## 7. Configuration Nginx (Reverse Proxy)

Comme Nginx est déjà installé, vous devez ajouter une configuration pour rediriger le trafic vers le port 8000.

Créez un nouveau fichier de configuration :
```bash
nano /etc/nginx/sites-available/agropredict
```

Ajoutez le contenu suivant (remplacez `votre_domaine.com` si vous en avez un, sinon utilisez l'IP) :

```nginx
server {
    listen 80;
    server_name 109.199.105.251; # Ou votre_domaine.com

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activez le site et redémarrez Nginx :
```bash
ln -s /etc/nginx/sites-available/agropredict /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## 8. Vérification

L'API devrait maintenant être accessible sur :
- Documentation Swagger : `http://109.199.105.251/docs`
- Santé de l'API : `http://109.199.105.251/api/v1/health` (si l'endpoint existe)
