# VONSENY — Very Optimized Neural System for Engineering & National York 🤖

Iron Man'in JARVIS'inden ilham alan, **tamamen yerel çalışan** (OpenAI API yok),  
çok modüllü Türkçe yapay zeka sistemi.

---

## ✨ Özellikler

| Modül | Açıklama |
|-------|----------|
| 🧠 **Yerel LLM** | Ollama üzerinden llama3.2 / mistral / phi3 |
| 🎤 **Ses Tanıma** | Whisper (yerel, offline), pyttsx3 TTS |
| 📷 **Görüntü** | OpenCV kamera + YOLOv8 nesne/tehlike tespiti + hedef takibi |
| 📡 **IoT** | MQTT broker + seri port (Arduino/ESP32) |
| 💻 **PC Kontrolü** | Uygulama aç/kapat, klavye/fare, ekran görüntüsü |
| 🔧 **CAD** | FreeCAD parça & montaj oluşturma + STL export |
| 🌐 **Web** | DuckDuckGo arama, Wikipedia, ürün karşılaştırma |
| ⚔️ **Askeri** | Taktik bilgi tabanı, tehdit değerlendirme, silah sistemi bilgisi |

---

## 🚀 Kurulum

### 1. Ollama (Yerel LLM Motor)
```bash
# Linux / macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows: https://ollama.com/download

# Model indir
ollama pull llama3.2    # 3B — hızlı
ollama pull mistral     # 7B — daha zeki
ollama pull phi3        # Microsoft Phi-3

# Servisi başlat
ollama serve
```

### 2. Python Bağımlılıkları

```bash
# Temel kurulum (LLM + web + PC kontrolü)
pip install requests rich beautifulsoup4 lxml duckduckgo-search psutil

# Tam kurulum
pip install -r requirements.txt
```

---

## ▶️ Çalıştırma

```bash
python vonseny.py                            # Temel mod
python vonseny.py --voice                   # Sesli mod
python vonseny.py --camera --show-camera    # Kameralı mod
python vonseny.py --voice --camera --iot    # Tam mod
python vonseny.py --model mistral           # Farklı model
python vonseny.py --help                    # Tüm seçenekler
```

---

## 💬 Komutlar

| Komut | Açıklama |
|-------|----------|
| `sistem bilgisi` | CPU/RAM/Disk durumu |
| `ekran görüntüsü` | Ekranı kaydet |
| `uygulama aç solidworks` | Uygulama başlat |
| `uygulama kapat chrome` | Uygulama kapat |
| `komut çalıştır ls -la` | Kabuk komutu çalıştır |
| `ara RTX 4090 fiyat` | Web araması |
| `wikipedia kuantum bilgisayar` | Wikipedia özeti |
| `telefon araştır 15000 TL` | Bütçeye göre telefon önerisi |
| `araştır Bayraktar TB3` | Derin web araştırması |
| `askeri terim ied` | Askeri terim açıkla |
| `taktik şehir muharebesi` | Taktik bilgisi |
| `silah bayraktar tb2` | Silah sistemi bilgisi |
| `cad kutu 100 50 30` | FreeCAD kutu parça (mm) |
| `cad silindir 25 80` | FreeCAD silindir |
| `iot kontrol led1 on` | IoT cihaza komut |
| `model listesi` | Mevcut Ollama modelleri |
| `model değiştir mistral` | Model değiştir |
| *herhangi soru* | Yerel LLM'e sor |

---

## 🏗️ Mimari

```
vonseny/
├── vonseny.py          # Ana orkestrasyon + komut döngüsü
└── core/
    ├── brain.py        # Ollama LLM motoru (akışlı yanıt)
    ├── voice.py        # Whisper STT + pyttsx3 TTS
    ├── vision.py       # OpenCV + YOLOv8 + hedef takibi
    ├── iot.py          # MQTT + seri port
    ├── computer.py     # PC kontrolü
    ├── web.py          # DuckDuckGo + Wikipedia + ürün araştırma
    ├── cad.py          # FreeCAD yüksek seviye API
    └── military.py     # Askeri bilgi tabanı + tehdit analizi
```

---

> **Not:** Tüm LLM işlemi yerel makinenizde gerçekleşir. İnternet yalnızca web araştırma için gereklidir.
