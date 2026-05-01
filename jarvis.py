#!/usr/bin/env python3
"""
JARVIS - Just A Rather Very Intelligent System
Türkçe destekli yapay zeka asistanı
"""

import os
import sys
import datetime
import random
import platform

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ──────────────────────────────────────────────
# Konsol kurulumu
# ──────────────────────────────────────────────
console = Console() if RICH_AVAILABLE else None

def jarvis_print(message: str, style: str = "bold cyan") -> None:
    if RICH_AVAILABLE:
        console.print(f"[{style}]JARVIS:[/{style}] {message}")
    else:
        print(f"JARVIS: {message}")

def user_input(prompt: str = "Siz") -> str:
    if RICH_AVAILABLE:
        return Prompt.ask(f"[bold yellow]{prompt}[/bold yellow]")
    return input(f"{prompt}: ")

def show_banner() -> None:
    banner = """
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    Just A Rather Very Intelligent System
    """
    if RICH_AVAILABLE:
        console.print(Panel(Text(banner, style="bold blue"), border_style="cyan"))
    else:
        print(banner)

# ──────────────────────────────────────────────
# Yerleşik komutlar (API gerektirmez)
# ──────────────────────────────────────────────
SAAT_KOMUTLARI   = ("saat kaç", "saat nedir", "şu an saat")
TARIH_KOMUTLARI  = ("bugün ne", "tarih nedir", "bugün tarih", "hangi gün")
SISTEM_KOMUTLARI = ("sistem bilgisi", "bilgisayar bilgisi", "hangi işletim sistemi")
MIZAH_KOMUTLARI  = ("şaka yap", "espri yap", "beni güldür", "komik bir şey söyle")
SELAMLAMA_KOMUTLARI = ("merhaba", "selam", "hey", "nasılsın")
CIKIS_KOMUTLARI  = ("çıkış", "kapat", "güle güle", "bye", "exit", "quit")

SAKALAR = [
    "Neden programcılar gözlük takar? Çünkü C# göremezler. 😄",
    "Bir yapay zeka bara girmiş. Barmen sormuş: 'Ne içersin?' AI: 'Veri.' 🤖",
    "Bilgisayarın en sevdiği yiyecek nedir? Çip! 🍟",
    "Neden bilgisayarlar hiç yorulmaz? Çünkü her gece uyurlar — sleep() komutuyla. 💤",
    "Python programcısı neden üzgündü? Çünkü hayatında çok fazla bug vardı. 🐛",
]

def handle_builtin(text: str) -> str | None:
    """Yerleşik komutu işle; tanımazsa None döndür."""
    t = text.lower().strip()

    if any(t == k or t.startswith(k) for k in CIKIS_KOMUTLARI):
        return "__EXIT__"

    if any(k in t for k in SELAMLAMA_KOMUTLARI):
        return "Merhaba! Ben Jarvis. Size nasıl yardımcı olabilirim? 😊"

    if any(k in t for k in SAAT_KOMUTLARI):
        now = datetime.datetime.now()
        return f"Şu an saat {now.strftime('%H:%M:%S')} 🕐"

    if any(k in t for k in TARIH_KOMUTLARI):
        now = datetime.datetime.now()
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        return (f"Bugün {days[now.weekday()]}, "
                f"{now.day} {months[now.month - 1]} {now.year} 📅")

    if any(k in t for k in SISTEM_KOMUTLARI):
        return (f"İşletim Sistemi: {platform.system()} {platform.release()}\n"
                f"Python: {platform.python_version()}\n"
                f"Makine: {platform.machine()}")

    if any(k in t for k in MIZAH_KOMUTLARI):
        return random.choice(SAKALAR)

    if "yardım" in t or "ne yapabilirsin" in t:
        return (
            "Yapabileceklerim:\n"
            "  • Saat ve tarih bilgisi\n"
            "  • Sistem bilgisi\n"
            "  • Şaka yapma\n"
            "  • Herhangi bir konuda soru yanıtlama (OpenAI ile)\n"
            "  • 'çıkış' yazarak programı kapatma\n"
        )

    return None  # yerleşik komut bulunamadı

# ──────────────────────────────────────────────
# OpenAI entegrasyonu
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """Sen Jarvis'sin — Iron Man filmindeki Jarvis gibi zeki, kibar ve yardımsever bir yapay zeka asistanısın.
Türkçe konuşuyorsun. Kısa, net ve faydalı yanıtlar veriyorsun.
Gerektiğinde emoji kullanabilirsin ama aşırıya kaçma.
Kullanıcıya her zaman saygılı ve yardımsever ol."""

def ask_openai(client: "OpenAI", history: list[dict], question: str) -> str:
    history.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        max_tokens=512,
        temperature=0.7,
    )
    answer = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": answer})
    return answer

# ──────────────────────────────────────────────
# Ana döngü
# ──────────────────────────────────────────────
def main() -> None:
    show_banner()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    client = None

    if OPENAI_AVAILABLE and api_key:
        client = OpenAI(api_key=api_key)
        jarvis_print("OpenAI bağlantısı aktif. Hazırım! ✅", "bold green")
    else:
        if not OPENAI_AVAILABLE:
            jarvis_print(
                "openai paketi kurulu değil. Yalnızca yerleşik komutlar kullanılabilir.\n"
                "  Kurmak için: pip install openai",
                "yellow",
            )
        else:
            jarvis_print(
                "OPENAI_API_KEY ortam değişkeni ayarlanmamış.\n"
                "  Tam AI desteği için: export OPENAI_API_KEY='sk-...'",
                "yellow",
            )
        jarvis_print("Yerleşik komut modunda çalışıyorum. 🔧", "cyan")

    jarvis_print("'yardım' yazarak komutları görebilirsiniz. 'çıkış' ile kapatabilirsiniz.\n")

    history: list[dict] = []

    while True:
        try:
            text = user_input()
        except (KeyboardInterrupt, EOFError):
            jarvis_print("Görüşmek üzere! 👋", "bold cyan")
            break

        if not text.strip():
            continue

        # Önce yerleşik komutları dene
        builtin_response = handle_builtin(text)

        if builtin_response == "__EXIT__":
            jarvis_print("Görüşmek üzere! 👋", "bold cyan")
            break

        if builtin_response:
            jarvis_print(builtin_response)
            continue

        # OpenAI'ye sor
        if client:
            try:
                answer = ask_openai(client, history, text)
                jarvis_print(answer)
            except Exception as exc:
                jarvis_print(f"OpenAI hatası: {exc}", "red")
        else:
            jarvis_print(
                "Bu soruyu yanıtlamak için OpenAI bağlantısı gerekiyor.\n"
                "  OPENAI_API_KEY ortam değişkenini ayarlayın.",
                "yellow",
            )


if __name__ == "__main__":
    main()
