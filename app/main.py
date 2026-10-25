"""Application SalonDiscussion : chat en temps réel multi-salons.

- API REST pour créer et lister les salons, et lire l'historique des messages.
- WebSocket pour envoyer et recevoir les messages en direct.
- Chaque message reçu en WebSocket est sauvegardé en base puis diffusé
  à tous les membres du salon.
"""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import models
from .connection_manager import manager
from .database import Base, engine, get_db
from .schemas import MessageCreate, MessageOut, RoomCreate, RoomOut

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SalonDiscussion",
    description="Chat en temps réel multi-salons avec historique des messages.",
    version="1.0.0",
)


@app.get("/", include_in_schema=False)
def home():
    """Sert la petite interface web du chat."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.post("/rooms", response_model=RoomOut, status_code=201)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    """Crée un nouveau salon (le nom doit être unique)."""
    existing = db.query(models.Room).filter(models.Room.name == room.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce salon existe déjà")
    new_room = models.Room(name=room.name, description=room.description)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


@app.get("/rooms", response_model=list[RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    """Liste tous les salons, par ordre de création."""
    return db.query(models.Room).order_by(models.Room.id).all()


@app.get("/rooms/{room_name}/messages", response_model=list[MessageOut])
def list_messages(room_name: str, limit: int = 50, db: Session = Depends(get_db)):
    """Renvoie les derniers messages d'un salon (les plus récents en dernier)."""
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    messages = (
        db.query(models.Message)
        .filter(models.Message.room_id == room.id)
        .order_by(models.Message.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


@app.post("/rooms/{room_name}/messages", response_model=MessageOut, status_code=201)
def post_message(room_name: str, message: MessageCreate, db: Session = Depends(get_db)):
    """Enregistre un message via l'API REST (sans diffusion WebSocket)."""
    room = db.query(models.Room).filter(models.Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    new_message = models.Message(
        room_id=room.id, username=message.username, content=message.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


@app.websocket("/ws/{room_name}")
async def websocket_chat(websocket: WebSocket, room_name: str):
    """Connexion temps réel à un salon : réception, sauvegarde, diffusion."""
    # La session est ouverte à part ici car le WebSocket est asynchrone.
    from .database import SessionLocal

    db = SessionLocal()
    try:
        room = db.query(models.Room).filter(models.Room.name == room_name).first()
        if not room:
            # Le salon est créé à la volée pour ne pas bloquer un nouvel arrivant.
            room = models.Room(name=room_name, description="")
            db.add(room)
            db.commit()
            db.refresh(room)
        await manager.connect(websocket, room_name)
        try:
            while True:
                data = await websocket.receive_json()
                username = str(data.get("username", "anonyme")).strip() or "anonyme"
                content = str(data.get("content", "")).strip()
                if not content:
                    continue
                saved = models.Message(
                    room_id=room.id, username=username, content=content
                )
                db.add(saved)
                db.commit()
                db.refresh(saved)
                await manager.broadcast(
                    {
                        "username": saved.username,
                        "content": saved.content,
                        "created_at": saved.created_at.isoformat(),
                    },
                    room_name,
                )
        except WebSocketDisconnect:
            manager.disconnect(websocket, room_name)
    finally:
        db.close()
