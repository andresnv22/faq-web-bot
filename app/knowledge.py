"""Motor de respuestas FAQ: búsqueda local por relevancia + LLM opcional."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

import httpx

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "knowledge.json"
RE_PALABRA = re.compile(r"[a-z0-9]{2,}")

SALUDOS = {"hola", "buenas", "buenos", "dias", "tardes", "noches", "hey", "hi"}


def _plano(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


def _tokens(texto: str) -> set[str]:
    return set(RE_PALABRA.findall(_plano(texto)))


def cargar_base(path: str | Path | None = None) -> dict:
    p = Path(path) if path else KNOWLEDGE_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def buscar_faqs(pregunta: str, base: dict, top_k: int = 2) -> list[dict]:
    toks = _tokens(pregunta)
    if not toks:
        return []
    resultados = []
    for item in base.get("faqs", []):
        claves = set()
        for p in item.get("preguntas", []):
            claves |= _tokens(p)
        claves |= _tokens(item.get("titulo", ""))
        coincidencias = len(toks & claves)
        if coincidencias > 0:
            resultados.append((coincidencias, item))
    resultados.sort(key=lambda x: -x[0])
    return [item for _, item in resultados[:top_k]]


def _llamar_llm(pregunta: str, contexto: list[dict], negocio: str) -> str | None:
    url = os.environ.get("LLM_API_URL", "").strip()
    key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    if not (url and key and model):
        return None
    contexto_txt = "\n".join(f"- {c['titulo']}: {c['respuesta']}" for c in contexto) or "Sin coincidencias directas."
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 220,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Eres el asistente de atención de {negocio}. Responde breve y amable en español "
                    "usando SOLO la información verificada del contexto. Si no está en el contexto, "
                    "invita al cliente a dejar su nombre y WhatsApp para asesoría personalizada."
                ),
            },
            {"role": "user", "content": f"Contexto:\n{contexto_txt}\n\nPregunta: {pregunta}"},
        ],
    }
    try:
        r = httpx.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=12)
        if r.status_code >= 400:
            return None
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def responder(pregunta: str, base: dict | None = None) -> dict:
    base = base or cargar_base()
    negocio = os.environ.get("BUSINESS_NAME", "").strip() or base.get("negocio", "el negocio")
    toks = _tokens(pregunta)

    if toks and toks.issubset(SALUDOS):
        return {
            "respuesta": base.get("saludo", f"¡Hola! Bienvenido a {negocio}. ¿En qué te ayudo?"),
            "fuente": "saludo",
            "sugerir_lead": False,
        }

    coincidencias = buscar_faqs(pregunta, base, top_k=2)
    llm_resp = _llamar_llm(pregunta, coincidencias, negocio)
    if llm_resp:
        return {"respuesta": llm_resp, "fuente": "llm", "sugerir_lead": not bool(coincidencias)}

    if coincidencias:
        principal = coincidencias[0]
        return {
            "respuesta": principal["respuesta"],
            "fuente": f"faq:{principal['id']}",
            "sugerir_lead": False,
        }

    return {
        "respuesta": (
            f"No tengo ese dato exacto en la guía de {negocio}, pero déjame tu nombre y WhatsApp "
            "en el formulario aquí abajo para que un asesor te responda en minutos."
        ),
        "fuente": "fallback",
        "sugerir_lead": True,
    }
