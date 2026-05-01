"""
cad.py — CAD otomasyon modülü (FreeCAD yüksek seviye API)

FreeCAD kurulumu:
  Ubuntu/Debian: sudo apt install freecad
  Windows: https://www.freecad.org/downloads.php
  pip install freecad  (bazı platformlarda)

SolidWorks için:
  pip install pywin32  (Windows)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("VONSENY.cad")


# ── FreeCAD Script Şablonları ─────────────────────────────────────────────────
FREECAD_BOX_TEMPLATE = """
import FreeCAD, Part
doc = FreeCAD.newDocument("{name}")
box = doc.addObject("Part::Box", "Box")
box.Label = "{name}"
box.Length = {length}
box.Width  = {width}
box.Height = {height}
doc.recompute()
doc.saveAs("{output}")
print("OK:{output}")
"""

FREECAD_CYLINDER_TEMPLATE = """
import FreeCAD, Part
doc = FreeCAD.newDocument("{name}")
cyl = doc.addObject("Part::Cylinder", "Cylinder")
cyl.Label  = "{name}"
cyl.Radius = {radius}
cyl.Height = {height}
doc.recompute()
doc.saveAs("{output}")
print("OK:{output}")
"""

FREECAD_SPHERE_TEMPLATE = """
import FreeCAD, Part
doc = FreeCAD.newDocument("{name}")
sph = doc.addObject("Part::Sphere", "Sphere")
sph.Label  = "{name}"
sph.Radius = {radius}
doc.recompute()
doc.saveAs("{output}")
print("OK:{output}")
"""

FREECAD_ASSEMBLY_TEMPLATE = """
import FreeCAD, Part
doc = FreeCAD.newDocument("{name}")
{part_scripts}
doc.recompute()
doc.saveAs("{output}")
print("OK:{output}")
"""


class CADEngine:
    """FreeCAD / SolidWorks CAD otomasyon motoru."""

    def __init__(self, output_dir: str = "./cad_output") -> None:
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _run_freecad_script(self, script: str, script_name: str = "vonseny_cad") -> bool:
        """FreeCAD Python betiğini çalıştır."""
        tmp = f"/tmp/{script_name}.py"
        Path(tmp).write_text(script, encoding="utf-8")
        import subprocess
        try:
            result = subprocess.run(
                ["freecad", "-c", tmp],
                capture_output=True, text=True, timeout=30
            )
            if "OK:" in result.stdout:
                logger.info("FreeCAD başarılı: %s", result.stdout.strip())
                return True
            logger.warning("FreeCAD çıktı: %s", result.stdout)
            if result.stderr:
                logger.error("FreeCAD hata: %s", result.stderr[:200])
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("FreeCAD kurulu değil. Kurulum: sudo apt install freecad")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FreeCAD zaman aşımı.")
            return False

    # ── Temel Parçalar ───────────────────────────────────────────────────────
    def create_box(
        self,
        length: float, width: float, height: float,
        name: str = "Kutu",
        output: str | None = None,
    ) -> str:
        """Dikdörtgen prizma (kutu) parça oluştur."""
        output = output or str(Path(self.output_dir) / f"{name}.FCStd")
        script = FREECAD_BOX_TEMPLATE.format(
            name=name, length=length, width=width, height=height, output=output
        )
        ok = self._run_freecad_script(script, f"box_{name}")
        return output if ok else ""

    def create_cylinder(
        self,
        radius: float, height: float,
        name: str = "Silindir",
        output: str | None = None,
    ) -> str:
        """Silindir parça oluştur."""
        output = output or str(Path(self.output_dir) / f"{name}.FCStd")
        script = FREECAD_CYLINDER_TEMPLATE.format(
            name=name, radius=radius, height=height, output=output
        )
        ok = self._run_freecad_script(script, f"cyl_{name}")
        return output if ok else ""

    def create_sphere(
        self,
        radius: float,
        name: str = "Küre",
        output: str | None = None,
    ) -> str:
        """Küre parça oluştur."""
        output = output or str(Path(self.output_dir) / f"{name}.FCStd")
        script = FREECAD_SPHERE_TEMPLATE.format(
            name=name, radius=radius, output=output
        )
        ok = self._run_freecad_script(script, f"sph_{name}")
        return output if ok else ""

    def create_assembly(
        self, parts: list[dict], name: str = "Montaj", output: str | None = None
    ) -> str:
        """
        Çoklu parçadan oluşan montaj oluştur.
        parts = [
          {"type": "box", "name": "Taban", "length": 100, "width": 80, "height": 10},
          {"type": "cylinder", "name": "Pin", "radius": 5, "height": 30},
          ...
        ]
        """
        output = output or str(Path(self.output_dir) / f"{name}.FCStd")
        scripts = []
        offset_x = 0.0

        for p in parts:
            ptype = p.get("type", "box")
            pname = p.get("name", "Part")
            if ptype == "box":
                scripts.append(
                    f'b = doc.addObject("Part::Box", "{pname}")\n'
                    f'b.Length={p.get("length",10)}; b.Width={p.get("width",10)}; '
                    f'b.Height={p.get("height",10)}\n'
                    f'b.Placement.Base.x = {offset_x}\n'
                )
                offset_x += float(p.get("length", 10)) + 5
            elif ptype == "cylinder":
                scripts.append(
                    f'c = doc.addObject("Part::Cylinder", "{pname}")\n'
                    f'c.Radius={p.get("radius",5)}; c.Height={p.get("height",10)}\n'
                    f'c.Placement.Base.x = {offset_x}\n'
                )
                offset_x += float(p.get("radius", 5)) * 2 + 5
            elif ptype == "sphere":
                scripts.append(
                    f's = doc.addObject("Part::Sphere", "{pname}")\n'
                    f's.Radius={p.get("radius",5)}\n'
                    f's.Placement.Base.x = {offset_x}\n'
                )
                offset_x += float(p.get("radius", 5)) * 2 + 5

        script = FREECAD_ASSEMBLY_TEMPLATE.format(
            name=name,
            part_scripts="\n".join(scripts),
            output=output,
        )
        ok = self._run_freecad_script(script, f"asm_{name}")
        return output if ok else ""

    def export_stl(self, freecad_file: str, output: str | None = None) -> str:
        """FreeCAD dosyasını STL'ye dönüştür (3D baskı için)."""
        if not output:
            output = freecad_file.replace(".FCStd", ".stl")
        script = f"""
import FreeCAD, Mesh
doc = FreeCAD.open("{freecad_file}")
objs = doc.Objects
Mesh.export(objs, "{output}")
print("OK:{output}")
"""
        ok = self._run_freecad_script(script, "export_stl")
        return output if ok else ""

    # ── SolidWorks (Windows) ─────────────────────────────────────────────────
    def solidworks_create_box(
        self, length: float, width: float, height: float
    ) -> bool:
        """SolidWorks COM API ile kutu parça oluştur."""
        try:
            import win32com.client  # type: ignore
            sw = win32com.client.Dispatch("SldWorks.Application")
            sw.Visible = True
            doc = sw.NewDocument(
                sw.GetUserPreferenceStringValue(9), 0, 0, 0
            )
            feature_mgr = doc.FeatureManager
            feature_mgr.FeatureExtrusion2(
                True, False, False, 0, 0,
                length, 0, False, False, False, False,
                0, 0, False, False, False, False, True, True, True, 0, 0, False
            )
            logger.info("SolidWorks kutu oluşturuldu: %sx%sx%s", length, width, height)
            return True
        except ImportError:
            logger.warning("pywin32 kurulu değil (Windows için): pip install pywin32")
            return False
        except Exception as exc:
            logger.error("SolidWorks hatası: %s", exc)
            return False

    # ── Yardımcı ─────────────────────────────────────────────────────────────
    def list_output_files(self) -> list[str]:
        return sorted(os.listdir(self.output_dir))

    def is_freecad_available(self) -> bool:
        import subprocess
        try:
            r = subprocess.run(["freecad", "--version"], capture_output=True, timeout=5)
            return r.returncode == 0
        except FileNotFoundError:
            return False
