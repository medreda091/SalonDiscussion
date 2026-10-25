"""Schémas d'entrée et de sortie de l'API."""

from datetime import datetime

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Données nécessaires pour créer un salon."""

    name: str = Field(min_length=2, max_length=50)
    description: str = ""


class RoomOut(BaseModel):
    """Un salon tel qu'il est renvoyé par l'API."""

    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Un message envoyé via l'API REST (en plus du WebSocket)."""

    username: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=1000)


class MessageOut(BaseModel):
    """Un message tel qu'il est renvoyé par l'API."""

    id: int
    room_id: int
    username: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
