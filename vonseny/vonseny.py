#!/usr/bin/env python3
"""
VONSENY — Very Optimized Neural System for Engineering & National York
========================================================================
Yerel LLM (Ollama) tabanlı, çok modüllü yapay zeka asistanı.

Özellikler:
  • Yerel LLM (Ollama / llama3.2 / mistral / phi3)
  • Sesli sohbet (Whisper STT + pyttsx3 TTS)
  • Kamera & nesne/tehlike tespiti (OpenCV + YOLOv8)
  • IoT cihaz kontrolü (MQTT + Seri Port)
  • Laptop/PC kontrolü (subprocess + pyautogui)
  • CAD otomasyon (FreeCAD / SolidWorks)
  • Web araştırma (DuckDuckGo + Wikipedia)
  • Askeri bilgi tabanı
  • Konuşma belleği (JSON)

Kurulum:
  pip install -r requirements.txt
  ollama pull llama3.2  (veya: ollama pull mistral)
  ollama serve

Çalıştırma:
  python vonseny.py
  python vonseny.py --voice        # Sesli mod
  python vonseny.py --camera       # Kameralı mod
  python vonseny.py --model phi3   # Model seçimi
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import re
from pathlib import Path

# Proje kökünü Python yoluna ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Loglama ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="[%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("VONSENY")

# ── Rich ───────────────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    RICH = True
except ImportError:
    RICH = False

console = Console() if RICH else None


def vprint(msg: str, style: str = "bold cyan") -> None:
    if RICH:
        console.print(f"[{style}]VONSENY ►[/{style}] {msg}")
    else:
        print(f"VONSENY ► {msg}")


def vmarkdown(text: str) -> None:
    if RICH:
        console.print(Markdown(text))
    else:
        print(text)


def get_input(prompt: str = "Siz") -> str:
    if RICH:
        return Prompt.ask(f"[bold yellow]{prompt}[/bold yellow]")
    return input(f"{prompt}: ")


def show_banner() -> None:
    banner = r"""
 __   ______  _   _ _____ _____   _  ___   __
 \ \ / / __ \| \ | / ____|  ___| | \| \ \ / /
  \ V / |  | |  \| | (___ | |__   |  \| |\ V /
   > <| |  | | . ` |\___ \|  __|  | . ` | > <
  / . | |__| | |\  |____) | |___  | |\  |/ . \
 /_/ \_\____/|_| \_|_____/|_____| |_| \_/_/ \_\

   Very Optimized Neural System for Engineering & National York
   ── Yerel AI · Askeri Zeka · Tam Kontrol ──
    """
    if RICH:
        console.print(Panel(Text(banner, style="bold blue"), border_style="cyan"))
    else:
        print(banner)


# ── Modül Yükleyici ────────────────────────────────────────────────────────────
def load_modules(args):
    modules = {}

    # Brain (zorunlu)
    from vonseny.core.brain import Brain
    modules["brain"] = Brain(model=args.model)
    modules["brain"].load_history()
    vprint(f"Beyin aktif — Model: {args.model}", "bold green")

    # Askeri bilgi tabanı (zorunlu, offline)
    from vonseny.core.military import MilitaryKnowledge
    modules["military"] = MilitaryKnowledge()
    vprint("Askeri bilgi tabanı yüklendi.", "green")

    # Ses (isteğe bağlı)
    if args.voice:
        from vonseny.core.voice import VoiceEngine
        voice = VoiceEngine(whisper_model=args.whisper_model)
        modules["voice"] = voice
        vprint("Ses motoru aktif (Whisper + TTS).", "green")

    # Kamera (isteğe bağlı)
    if args.camera:
        from vonseny.core.vision import VisionEngine
        vision = VisionEngine(camera_index=args.camera_index, use_yolo=not args.no_yolo)
        modules["vision"] = vision
        # Tehlike uyarısı callback'i
        def _threat_cb(threats):
            names = [t.class_name for t in threats]
            assessment = modules["military"].threat_assessment(names)
            msg = (
                f"⚠️  TEHDİT TESPİT EDİLDİ! "
                f"{assessment['threat_status']} | "
                f"Nesneler: {', '.join(names)} | "
                f"{assessment['recommendation']}"
            )
            vprint(msg, "bold red")
            if "voice" in modules:
                modules["voice"].speak(msg)

        vision.on_threat(_threat_cb)
        vision.start_stream(show_window=args.show_camera)
        vprint("Kamera sistemi aktif.", "green")

    # IoT (isteğe bağlı)
    if args.iot:
        from vonseny.core.iot import IoTManager
        iot = IoTManager()
        iot.connect_mqtt(broker=args.mqtt_broker, port=args.mqtt_port)
        modules["iot"] = iot
        vprint(f"IoT yöneticisi aktif — MQTT: {args.mqtt_broker}:{args.mqtt_port}", "green")

    # Web (her zaman mevcut, online olunca çalışır)
    from vonseny.core.web import search_web, wikipedia_summary, find_best_value_phone, deep_research
    modules["web"] = {
        "search": search_web,
        "wiki": wikipedia_summary,
        "best_phone": find_best_value_phone,
        "research": deep_research,
    }
    vprint("Web araştırma motoru hazır.", "green")

    # Bilgisayar kontrolü
    from vonseny.core.computer import (
        get_system_info, open_application, close_application,
        run_command, InputController, FileManager, CADController
    )
    modules["computer"] = {
        "system_info": get_system_info,
        "open": open_application,
        "close": close_application,
        "run": run_command,
        "input": InputController(),
        "files": FileManager(),
        "cad_ctrl": CADController(),
    }
    vprint("Bilgisayar kontrol modülü hazır.", "green")

    # CAD
    from vonseny.core.cad import CADEngine
    modules["cad"] = CADEngine()
    vprint("CAD motoru hazır.", "green")

    return modules


# ── Yerleşik Komutlar ──────────────────────────────────────────────────────────
BUILTIN_HELP = """
╔══════════════════════════════════════════════════════════════════╗
║                   VONSENY KOMUT REHBERİ                        ║
╠══════════════════════════════════════════════════════════════════╣
║  sistem bilgisi          CPU, RAM, disk durumu                  ║
║  ekran görüntüsü         Ekranı kaydet                         ║
║  uygulama aç <isim>      Program başlat                         ║
║  uygulama kapat <isim>   Program sonlandır                      ║
║  komut çalıştır <cmd>    Kabuk komutu                           ║
║  kamera aç               Görüntü akışı başlat                   ║
║  snapshot al             Anlık kamera görüntüsü                 ║
║  iot listesi             Bağlı IoT cihazları                    ║
║  iot kontrol <id> <cmd>  IoT cihaza komut                       ║
║  ara <sorgu>             Web araması                            ║
║  wikipedia <konu>        Wikipedia özeti                        ║
║  telefon araştır [bütçe] Fiyat-performans telefon               ║
║  araştır <konu>          Derin web araştırması                  ║
║  model listesi           Ollama modelleri                       ║
║  model değiştir <isim>   Farklı model seç                       ║
║  askeri terim <terim>    Askeri terim açıkla                    ║
║  taktik <senaryo>        Taktik bilgisi                         ║
║  silah <isim>            Silah sistemi bilgisi                  ║
║  tehdit değerlendir      Manuel tehdit analizi                  ║
║  cad kutu L G Y          FreeCAD kutu parça oluştur             ║
║  cad silindir R Y        FreeCAD silindir oluştur               ║
║  belleği temizle         Konuşma geçmişini sil                  ║
║  belleği kaydet          Geçmişi JSON'a yaz                     ║
║  yardım                  Bu menü                                ║
║  çıkış / exit            VONSENY kapat                          ║
╚══════════════════════════════════════════════════════════════════╝
"""


def handle_builtin(text: str, modules: dict) -> str | None:
    """
    Yerleşik komutları işle. Tanımazsa None döndür.
    '__EXIT__' döndürürse program kapanır.
    """
    t = text.lower().strip()

    # ── Çıkış ───────────────────────────────────────────────────────────────
    if t in ("çıkış", "exit", "quit", "kapat", "güle güle", "bye"):
        return "__EXIT__"

    # ── Yardım ──────────────────────────────────────────────────────────────
    if t in ("yardım", "help", "komutlar", "ne yapabilirsin"):
        return BUILTIN_HELP

    # ── Sistem Bilgisi ────────────────────────────────────────────────────────
    if "sistem bilgisi" in t or "bilgisayar durumu" in t:
        info = modules["computer"]["system_info"]()
        lines = [f"  {k}: {v}" for k, v in info.items()]
        return "🖥️  Sistem Durumu:\n" + "\n".join(lines)

    # ── Ekran Görüntüsü ───────────────────────────────────────────────────────
    if "ekran görüntüsü" in t or "screenshot" in t:
        ok = modules["computer"]["input"].screenshot("vonseny_screen.png")
        return "📸 Ekran görüntüsü alındı: vonseny_screen.png" if ok else "⚠️  Screenshot alınamadı."

    # ── Uygulama Kontrolü ────────────────────────────────────────────────────
    if t.startswith("uygulama aç "):
        app = text[len("uygulama aç "):].strip()
        ok = modules["computer"]["open"](app)
        return f"✅ '{app}' açıldı." if ok else f"⚠️  '{app}' açılamadı."

    if t.startswith("uygulama kapat "):
        app = text[len("uygulama kapat "):].strip()
        ok = modules["computer"]["close"](app)
        return f"✅ '{app}' kapatıldı." if ok else f"⚠️  '{app}' kapatılamadı."

    # ── Kabuk Komutu ─────────────────────────────────────────────────────────
    if t.startswith("komut çalıştır "):
        cmd = text[len("komut çalıştır "):].strip()
        stdout, stderr, rc = modules["computer"]["run"](cmd)
        out = stdout or stderr
        return f"$ {cmd}\n{out[:1000]}" if out else f"Komut çalıştı (kod: {rc})"

    # ── Kamera ───────────────────────────────────────────────────────────────
    if "kamera aç" in t or "kamerayı aç" in t:
        if "vision" in modules:
            return "✅ Kamera zaten aktif."
        from vonseny.core.vision import VisionEngine
        vision = VisionEngine()
        modules["vision"] = vision
        vision.start_stream(show_window=True)
        return "📷 Kamera başlatıldı. 'q' tuşu ile kapatabilirsiniz."

    if "snapshot" in t or "anlık görüntü" in t:
        if "vision" in modules:
            ok = modules["vision"].capture_snapshot("vonseny_snapshot.jpg")
            return "📷 Snapshot kaydedildi." if ok else "⚠️  Snapshot alınamadı."
        return "⚠️  Kamera aktif değil. Önce 'kamera aç' komutunu verin."

    # ── IoT ──────────────────────────────────────────────────────────────────
    if "iot listesi" in t or "cihazları listele" in t:
        if "iot" in modules:
            return str(modules["iot"].list_devices())
        return "⚠️  IoT modülü aktif değil (--iot argümanıyla başlatın)."

    m = re.match(r"iot kontrol (\S+) (\S+)(?:\s+(.+))?", t)
    if m:
        device_id, cmd, value = m.groups()
        if "iot" in modules:
            ok = modules["iot"].control_device(device_id, cmd, value)
            return f"✅ Cihaz '{device_id}' → {cmd}={value}" if ok else "⚠️  Gönderilemedi."
        return "⚠️  IoT modülü aktif değil."

    # ── Web Araması ───────────────────────────────────────────────────────────
    if t.startswith("ara "):
        query = text[4:].strip()
        results = modules["web"]["search"](query, max_results=5)
        if not results:
            return "⚠️  Sonuç bulunamadı."
        lines = [f"\n{i}. **{r.title}**\n   {r.snippet[:180]}\n   🔗 {r.url}"
                 for i, r in enumerate(results, 1)]
        return f"🔍 '{query}' arama sonuçları:\n" + "\n".join(lines)

    if t.startswith("wikipedia "):
        topic = text[10:].strip()
        summary = modules["web"]["wiki"](topic)
        return f"📖 **{topic}**\n\n{summary}"

    if "telefon araştır" in t or "fiyat performans telefon" in t:
        budget = None
        m = re.search(r"(\d+)\s*(?:tl|lira)", t)
        if m:
            budget = int(m.group(1))
        result = modules["web"]["best_phone"](budget)
        return result

    if t.startswith("araştır "):
        topic = text[8:].strip()
        vprint(f"Araştırılıyor: {topic} …", "yellow")
        result = modules["web"]["research"](topic)
        return result

    # ── Model Yönetimi ────────────────────────────────────────────────────────
    if "model listesi" in t:
        from vonseny.core.brain import Brain
        models = Brain.list_models()
        return "🧠 Mevcut Ollama modelleri:\n" + "\n".join(f"  • {m}" for m in models)

    if t.startswith("model değiştir "):
        model = text[len("model değiştir "):].strip()
        modules["brain"].set_model(model)
        return f"✅ Model değiştirildi: {model}"

    # ── Askeri Bilgi ──────────────────────────────────────────────────────────
    if t.startswith("askeri terim "):
        term = text[len("askeri terim "):].strip()
        return modules["military"].get_term(term)

    if t.startswith("taktik "):
        scenario = text[7:].strip()
        return modules["military"].get_tactic(scenario)

    if t.startswith("silah "):
        weapon = text[6:].strip()
        info = modules["military"].get_weapon_info(weapon)
        if info:
            lines = [f"  {k}: {v}" for k, v in info.items()]
            return f"🔫 **{weapon}**\n" + "\n".join(lines)
        return f"⚠️  '{weapon}' bulunamadı."

    if "tehdit değerlendir" in t:
        nesneler_str = input("Tespit edilen nesneleri virgülle girin: ")
        nesneler = [x.strip() for x in nesneler_str.split(",")]
        result = modules["military"].threat_assessment(nesneler)
        return (
            f"🎯 Tehdit Değerlendirmesi:\n"
            f"  Seviye : {result['threat_level']} — {result['threat_status']}\n"
            f"  Tehditler: {', '.join(result['threats']) or 'Yok'}\n"
            f"  Öneri  : {result['recommendation']}"
        )

    # ── CAD ───────────────────────────────────────────────────────────────────
    m = re.match(r"cad kutu\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", t)
    if m:
        l, g, y = float(m.group(1)), float(m.group(2)), float(m.group(3))
        vprint(f"FreeCAD kutu oluşturuluyor: {l}×{g}×{y} mm …", "yellow")
        path = modules["cad"].create_box(l, g, y)
        return f"✅ Kutu parça oluşturuldu: {path}" if path else "⚠️  FreeCAD kurulu değil."

    m = re.match(r"cad silindir\s+([\d.]+)\s+([\d.]+)", t)
    if m:
        r_val, h_val = float(m.group(1)), float(m.group(2))
        vprint(f"FreeCAD silindir: R={r_val} H={h_val} …", "yellow")
        path = modules["cad"].create_cylinder(r_val, h_val)
        return f"✅ Silindir oluşturuldu: {path}" if path else "⚠️  FreeCAD kurulu değil."

    # ── Bellek ────────────────────────────────────────────────────────────────
    if "belleği temizle" in t:
        modules["brain"].clear_history()
        return "🧹 Konuşma geçmişi temizlendi."

    if "belleği kaydet" in t:
        modules["brain"].save_history()
        return "💾 Konuşma geçmişi kaydedildi: vonseny_memory.json"

    return None  # bilinmeyen komut → LLM'e yönlendir


# ── Ana Program ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="VONSENY AI Sistemi")
    parser.add_argument("--model", default="llama3.2", help="Ollama modeli (varsayılan: llama3.2)")
    parser.add_argument("--voice", action="store_true", help="Sesli mod")
    parser.add_argument("--whisper-model", default="base", dest="whisper_model")
    parser.add_argument("--camera", action="store_true", help="Kamera modu")
    parser.add_argument("--camera-index", type=int, default=0, dest="camera_index")
    parser.add_argument("--show-camera", action="store_true", dest="show_camera")
    parser.add_argument("--no-yolo", action="store_true", dest="no_yolo")
    parser.add_argument("--iot", action="store_true", help="IoT modülünü etkinleştir")
    parser.add_argument("--mqtt-broker", default="localhost", dest="mqtt_broker")
    parser.add_argument("--mqtt-port", type=int, default=1883, dest="mqtt_port")
    args = parser.parse_args()

    show_banner()
    vprint("Modüller yükleniyor …", "yellow")
    modules = load_modules(args)
    vprint("VONSENY hazır. 'yardım' yazarak başlayın.\n", "bold green")

    # Ses modu: sürekli dinleme
    if "voice" in modules:
        def _voice_cb(text: str) -> None:
            vprint(f"(Ses) {text}", "bold yellow")
            _process_input(text, modules, args)
        modules["voice"].start_listening(duration=5.0)

    while True:
        try:
            if "voice" in modules and args.voice:
                user_text = get_input("Siz (metin veya boş bırakın)")
                if not user_text.strip():
                    vprint("Dinleniyor …", "dim")
                    user_text = modules["voice"].listen_once(duration=5.0)
                    if not user_text.strip():
                        continue
                    vprint(f"Duyulan: {user_text}", "italic yellow")
            else:
                user_text = get_input()
        except (KeyboardInterrupt, EOFError):
            vprint("Göreve devam. Sistemler hazır beklemede. 👋", "bold cyan")
            modules["brain"].save_history()
            break

        if not user_text.strip():
            continue

        _process_input(user_text, modules, args)


def _process_input(text: str, modules: dict, args) -> None:
    """Girişi işle, yanıt ver ve gerekirse sesli oku."""
    # Yerleşik komut mu?
    response = handle_builtin(text, modules)
    if response == "__EXIT__":
        vprint("Göreve devam. Sistemler hazır beklemede. 👋", "bold cyan")
        modules["brain"].save_history()
        sys.exit(0)

    if response is None:
        # LLM'e sor — akışlı yanıt
        if RICH:
            console.print("[bold cyan]VONSENY ►[/bold cyan] ", end="")
        else:
            print("VONSENY ► ", end="", flush=True)
        full_response = ""
        for token in modules["brain"].ask_stream(text):
            print(token, end="", flush=True)
            full_response += token
        print()
        response = full_response
    else:
        vmarkdown(response)

    # Sesli çıktı
    if "voice" in modules and response and response not in (BUILTIN_HELP,):
        clean = re.sub(r"[#*`►╔╗╚╝║╠═]", "", response)
        modules["voice"].speak(clean[:300])


if __name__ == "__main__":
    main()
