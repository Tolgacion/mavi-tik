"""
iot.py — IoT cihaz iletişimi (MQTT + seri port + GPIO)

Kurulum:
  pip install paho-mqtt pyserial
  # Raspberry Pi GPIO için: pip install RPi.GPIO
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Callable, Any

logger = logging.getLogger("VONSENY.iot")


# ── MQTT İstemcisi ────────────────────────────────────────────────────────────
class MQTTBridge:
    """MQTT broker üzerinden IoT cihazlarla iletişim."""

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        client_id: str = "VONSENY",
    ) -> None:
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self._client = None
        self._subscriptions: dict[str, list[Callable]] = {}
        self._connected = False

    def connect(self) -> bool:
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(client_id=self.client_id)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            logger.info("MQTT broker'a bağlanılıyor: %s:%d", self.broker, self.port)
            return True
        except ImportError:
            logger.warning("paho-mqtt kurulu değil: pip install paho-mqtt")
            return False
        except Exception as exc:
            logger.error("MQTT bağlantı hatası: %s", exc)
            return False

    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("MQTT bağlantısı kesildi.")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._connected = True
            logger.info("MQTT bağlandı!")
            # Önceki abonelikleri yeniden yap
            for topic in self._subscriptions:
                client.subscribe(topic)
        else:
            logger.error("MQTT bağlantı kodu: %d", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False
        logger.warning("MQTT bağlantısı kesildi (rc=%d)", rc)

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = msg.payload.decode(errors="replace")

        logger.debug("MQTT mesaj: %s → %s", topic, payload)

        for pattern, callbacks in self._subscriptions.items():
            if self._topic_match(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as exc:
                        logger.error("MQTT callback hatası: %s", exc)

    @staticmethod
    def _topic_match(pattern: str, topic: str) -> bool:
        if pattern == topic:
            return True
        if pattern.endswith("#"):
            return topic.startswith(pattern[:-1])
        parts_p = pattern.split("/")
        parts_t = topic.split("/")
        if len(parts_p) != len(parts_t):
            return False
        return all(p == t or p == "+" for p, t in zip(parts_p, parts_t))

    def subscribe(self, topic: str, callback: Callable[[str, Any], None]) -> None:
        self._subscriptions.setdefault(topic, []).append(callback)
        if self._client and self._connected:
            self._client.subscribe(topic)
        logger.info("MQTT abone: %s", topic)

    def publish(self, topic: str, payload: Any, qos: int = 0) -> bool:
        if not self._client or not self._connected:
            logger.warning("MQTT bağlı değil, mesaj gönderilemedi.")
            return False
        try:
            data = json.dumps(payload) if not isinstance(payload, (str, bytes)) else payload
            self._client.publish(topic, data, qos=qos)
            logger.debug("MQTT gönderildi: %s → %s", topic, data)
            return True
        except Exception as exc:
            logger.error("MQTT publish hatası: %s", exc)
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected


# ── Seri Port İletişimi ───────────────────────────────────────────────────────
class SerialBridge:
    """Arduino / ESP32 / seri cihazlarla iletişim."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._callbacks: list[Callable[[str], None]] = []
        self._running = False

    def connect(self) -> bool:
        try:
            import serial
            self._serial = serial.Serial(self.port, self.baudrate, timeout=1)
            logger.info("Seri port açıldı: %s @ %d", self.port, self.baudrate)
            self._running = True
            threading.Thread(target=self._read_loop, daemon=True).start()
            return True
        except ImportError:
            logger.warning("pyserial kurulu değil: pip install pyserial")
            return False
        except Exception as exc:
            logger.error("Seri port hatası: %s", exc)
            return False

    def disconnect(self) -> None:
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()

    def send(self, data: str) -> bool:
        if not self._serial or not self._serial.is_open:
            logger.warning("Seri port kapalı.")
            return False
        try:
            self._serial.write((data + "\n").encode())
            logger.debug("Seri gönderildi: %s", data)
            return True
        except Exception as exc:
            logger.error("Seri gönderme hatası: %s", exc)
            return False

    def send_json(self, obj: dict) -> bool:
        return self.send(json.dumps(obj))

    def on_data(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    def _read_loop(self) -> None:
        while self._running and self._serial and self._serial.is_open:
            try:
                line = self._serial.readline().decode(errors="replace").strip()
                if line:
                    logger.debug("Seri alındı: %s", line)
                    for cb in self._callbacks:
                        try:
                            cb(line)
                        except Exception as exc:
                            logger.error("Seri callback hatası: %s", exc)
            except Exception:
                pass


# ── Yüksek Seviye IoT Yöneticisi ─────────────────────────────────────────────
class IoTManager:
    """Tüm IoT alt sistemlerini yöneten ana sınıf."""

    def __init__(self) -> None:
        self.mqtt = MQTTBridge()
        self.serial_devices: dict[str, SerialBridge] = {}
        self._device_states: dict[str, Any] = {}

    # ── MQTT Kısa Yollar ───────────────────────────────────────────────────────
    def connect_mqtt(self, broker: str = "localhost", port: int = 1883) -> bool:
        self.mqtt.broker = broker
        self.mqtt.port = port
        return self.mqtt.connect()

    def control_device(self, device_id: str, command: str, value: Any = None) -> bool:
        """Bir IoT cihazına komut gönder."""
        topic = f"vonseny/control/{device_id}"
        payload = {"command": command, "value": value}
        self._device_states[device_id] = payload
        return self.mqtt.publish(topic, payload)

    def get_sensor_data(self, sensor_id: str) -> Any:
        """Son bilinen sensör verisini al."""
        return self._device_states.get(sensor_id)

    def register_sensor(
        self, sensor_id: str, callback: Callable[[str, Any], None]
    ) -> None:
        topic = f"vonseny/sensor/{sensor_id}"

        def _handler(t, p):
            self._device_states[sensor_id] = p
            callback(sensor_id, p)

        self.mqtt.subscribe(topic, _handler)

    # ── Seri Port Kısa Yollar ─────────────────────────────────────────────────
    def add_serial_device(
        self, name: str, port: str = "/dev/ttyUSB0", baudrate: int = 9600
    ) -> bool:
        bridge = SerialBridge(port, baudrate)
        if bridge.connect():
            self.serial_devices[name] = bridge
            return True
        return False

    def send_serial(self, device_name: str, data: str) -> bool:
        bridge = self.serial_devices.get(device_name)
        if not bridge:
            logger.warning("Seri cihaz bulunamadı: %s", device_name)
            return False
        return bridge.send(data)

    # ── Cihaz Listesi ────────────────────────────────────────────────────────
    def list_devices(self) -> dict:
        return {
            "mqtt_connected": self.mqtt.is_connected,
            "serial_devices": list(self.serial_devices.keys()),
            "device_states": self._device_states,
        }
