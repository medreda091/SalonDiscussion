# SalonDiscussion

Chat en temps réel multi-salons, construit avec **FastAPI** et les **WebSockets**.
Chaque salon garde l'historique de ses messages, et chaque message envoyé en
direct est diffusé instantanément à tous les membres connectés au salon.

## Fonctionnalités

- Création et liste des salons de discussion via l'API REST
- Chat en temps réel par WebSocket, un salon = une conversation isolée
- Historique des messages sauvegardé en base de données
- Création automatique d'un salon quand on s'y connecte pour la première fois
- Petite interface web incluse (page d'accueil) pour tester le chat
- Envoi de messages aussi possible via l'API REST

## Stack

- Python 3.12, FastAPI, WebSockets
- SQLAlchemy (SQLite par défaut, PostgreSQL possible via `DATABASE_URL`)
- Uvicorn, pytest, Docker

## Installation

```bash
git clone https://github.com/medreda091/SalonDiscussion.git
cd SalonDiscussion
pip install -r requirements.txt
uvicorn app.main:app --reload
```

L'application est ensuite disponible sur http://localhost:8000, et la
documentation interactive de l'API sur http://localhost:8000/docs.

## Utilisation

Créer un salon :

```bash
curl -X POST http://localhost:8000/rooms \
  -H "Content-Type: application/json" \
  -d '{"name": "general", "description": "Le salon principal"}'
```

Lister les salons :

```bash
curl http://localhost:8000/rooms
```

Lire l'historique d'un salon :

```bash
curl http://localhost:8000/rooms/general/messages
```

Se connecter en WebSocket (par exemple avec un client WebSocket) sur
`ws://localhost:8000/ws/general`, puis envoyer :

```json
{"username": "reda", "content": "Salut tout le monde"}
```

Tous les membres du salon reçoivent le message en direct, et il est
sauvegardé dans l'historique.

## Avec Docker

```bash
docker compose up --build
```

## Structure du projet

```
SalonDiscussion/
├── app/
│   ├── main.py                  # API REST + WebSocket + page d'accueil
│   ├── models.py                # Salons et messages
│   ├── schemas.py               # Validation des données
│   ├── database.py              # Connexion à la base
│   ├── connection_manager.py    # Diffusion WebSocket par salon
│   └── static/index.html        # Petite interface web du chat
├── tests/
│   └── test_chat.py             # Tests salons, historique et WebSocket
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Tests

```bash
python -m pytest -q
```

## Licence

MIT — voir le fichier `LICENSE`.
