"""Base de datos SQLite para leads e historial básico del widget FAQ."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "faq_bot.db"


def conectar(db_path: str | Path | None = None) -> sqlite3.Connection:
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar(db_path: str | Path | None = None) -> None:
    with conectar(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT NOT NULL,
                consulta TEXT NOT NULL,
                origen TEXT NOT NULL DEFAULT '',
                creado_en REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                pregunta TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                fuente TEXT NOT NULL,
                creado_en REAL NOT NULL
            );
            """
        )


def guardar_lead(nombre: str, contacto: str, consulta: str, origen: str = "", db_path: str | Path | None = None) -> int:
    with conectar(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO leads (nombre, contacto, consulta, origen, creado_en) VALUES (?, ?, ?, ?, ?)",
            (nombre.strip(), contacto.strip(), consulta.strip(), origen.strip(), time.time()),
        )
        return int(cur.lastrowid)


def listar_leads(db_path: str | Path | None = None) -> list[dict]:
    with conectar(db_path) as conn:
        filas = conn.execute(
            "SELECT id, nombre, contacto, consulta, origen, creado_en FROM leads ORDER BY creado_en DESC"
        ).fetchall()
    return [dict(f) for f in filas]


def registrar_mensaje(session_id: str, pregunta: str, respuesta: str, fuente: str, db_path: str | Path | None = None) -> None:
    with conectar(db_path) as conn:
        conn.execute(
            "INSERT INTO mensajes (session_id, pregunta, respuesta, fuente, creado_en) VALUES (?, ?, ?, ?, ?)",
            (session_id, pregunta, respuesta, fuente, time.time()),
        )
