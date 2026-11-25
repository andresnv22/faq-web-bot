"""Pruebas del widget FAQ web, motor de conocimiento y captura de leads."""

import pytest
from fastapi.testclient import TestClient

from app import db, main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "faq_test.db")
    db.inicializar()
    return TestClient(main.app)


def test_saludo_y_faq_precios_sin_api_key(client, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    r_saludo = client.post("/chat", json={"session_id": "s1", "pregunta": "Hola!"})
    assert r_saludo.status_code == 200
    assert r_saludo.json()["fuente"] == "saludo"
    assert r_saludo.json()["sugerir_lead"] is False

    r_precio = client.post("/chat", json={"session_id": "s1", "pregunta": "¿Cuál es el precio y tarifa?"})
    assert r_precio.status_code == 200
    assert "$120 USD" in r_precio.json()["respuesta"]
    assert r_precio.json()["fuente"] == "faq:precios"


def test_pregunta_desconocida_sugiere_lead(client, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    r = client.post("/chat", json={"session_id": "s2", "pregunta": "¿Hacen integración con SAP R/3?"})
    assert r.status_code == 200
    data = r.json()
    assert data["fuente"] == "fallback"
    assert data["sugerir_lead"] is True


def test_guardar_y_proteger_leads(client, monkeypatch):
    r_post = client.post("/lead", json={
        "nombre": "Carlos Pérez",
        "contacto": "+573001234567",
        "consulta": "Cotizar bot web",
        "origen": "https://cliente.com",
    })
    assert r_post.status_code == 200
    assert r_post.json()["ok"] is True

    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    r_list = client.get("/leads")
    assert r_list.status_code == 401

    monkeypatch.setenv("ADMIN_TOKEN", "secreto")
    assert client.get("/leads").status_code == 401
    authorized = client.get("/leads", headers={"Authorization": "Bearer secreto"})
    assert authorized.status_code == 200
    assert len(authorized.json()) == 1
    assert authorized.json()[0]["nombre"] == "Carlos Pérez"


def test_widget_js_y_demo_html(client):
    assert client.get("/health").json() == {"ok": True}
    assert client.get("/").status_code == 200
    w = client.get("/widget.js")
    assert w.status_code == 200
    assert "textContent" in w.text
