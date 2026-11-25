"""Servidor FastAPI para el widget de chat FAQ embebible y captura de leads."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import db, knowledge

load_dotenv()

RAIZ = Path(__file__).resolve().parent.parent
STATIC = RAIZ / "static"

app = FastAPI(title="FAQ Web Bot")

origins_raw = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in origins_raw.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

db.inicializar()


class PreguntaReq(BaseModel):
    session_id: str = Field(default="anon", min_length=1, max_length=64)
    pregunta: str = Field(min_length=1, max_length=1000)


class LeadReq(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    contacto: str = Field(min_length=5, max_length=120)
    consulta: str = Field(default="", max_length=1000)
    origen: str = Field(default="", max_length=200)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def demo():
    return FileResponse(STATIC / "index.html")


@app.get("/widget.js")
def widget_js():
    return FileResponse(STATIC / "widget.js", media_type="application/javascript")


@app.post("/chat")
def chat(req: PreguntaReq):
    res = knowledge.responder(req.pregunta.strip())
    db.registrar_mensaje(req.session_id, req.pregunta.strip(), res["respuesta"], res["fuente"])
    return res


@app.post("/lead")
def crear_lead(req: LeadReq):
    lead_id = db.guardar_lead(req.nombre, req.contacto, req.consulta, req.origen)
    return {"ok": True, "id": lead_id}


@app.get("/leads")
def listar_leads(authorization: str | None = Header(default=None)):
    expected = os.environ.get("ADMIN_TOKEN", "")
    if not expected or not authorization or not secrets.compare_digest(authorization, f"Bearer {expected}"):
        raise HTTPException(401, "No autorizado")
    return db.listar_leads()
