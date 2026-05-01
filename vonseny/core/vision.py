"""
vision.py — OpenCV kamera, YOLOv8 nesne/tehlike tespiti, hedef takibi

Kurulum:
  pip install opencv-python ultralytics numpy
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger("VONSENY.vision")

# ── Tehlikeli nesne sınıfları (COCO / askeri genişletilmiş) ──────────────────
THREAT_CLASSES = {
    # Silah & tehlike
    "knife", "gun", "rifle", "pistol", "sword", "scissors",
    # Araç tehdidi
    "truck", "bus",
    # Hayvan tehdidi
    "bear", "wolf",
    # Yangın/duman (özel model gerektirir)
    "fire", "smoke",
    # İnsan (kalabalık izleme için)
    "person",
}

MILITARY_THREAT_KEYWORDS = {
    "knife", "gun", "rifle", "pistol", "fire", "smoke"
}


@dataclass
class DetectedObject:
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    is_threat: bool = field(init=False)
    is_military_threat: bool = field(init=False)

    def __post_init__(self) -> None:
        self.is_threat = self.class_name.lower() in THREAT_CLASSES
        self.is_military_threat = self.class_name.lower() in MILITARY_THREAT_KEYWORDS


class VisionEngine:
    """Kamera yönetimi, YOLO nesne tespiti ve hedef takibi."""

    def __init__(self, camera_index: int = 0, use_yolo: bool = True) -> None:
        self.camera_index = camera_index
        self.use_yolo = use_yolo
        self._cap = None
        self._yolo = None
        self._tracker = None
        self._running = False
        self._frame = None
        self._lock = threading.Lock()
        self._threat_callbacks: list[Callable[[list[DetectedObject]], None]] = []
        self._frame_callbacks: list[Callable] = []

    # ── Kamera ───────────────────────────────────────────────────────────────
    def start_camera(self) -> bool:
        try:
            import cv2
            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                logger.error("Kamera açılamadı (index=%d)", self.camera_index)
                return False
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
            logger.info("Kamera başlatıldı: index=%d", self.camera_index)
            return True
        except ImportError:
            logger.warning("opencv-python kurulu değil: pip install opencv-python")
            return False

    def stop_camera(self) -> None:
        self._running = False
        if self._cap:
            self._cap.release()
            self._cap = None

    # ── YOLO ─────────────────────────────────────────────────────────────────
    def _load_yolo(self):
        if self._yolo is None and self.use_yolo:
            try:
                from ultralytics import YOLO
                self._yolo = YOLO("yolov8n.pt")  # nano model, hızlı
                logger.info("YOLOv8 modeli yüklendi.")
            except ImportError:
                logger.warning("ultralytics kurulu değil: pip install ultralytics")
            except Exception as exc:
                logger.error("YOLO yüklenemedi: %s", exc)
        return self._yolo

    # ── Nesne Tespiti ─────────────────────────────────────────────────────────
    def detect(self, frame) -> list[DetectedObject]:
        """Frame üzerinde YOLO ile nesne tespiti yap."""
        model = self._load_yolo()
        if model is None:
            return []
        try:
            results = model(frame, verbose=False)
            objects: list[DetectedObject] = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = result.names[cls_id]
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    obj = DetectedObject(cls_name, conf, (x1, y1, x2, y2))
                    objects.append(obj)
            return objects
        except Exception as exc:
            logger.error("Tespit hatası: %s", exc)
            return []

    # ── Hedef Takibi (CSRT) ───────────────────────────────────────────────────
    def init_tracker(self, frame, bbox: tuple[int, int, int, int]):
        """Belirli bir bölgeyi takip etmeye başla."""
        try:
            import cv2
            self._tracker = cv2.TrackerCSRT_create()
            x1, y1, x2, y2 = bbox
            w, h = x2 - x1, y2 - y1
            self._tracker.init(frame, (x1, y1, w, h))
            logger.info("Hedef takibi başlatıldı: bbox=%s", bbox)
        except Exception as exc:
            logger.error("Takip başlatma hatası: %s", exc)

    def update_tracker(self, frame) -> tuple[bool, tuple] | None:
        """Takipçiyi güncelle, başarı ve bbox döndür."""
        if self._tracker is None:
            return None
        try:
            ok, bbox = self._tracker.update(frame)
            return ok, bbox
        except Exception as exc:
            logger.error("Takip güncelleme hatası: %s", exc)
            return None

    # ── Frame Çizimi ─────────────────────────────────────────────────────────
    def draw_detections(self, frame, objects: list[DetectedObject]):
        """Tespit edilen nesneleri frame üzerine çiz."""
        try:
            import cv2
            for obj in objects:
                x1, y1, x2, y2 = obj.bbox
                color = (0, 0, 255) if obj.is_military_threat else (
                    (0, 165, 255) if obj.is_threat else (0, 255, 0)
                )
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{obj.class_name} {obj.confidence:.0%}"
                if obj.is_military_threat:
                    label = f"⚠ TEHLİKE: {label}"
                cv2.putText(
                    frame, label, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                )
        except Exception as exc:
            logger.error("Çizim hatası: %s", exc)
        return frame

    # ── Callback Yönetimi ─────────────────────────────────────────────────────
    def on_threat(self, callback: Callable[[list[DetectedObject]], None]) -> None:
        self._threat_callbacks.append(callback)

    def on_frame(self, callback: Callable) -> None:
        self._frame_callbacks.append(callback)

    # ── Ana Video Döngüsü ─────────────────────────────────────────────────────
    def start_stream(self, show_window: bool = True, detect_interval: int = 3) -> None:
        """Kamera akışını başlat, her N frame'de bir tespit yap."""
        if not self.start_camera():
            return
        self._running = True
        thread = threading.Thread(
            target=self._stream_loop,
            args=(show_window, detect_interval),
            daemon=True,
        )
        thread.start()
        logger.info("Kamera akışı başlatıldı.")

    def _stream_loop(self, show_window: bool, detect_interval: int) -> None:
        import cv2
        frame_count = 0
        last_objects: list[DetectedObject] = []

        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_count += 1

            # Nesne tespiti — her N frame'de bir
            if frame_count % detect_interval == 0:
                last_objects = self.detect(frame)
                threats = [o for o in last_objects if o.is_threat]
                if threats:
                    for cb in self._threat_callbacks:
                        try:
                            cb(threats)
                        except Exception as exc:
                            logger.error("Tehlike callback hatası: %s", exc)

            # Takipçi güncelle
            tracker_result = self.update_tracker(frame)
            if tracker_result:
                ok, bbox = tracker_result
                if ok:
                    x, y, w, h = [int(v) for v in bbox]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    cv2.putText(
                        frame, "TAKİP", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2
                    )

            frame = self.draw_detections(frame, last_objects)

            # Durum göstergesi
            cv2.putText(
                frame, "VONSENY VISION AKTIF", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2
            )
            cv2.putText(
                frame, f"Nesne: {len(last_objects)}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2
            )

            with self._lock:
                self._frame = frame.copy()

            for cb in self._frame_callbacks:
                try:
                    cb(frame)
                except Exception:
                    pass

            if show_window:
                cv2.imshow("VONSENY — Görüş Sistemi", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("t") and last_objects:
                    # İlk nesneyi takibe al
                    self.init_tracker(frame, last_objects[0].bbox)

        self.stop_camera()
        if show_window:
            cv2.destroyAllWindows()

    def get_frame(self):
        """Thread-safe son frame'i al."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def capture_snapshot(self, path: str = "snapshot.jpg") -> bool:
        """Anlık görüntü kaydet."""
        frame = self.get_frame()
        if frame is None:
            return False
        try:
            import cv2
            cv2.imwrite(path, frame)
            logger.info("Snapshot kaydedildi: %s", path)
            return True
        except Exception as exc:
            logger.error("Snapshot hatası: %s", exc)
            return False

    def count_objects(self) -> dict[str, int]:
        """Şu anda ekranda kaç tane hangi nesne var."""
        frame = self.get_frame()
        if frame is None:
            return {}
        objects = self.detect(frame)
        counts: dict[str, int] = {}
        for obj in objects:
            counts[obj.class_name] = counts.get(obj.class_name, 0) + 1
        return counts
