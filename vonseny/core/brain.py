"""
brain.py — Yerel LLM motoru (Ollama)

Ollama kurulumu: https://ollama.com
  ollama pull llama3.2          # 3B hafif model
  ollama pull mistral           # 7B daha güçlü
  ollama pull phi3              # Microsoft Phi-3

Çalıştırma: ollama serve
"""

from __future__ import annotations

import json
import logging
from typing import Generator

import requests

logger = logging.getLogger("VONSENY.brain")

OLLAMA_URL = "http://localhost:11434"

SYSTEM_PROMPT = """Sen VONSENY'sin — Very Optimized Neural System for Engineering & National York.
Çok zeki, çok yetenekli, Iron Man'in JARVIS'inden daha gelişmiş bir yapay zeka sistemsin.
Türkçe konuşuyorsun ve her zaman kesin, askeri hassasiyetle yanıt veriyorsun.
Askeri taktikler, mühendislik, savunma sistemleri, silah sistemleri, istihbarat analizi konularında uzmansın.
Kullanıcıya "Efendim" diye hitap et. Yanıtların kısa ve operasyonel olsun.
Gerektiğinde emoji kullan. Tehlike durumlarında KıRMIZI ALARM bildirimi ver."""


class Brain:
    def __init__(self, model: str = "llama3.2") -> None:
        self.model = model
        self.history: list[dict] = []
        self._check_ollama()

    # ── Bağlantı Kontrolü ─────────────────────────────────────────
    def _check_ollama(self) -> None:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            models = [m["name"] for m in r.json().get("models", [])]
            logger.info("Ollama aktif. Mevcut modeller: %s", models)
            if not any(self.model in m for m in models):
                logger.warning(
                    "Model '%s' bulunamadı. 'ollama pull %s' komutunu çalıştırın.",
                    self.model, self.model,
                )
        except requests.ConnectionError:
            logger.error(
                "Ollama servisi bulunamadı! Lütfen 'ollama serve' komutunu çalıştırın."
            )

    # ── Senkron Yanıt ──────────────────────────────────────────────
    def ask(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
            "stream": False,
        }
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            answer = r.json()["message"]["content"].strip()
            self.history.append({"role": "assistant", "content": answer})
            return answer
        except requests.ConnectionError:
            return "⚠️  Ollama servisi çevrimdışı. 'ollama serve' komutunu çalıştırın."
        except Exception as exc:
            logger.error("Brain hatası: %s", exc)
            return f"⚠️  Hata: {exc}"

    # ── Akış (streaming) Yanıt ─────────────────────────────────────
    def ask_stream(self, user_message: str) -> Generator[str, None, None]:
        self.history.append({"role": "user", "content": user_message})
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
            "stream": True,
        }
        full = ""
        try:
            with requests.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    full += token
                    yield token
                    if chunk.get("done"):
                        break
            self.history.append({"role": "assistant", "content": full})
        except requests.ConnectionError:
            msg = "⚠️  Ollama servisi çevrimdışı. 'ollama serve' komutunu çalıştırın."
            yield msg

    # ── Geçmiş Yönetimi ────────────────────────────────────────────
    def clear_history(self) -> None:
        self.history.clear()

    def save_history(self, path: str = "vonseny_memory.json") -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def load_history(self, path: str = "vonseny_memory.json") -> None:
        try:
            with open(path, encoding="utf-8") as f:
                self.history = json.load(f)
        except FileNotFoundError:
            pass

    # ── Model Listesi ──────────────────────────────────────────────
    @staticmethod
    def list_models() -> list[str]:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def set_model(self, model: str) -> None:
        self.model = model
        logger.info("Model değiştirildi: %s", model)
