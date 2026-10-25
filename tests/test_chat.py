"""Tests du chat : salons, historique et WebSocket."""

import os
import sys

# La base de test est isolée de la base de développement avant tout import.
os.environ["DATABASE_URL"] = "sqlite:///./test_salon.db"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Recrée des tables vides avant chaque test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_and_list_rooms():
    response = client.post("/rooms", json={"name": "general", "description": "Le salon principal"})
    assert response.status_code == 201
    assert response.json()["name"] == "general"

    listing = client.get("/rooms")
    assert listing.status_code == 200
    assert [room["name"] for room in listing.json()] == ["general"]


def test_duplicate_room_is_rejected():
    client.post("/rooms", json={"name": "sport"})
    response = client.post("/rooms", json={"name": "sport"})
    assert response.status_code == 400


def test_unknown_room_messages_returns_404():
    assert client.get("/rooms/inconnu/messages").status_code == 404


def test_post_message_then_history():
    client.post("/rooms", json={"name": "films"})
    posted = client.post(
        "/rooms/films/messages", json={"username": "reda", "content": "Bonjour à tous"}
    )
    assert posted.status_code == 201

    history = client.get("/rooms/films/messages")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["content"] == "Bonjour à tous"


def test_empty_message_is_rejected():
    client.post("/rooms", json={"name": "musique"})
    response = client.post(
        "/rooms/musique/messages", json={"username": "reda", "content": ""}
    )
    assert response.status_code == 422


def test_websocket_broadcast_and_history():
    client.post("/rooms", json={"name": "general"})
    with client.websocket_connect("/ws/general") as first:
        with client.websocket_connect("/ws/general") as second:
            first.send_json({"username": "reda", "content": "Salut tout le monde"})
            # Les deux membres du salon reçoivent le message.
            assert first.receive_json()["content"] == "Salut tout le monde"
            assert second.receive_json()["content"] == "Salut tout le monde"

    # Le message est bien conservé dans l'historique.
    history = client.get("/rooms/general/messages")
    assert len(history.json()) == 1
    assert history.json()[0]["username"] == "reda"


def test_websocket_rooms_are_isolated():
    client.post("/rooms", json={"name": "sport"})
    client.post("/rooms", json={"name": "cuisine"})
    with client.websocket_connect("/ws/sport") as sport_client:
        with client.websocket_connect("/ws/cuisine"):
            sport_client.send_json({"username": "reda", "content": "Allez Paris"})
            assert sport_client.receive_json()["content"] == "Allez Paris"

    assert len(client.get("/rooms/sport/messages").json()) == 1
    assert client.get("/rooms/cuisine/messages").json() == []


def test_homepage_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "SalonDiscussion" in response.text
