"""
voice.py — Ses tanıma (Whisper local) + Metin-to-Konuşma (pyttsx3 / edge-tts)

Kurulum:
  pip install openai-whisper sounddevice scipy pyttsx3
  # GPU için: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
"""

from __future__ import annotations

import logging
import queue
import threading
import tempfile
import os
from typing import Callable

logger = logging.getLogger("VONSENY.voice")

# ── Lazy imports ─────────────────────────────────────────────────────────────
def _import_whisper():
    try:
        import whisper
        return whisper
    except ImportError:
        logger.warning("whisper kurulu değil: pip install openai-whisper")
        return None

def _import_sounddevice():
    try:
        import sounddevice as sd
        return sd
    except ImportError:
        logger.warning("sounddevice kurulu değil: pip install sounddevice")
        return None

def _import_pyttsx3():
    try:
        import pyttsx3
        return pyttsx3
    except ImportError:
        logger.warning("pyttsx3 kurulu değil: pip install pyttsx3")
        return None

def _import_scipy():
    try:
        from scipy.io import wavfile
        import numpy as np
        return wavfile, np
    except ImportError:
        logger.warning("scipy kurulu değil: pip install scipy")
        return None, None


class VoiceEngine:
    """Ses tanıma ve konuşma motoru."""

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, whisper_model: str = "base", language: str = "tr") -> None:
        self.language = language
        self._whisper_model_name = whisper_model
        self._whisper = None
        self._tts_engine = None
        self._listening = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._callbacks: list[Callable[[str], None]] = []

    # ── TTS Kurulum ──────────────────────────────────────────────────────────
    def _get_tts(self):
        if self._tts_engine is None:
            pyttsx3 = _import_pyttsx3()
            if pyttsx3:
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty("rate", 175)
                self._tts_engine.setProperty("volume", 1.0)
                # Türkçe ses varsa seç
                voices = self._tts_engine.getProperty("voices")
                for v in voices:
                    if "tr" in v.id.lower() or "turkish" in v.name.lower():
                        self._tts_engine.setProperty("voice", v.id)
                        break
        return self._tts_engine

    def speak(self, text: str) -> None:
        """Metni sesli oku."""
        logger.info("TTS: %s", text[:80])
        tts = self._get_tts()
        if tts:
            try:
                tts.say(text)
                tts.runAndWait()
            except Exception as exc:
                logger.error("TTS hatası: %s", exc)
                print(f"[VONSENY]: {text}")
        else:
            # Fallback: sadece yazdır
            print(f"[VONSENY]: {text}")

    # ── Whisper Kurulum ───────────────────────────────────────────────────────
    def _get_whisper(self):
        if self._whisper is None:
            whisper = _import_whisper()
            if whisper:
                logger.info("Whisper modeli yükleniyor: %s", self._whisper_model_name)
                self._whisper = whisper.load_model(self._whisper_model_name)
        return self._whisper

    # ── Mikrofon Kaydı ────────────────────────────────────────────────────────
    def record(self, duration: float = 5.0) -> bytes | None:
        """Mikrofonden ses kaydet ve ham bytes döndür."""
        sd = _import_sounddevice()
        _, np = _import_scipy()
        if sd is None or np is None:
            return None
        try:
            logger.info("Kayıt başlıyor: %.1f saniye", duration)
            audio = sd.rec(
                int(duration * self.SAMPLE_RATE),
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16",
            )
            sd.wait()
            return audio.tobytes()
        except Exception as exc:
            logger.error("Kayıt hatası: %s", exc)
            return None

    def transcribe(self, audio_bytes: bytes) -> str:
        """Ses verisini metne çevir (Whisper local)."""
        whisper_model = self._get_whisper()
        if whisper_model is None:
            return ""
        wavfile, np = _import_scipy()
        if wavfile is None:
            return ""
        try:
            # Geçici WAV dosyası oluştur
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            wavfile.write(tmp_path, self.SAMPLE_RATE, audio_array)
            result = whisper_model.transcribe(tmp_path, language=self.language)
            os.unlink(tmp_path)
            text = result["text"].strip()
            logger.info("Transkript: %s", text)
            return text
        except Exception as exc:
            logger.error("Transkript hatası: %s", exc)
            return ""

    def listen_once(self, duration: float = 5.0) -> str:
        """Bir kez dinle ve metni döndür."""
        audio = self.record(duration)
        if audio:
            return self.transcribe(audio)
        return ""

    # ── Sürekli Dinleme ───────────────────────────────────────────────────────
    def on_speech(self, callback: Callable[[str], None]) -> None:
        """Ses algılandığında çağrılacak fonksiyon ekle."""
        self._callbacks.append(callback)

    def start_listening(self, duration: float = 5.0) -> None:
        """Arka planda sürekli dinleme başlat."""
        self._listening = True
        thread = threading.Thread(
            target=self._listen_loop, args=(duration,), daemon=True
        )
        thread.start()
        logger.info("Sürekli dinleme başlatıldı.")

    def stop_listening(self) -> None:
        self._listening = False

    def _listen_loop(self, duration: float) -> None:
        while self._listening:
            text = self.listen_once(duration)
            if text:
                for cb in self._callbacks:
                    try:
                        cb(text)
                    except Exception as exc:
                        logger.error("Callback hatası: %s", exc)
