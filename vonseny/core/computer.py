"""
computer.py — Laptop / masaüstü kontrolü

Özellikler:
  - Uygulama aç/kapat/odakla
  - Klavye & fare otomasyonu (pyautogui)
  - Ekran görüntüsü
  - Dosya sistemi işlemleri
  - SolidWorks makro çalıştırma (COM / subprocess)
  - Sistem bilgisi (CPU, RAM, disk, ağ)

Kurulum:
  pip install pyautogui psutil pillow
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("VONSENY.computer")

SYSTEM = platform.system()  # "Windows" | "Linux" | "Darwin"


# ── Sistem Bilgisi ─────────────────────────────────────────────────────────────
def get_system_info() -> dict[str, Any]:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu_percent": cpu,
            "ram_used_gb": round(ram.used / 1e9, 2),
            "ram_total_gb": round(ram.total / 1e9, 2),
            "ram_percent": ram.percent,
            "disk_used_gb": round(disk.used / 1e9, 2),
            "disk_total_gb": round(disk.total / 1e9, 2),
            "net_sent_mb": round(net.bytes_sent / 1e6, 2),
            "net_recv_mb": round(net.bytes_recv / 1e6, 2),
        }
    except ImportError:
        logger.warning("psutil kurulu değil: pip install psutil")
        return {"os": f"{platform.system()} {platform.release()}"}
    except Exception as exc:
        logger.error("Sistem bilgisi hatası: %s", exc)
        return {}


# ── Uygulama Yönetimi ──────────────────────────────────────────────────────────
def open_application(app: str) -> bool:
    """Uygulama aç (çapraz platform)."""
    logger.info("Uygulama açılıyor: %s", app)
    try:
        if SYSTEM == "Windows":
            os.startfile(app)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", app])
        else:
            subprocess.Popen([app])
        return True
    except Exception as exc:
        logger.error("Uygulama açma hatası: %s", exc)
        return False


def close_application(process_name: str) -> bool:
    """Süreç adıyla uygulama kapat."""
    try:
        import psutil
        for proc in psutil.process_iter(["name", "pid"]):
            if process_name.lower() in proc.info["name"].lower():
                proc.terminate()
                logger.info("Uygulama kapatıldı: %s (PID=%d)", proc.info["name"], proc.pid)
                return True
        logger.warning("Süreç bulunamadı: %s", process_name)
        return False
    except ImportError:
        # psutil yoksa os kill
        if SYSTEM == "Windows":
            os.system(f"taskkill /f /im {process_name}")
        else:
            os.system(f"pkill -f {process_name}")
        return True
    except Exception as exc:
        logger.error("Kapatma hatası: %s", exc)
        return False


def list_running_apps() -> list[str]:
    """Çalışan uygulama listesi."""
    try:
        import psutil
        names = sorted({
            p.info["name"]
            for p in psutil.process_iter(["name"])
            if p.info["name"]
        })
        return names
    except ImportError:
        return []


def run_command(cmd: str, shell: bool = True) -> tuple[str, str, int]:
    """Kabuk komutu çalıştır, (stdout, stderr, returncode) döndür."""
    logger.info("Komut çalıştırılıyor: %s", cmd)
    result = subprocess.run(
        cmd, shell=shell, capture_output=True, text=True, timeout=30
    )
    return result.stdout, result.stderr, result.returncode


# ── Klavye & Fare ──────────────────────────────────────────────────────────────
class InputController:
    """pyautogui tabanlı klavye ve fare kontrolü."""

    def __init__(self) -> None:
        self._gui = None

    def _get_gui(self):
        if self._gui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True  # Sol üst köşeye götürünce dur
                pyautogui.PAUSE = 0.05
                self._gui = pyautogui
            except ImportError:
                logger.warning("pyautogui kurulu değil: pip install pyautogui")
        return self._gui

    def type_text(self, text: str, interval: float = 0.03) -> None:
        gui = self._get_gui()
        if gui:
            gui.typewrite(text, interval=interval)

    def press_key(self, *keys: str) -> None:
        gui = self._get_gui()
        if gui:
            gui.hotkey(*keys)

    def click(self, x: int, y: int, button: str = "left") -> None:
        gui = self._get_gui()
        if gui:
            gui.click(x, y, button=button)

    def move_to(self, x: int, y: int, duration: float = 0.3) -> None:
        gui = self._get_gui()
        if gui:
            gui.moveTo(x, y, duration=duration)

    def screenshot(self, path: str = "screen.png") -> bool:
        gui = self._get_gui()
        if not gui:
            return False
        try:
            img = gui.screenshot()
            img.save(path)
            logger.info("Ekran görüntüsü: %s", path)
            return True
        except Exception as exc:
            logger.error("Screenshot hatası: %s", exc)
            return False

    def scroll(self, clicks: int = 3, x: int | None = None, y: int | None = None) -> None:
        gui = self._get_gui()
        if gui:
            if x and y:
                gui.scroll(clicks, x=x, y=y)
            else:
                gui.scroll(clicks)

    def get_screen_size(self) -> tuple[int, int]:
        gui = self._get_gui()
        if gui:
            return gui.size()
        return (1920, 1080)


# ── Dosya Sistemi ──────────────────────────────────────────────────────────────
class FileManager:
    """Dosya ve klasör işlemleri."""

    @staticmethod
    def list_dir(path: str = ".") -> list[str]:
        try:
            return sorted(os.listdir(path))
        except Exception as exc:
            logger.error("Dizin listesi hatası: %s", exc)
            return []

    @staticmethod
    def read_file(path: str) -> str:
        try:
            return Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Dosya okuma hatası: %s", exc)
            return ""

    @staticmethod
    def write_file(path: str, content: str) -> bool:
        try:
            Path(path).write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.error("Dosya yazma hatası: %s", exc)
            return False

    @staticmethod
    def search_files(root: str, pattern: str) -> list[str]:
        matches = []
        for p in Path(root).rglob(pattern):
            matches.append(str(p))
        return matches


# ── SolidWorks / FreeCAD Otomasyonu ───────────────────────────────────────────
class CADController:
    """
    SolidWorks (Windows COM) veya FreeCAD Python API ile CAD otomasyonu.
    """

    # ── FreeCAD ─────────────────────────────────────────────────────────────
    @staticmethod
    def freecad_create_box(
        length: float, width: float, height: float, output: str = "box.FCStd"
    ) -> bool:
        """FreeCAD ile kutu parça oluştur."""
        script = f"""
import FreeCAD, Part, FreeCADGui
doc = FreeCAD.newDocument("VONSENY_Part")
box = doc.addObject("Part::Box", "Box")
box.Length = {length}
box.Width  = {width}
box.Height = {height}
doc.recompute()
doc.saveAs("{output}")
print("Kutu oluşturuldu:", "{output}")
"""
        tmp_path = "/tmp/vonseny_freecad.py"
        Path(tmp_path).write_text(script)
        stdout, stderr, rc = run_command(f"freecad -c {tmp_path}")
        logger.info("FreeCAD çıktı: %s", stdout)
        if stderr:
            logger.warning("FreeCAD hata: %s", stderr)
        return rc == 0

    @staticmethod
    def freecad_run_script(script_path: str) -> bool:
        stdout, stderr, rc = run_command(f"freecad -c {script_path}")
        logger.info("FreeCAD script: %s", stdout)
        return rc == 0

    # ── SolidWorks (Windows COM) ─────────────────────────────────────────────
    @staticmethod
    def solidworks_run_macro(macro_path: str) -> bool:
        """SolidWorks makro dosyasını çalıştır (Windows + SolidWorks gerekli)."""
        if SYSTEM != "Windows":
            logger.warning("SolidWorks yalnızca Windows'ta çalışır.")
            return False
        try:
            import win32com.client  # type: ignore
            sw = win32com.client.Dispatch("SldWorks.Application")
            sw.Visible = True
            sw.RunMacro2(macro_path, "", "", 0, 0)
            logger.info("SolidWorks makro çalıştırıldı: %s", macro_path)
            return True
        except ImportError:
            logger.warning("pywin32 kurulu değil: pip install pywin32")
            return False
        except Exception as exc:
            logger.error("SolidWorks hatası: %s", exc)
            return False

    @staticmethod
    def solidworks_open_file(file_path: str) -> bool:
        """SolidWorks ile dosya aç."""
        if SYSTEM != "Windows":
            return False
        try:
            import win32com.client  # type: ignore
            sw = win32com.client.Dispatch("SldWorks.Application")
            sw.Visible = True
            doc_type = 1 if file_path.endswith(".sldprt") else 2
            sw.OpenDoc(file_path, doc_type)
            return True
        except Exception as exc:
            logger.error("SolidWorks açma hatası: %s", exc)
            return False


# ── Bildirim Gönder ───────────────────────────────────────────────────────────
def send_notification(title: str, message: str) -> None:
    """İşletim sistemine bildirim gönder."""
    try:
        if SYSTEM == "Windows":
            from win10toast import ToastNotifier  # type: ignore
            ToastNotifier().show_toast(title, message, duration=5)
        elif SYSTEM == "Darwin":
            os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
        else:
            os.system(f'notify-send "{title}" "{message}"')
    except Exception as exc:
        logger.error("Bildirim hatası: %s", exc)
