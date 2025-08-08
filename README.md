# Infomaniak DDNS Updater (Python + Docker)

Service léger qui met automatiquement à jour votre enregistrement DNS Infomaniak avec votre IP publique actuelle. Fonctionne en continu, supporte IPv4 et (optionnel) IPv6.

## Fonctionnalités
- Récupération périodique de l’IP publique (IPv4 / IPv6)
- Comparaison avec l’IP DNS existante et mise à jour uniquement si nécessaire
- Intervalle configurable et protection anti-spam API
- Exécutable en conteneur (Docker / Portainer) ou en Python natif

## Image Docker officielle (GHCR)
L’image est construite et publiée automatiquement via GitHub Actions.
- Registry: `ghcr.io/laxe4k/ddns-infomaniak`
- Tags:
  - `latest` (publie sur tag Git)
  - `dev` (sur branches `dev/*`)
  - `x.y.z` (correspondant aux tags Git)

Aucune construction locale n’est requise: il suffit de récupérer l’image et de configurer les variables d’environnement.

## Variables d’environnement
- `INFOMANIAK_DDNS_HOSTNAME` (obligatoire) — Nom d’hôte complet à mettre à jour (ex: `sub.domaine.tld`)
- `INFOMANIAK_DDNS_USERNAME` (obligatoire) — Identifiant/compte Infomaniak (ou token si applicable)
- `INFOMANIAK_DDNS_PASSWORD` (obligatoire) — Mot de passe/token
- `DDNS_INTERVAL_SECONDS` (optionnel, défaut: `300`) — Intervalle entre deux vérifications (min 15s)
- `DDNS_ENABLE_IPV6` (optionnel, défaut: `false`) — Activer la gestion IPv6 (`true`/`false`)

Astuce Portainer: vous pouvez définir des variables intermédiaires (ex: `INFOMANIAK_DDNS_HOSTNAME_ENV`) et les référencer dans `docker-compose.yml` via `${…}`.

## Démarrage rapide (Docker Compose / Portainer)
Exemple minimal (valeurs en dur):

```yaml
services:
  ddns:
    image: ghcr.io/laxe4k/ddns-infomaniak:latest
    container_name: ddns-infomaniak
    restart: unless-stopped
    environment:
      - INFOMANIAK_DDNS_HOSTNAME=example.domain.tld
      - INFOMANIAK_DDNS_USERNAME=mon-user
      - INFOMANIAK_DDNS_PASSWORD=mon-mot-de-passe-ou-token
      - DDNS_INTERVAL_SECONDS=300
      - DDNS_ENABLE_IPV6=false
```

Exemple avec variables Portainer/Compose (références `${…}`), comme dans ce dépôt:

```yaml
version: "3.9"
services:
  ddns:
    image: ghcr.io/laxe4k/ddns-infomaniak:latest
    container_name: ddns-infomaniak
    restart: unless-stopped
    environment:
      - INFOMANIAK_DDNS_HOSTNAME=${INFOMANIAK_DDNS_HOSTNAME_ENV}
      - INFOMANIAK_DDNS_USERNAME=${INFOMANIAK_DDNS_USERNAME_ENV}
      - INFOMANIAK_DDNS_PASSWORD=${INFOMANIAK_DDNS_PASSWORD_ENV}
      - DDNS_INTERVAL_SECONDS=300
      - DDNS_ENABLE_IPV6=false
```

- Dans Portainer (Stacks): collez le Compose, définissez les variables `${…}` dans la section dédiée puis déployez.
- Suivre les logs: `docker logs -f ddns-infomaniak`

## Démarrage rapide (Docker CLI)
- Récupérer l’image: `docker pull ghcr.io/laxe4k/ddns-infomaniak:latest`
- Lancer:

```bash
docker run -d --name ddns-infomaniak --restart unless-stopped \
  -e INFOMANIAK_DDNS_HOSTNAME=example.domain.tld \
  -e INFOMANIAK_DDNS_USERNAME=mon-user \
  -e INFOMANIAK_DDNS_PASSWORD=mon-mot-de-passe-ou-token \
  -e DDNS_INTERVAL_SECONDS=300 \
  -e DDNS_ENABLE_IPV6=false \
  ghcr.io/laxe4k/ddns-infomaniak:latest
```

## Exécution locale (facultatif, sans Docker)
1) Prérequis: Python 3.13+ et `pip`
2) Installation: `pip install -r requirements.txt`
3) Exportez les variables d’environnement (voir plus haut)
4) Lancer: `python main.py`

## Détails de fonctionnement
- Boucle continue avec intervalle configurable (min. 15s)
- Validation IPv6 (si activée) via le module `ipaddress`
- User-Agent dédié, gestion basique des réponses Infomaniak (`good`, `nochg`, `badauth`, etc.)

## Sécurité
- Ne versionnez pas votre fichier `.env` (contient des secrets). Utilisez Portainer (variables) ou un coffre.
- Si des identifiants ont été exposés publiquement, changez-les immédiatement depuis votre compte Infomaniak.

## Structure du projet
- `main.py` — Point d’entrée, démarre le service en boucle
- `models/ddns_client.py` — Client OOP Infomaniak DDNS (logique métier)
- `docker-compose.yml` — Déploiement Docker/Portainer
- `Dockerfile` — Image Docker
- `requirements.txt` — Dépendances Python
- `LICENSE`, `README.md`

## Licence
MIT — voir `LICENSE`.