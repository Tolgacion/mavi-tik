"""
military.py — Askeri bilgi ve taktik modülü

Bu modül yerel bir bilgi tabanı (knowledge base) içerir.
Dışa bağımlılık yoktur.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("VONSENY.military")


# ── Sınıflandırma ────────────────────────────────────────────────────────────
THREAT_LEVELS = {
    0: "YEŞİL — Normal durum",
    1: "SARI — Dikkat",
    2: "TURUNCU — Yüksek tehdit",
    3: "KIRMIZI — KRİTİK TEHLİKE",
}

# ── Askeri Terimler Sözlüğü ───────────────────────────────────────────────────
MILITARY_GLOSSARY: dict[str, str] = {
    "c4isr": (
        "Command, Control, Communications, Computers, Intelligence, Surveillance and Reconnaissance. "
        "Komuta, kontrol, iletişim, bilgisayar, istihbarat, gözetleme ve keşif sistemi bütünü."
    ),
    "ied": (
        "Improvised Explosive Device — El yapımı patlayıcı düzenek. "
        "Asimetrik savaşta sıkça kullanılan terör silahı."
    ),
    "isr": (
        "Intelligence, Surveillance, Reconnaissance — İstihbarat, Gözetleme, Keşif. "
        "Modern muharebe alanında bilgi üstünlüğü sağlayan sistem."
    ),
    "roe": (
        "Rules of Engagement — Muharebe katılım kuralları. "
        "Askeri kuvvetlerin ne zaman ve nasıl güç kullanacağını belirleyen direktifler."
    ),
    "medevac": (
        "Medical Evacuation — Tıbbi tahliye. "
        "Yaralı personelin savaş alanından sağlık tesisine nakli."
    ),
    "sitrep": "Situation Report — Durum raporu. Sahadan komutana periyodik bilgi güncellemesi.",
    "frago": "Fragmentary Order — Parçalanmış emir. Operasyon sırasında yapılan hızlı değişiklik emri.",
    "sop": "Standard Operating Procedure — Standart operasyon prosedürü.",
    "aor": "Area of Responsibility — Sorumluluk Alanı.",
    "fob": "Forward Operating Base — İleri Harekât Üssü.",
    "los": "Line of Sight — Görüş hattı. Silah sistemlerinde hedefle doğrudan göz teması.",
    "ew": "Electronic Warfare — Elektronik Harp. Düşman sistemlerini jamming, spoofing ile etkisiz kılma.",
    "humint": "Human Intelligence — İnsan istihbaratı. Ajan ve muhbir ağlarından toplanan bilgi.",
    "sigint": "Signals Intelligence — Sinyal istihbaratı. Elektronik iletişimin dinlenmesi.",
    "imint": "Imagery Intelligence — Görüntü istihbaratı. Uydu ve insansız hava aracı görüntüleri.",
    "nato": "North Atlantic Treaty Organization — Kuzey Atlantik Antlaşması Örgütü.",
    "cas": "Close Air Support — Yakın Hava Desteği. Kara kuvvetlerine havadan ateş desteği.",
    "iaf": "Integrated Air Defense — Entegre Hava Savunma Sistemi.",
    "ecm": "Electronic Countermeasures — Elektronik Karşı Tedbirler.",
    "uav": "Unmanned Aerial Vehicle — İnsansız Hava Aracı (İHA).",
    "ucav": "Unmanned Combat Aerial Vehicle — Silahlı İnsansız Hava Aracı (SIHA).",
    "loitering munition": "Kamikazı / Gezgin mühimmat. Hedef arayarak üzerine dalan patlayıcı.",
}

# ── Taktikler ─────────────────────────────────────────────────────────────────
TACTICS: dict[str, str] = {
    "şehir muharebesi": (
        "MOUT (Military Operations in Urban Terrain) temel prensipleri:\n"
        "1. Bina bina temizleme — yukarıdan aşağı.\n"
        "2. Çatı hattı kontrolü önce sağlanır.\n"
        "3. Mühimmat yetersizliği riski — ikmal hatları canlı tutulur.\n"
        "4. Sivilleri tehditten ayırt etmek ROE'ye göre kritiktir.\n"
        "5. IED tehdidine karşı yavaş ve kontrollü ilerleme."
    ),
    "savunma": (
        "Savunma mevzii prensipleri:\n"
        "1. Derinlikli savunma — birden fazla hat.\n"
        "2. Engel sistemleri (mayın, barikat, hendek).\n"
        "3. Ateş desteği koordinasyonu.\n"
        "4. Geri çekilme güzergahları önceden belirlenir.\n"
        "5. Tünel ve yeraltı mevzileri kullanılır."
    ),
    "keşif": (
        "Keşif harekâtı prensipleri:\n"
        "1. Gizlilik — maksimum sessizlik, termal kamuflaj.\n"
        "2. Küçük taktik gruplar (2-4 kişi optimal).\n"
        "3. Gözetleme noktası seçimi: yüksek, görüş açısı geniş, geri çekilebilir.\n"
        "4. SIGINT desteği ile koordinasyon.\n"
        "5. Temasla çekil — temas halinde imha değil, bilgi topla ve çekil."
    ),
    "drone savunma": (
        "Drone / İHA tehdidine karşı önlemler:\n"
        "1. RF jamming sistemleri (frekans boğma).\n"
        "2. Anti-drone lazer sistemleri.\n"
        "3. Akustik tespit sensörleri.\n"
        "4. Radar tabanlı erken uyarı.\n"
        "5. Eğitimli anti-drone nişancı tüfekleri."
    ),
    "siber harp": (
        "Siber harp temel vektörleri:\n"
        "1. SCADA/ICS sistemlerine saldırı (altyapı sabotajı).\n"
        "2. GPS spoofing — navigasyon yanıltma.\n"
        "3. C2 kesintisi — komuta iletişimini bozmak.\n"
        "4. Dezenformasyon kampanyaları.\n"
        "5. Kritik altyapı koruma: hava boşluğu (air gap) izolasyonu."
    ),
}

# ── Silah Sistemleri Bilgisi ──────────────────────────────────────────────────
WEAPON_SYSTEMS: dict[str, dict] = {
    "bayraktar tb2": {
        "tip": "SIHA (Silahlı İnsansız Hava Aracı)",
        "menzil": "150 km kontrol, 300 km yarıçap",
        "yük": "4x MAM-L veya MAM-C akıllı mikro mühimmat",
        "irtifa": "25.000 feet",
        "dayanıklılık": "27 saat",
        "üretici": "Baykar Makina, Türkiye",
        "kullanıcılar": "Türkiye, Ukrayna, Azerbaycan, 25+ ülke",
    },
    "akıncı": {
        "tip": "Ağır SIHA",
        "menzil": "1.500 km",
        "yük": "1.350 kg",
        "irtifa": "40.000 feet",
        "dayanıklılık": "24 saat",
        "üretici": "Baykar Makina, Türkiye",
    },
    "kipri": {
        "tip": "Loitering Munition (Kamikaze mühimmatı)",
        "aralık": "Hedef arayarak uçar, üzerine çöker",
        "üretici": "Roketsan, Türkiye",
    },
    "hisar": {
        "tip": "HİSAR-A/O/U — Yerli hava savunma sistemi",
        "menzil_a": "15 km",
        "menzil_o": "25 km",
        "menzil_u": "70 km",
        "üretici": "Aselsan / Roketsan",
    },
    "leopard 2": {
        "tip": "Ana Muharebe Tankı",
        "ağırlık": "62 ton",
        "top": "120mm Rheinmetall L55A1",
        "hız": "72 km/h (yolda)",
        "zırh": "Kompozit + reaktif zırh",
        "kullanıcılar": "Türkiye, Almanya, 15+ NATO ülkesi",
    },
}


# ── Ana Sınıf ─────────────────────────────────────────────────────────────────
class MilitaryKnowledge:
    """Askeri bilgi tabanı ve taktik danışman."""

    def get_threat_level(self, level: int) -> str:
        return THREAT_LEVELS.get(level, "Bilinmiyor")

    def get_term(self, term: str) -> str:
        key = term.lower().strip()
        return MILITARY_GLOSSARY.get(key, f"'{term}' terimi bulunamadı.")

    def get_tactic(self, scenario: str) -> str:
        key = scenario.lower().strip()
        # Kısmi eşleşme ara
        for k, v in TACTICS.items():
            if key in k or k in key:
                return v
        return (
            f"'{scenario}' için hazır taktik bulunamadı. "
            "LLM'e sormak için brain modülünü kullanın."
        )

    def get_weapon_info(self, name: str) -> dict[str, Any]:
        key = name.lower().strip()
        for k, v in WEAPON_SYSTEMS.items():
            if key in k or k in key:
                return v
        return {}

    def threat_assessment(self, detected_objects: list[str]) -> dict:
        """
        Görüntüden tespit edilen nesnelere göre tehdit değerlendirmesi yap.
        """
        threats_found = []
        level = 0

        for obj in detected_objects:
            obj_lower = obj.lower()
            if any(w in obj_lower for w in ("gun", "rifle", "knife", "pistol")):
                threats_found.append(obj)
                level = max(level, 3)
            elif any(w in obj_lower for w in ("fire", "smoke")):
                threats_found.append(obj)
                level = max(level, 2)
            elif "person" in obj_lower:
                level = max(level, 1)

        return {
            "threat_level": level,
            "threat_status": self.get_threat_level(level),
            "threats": threats_found,
            "recommendation": self._recommend(level),
        }

    @staticmethod
    def _recommend(level: int) -> str:
        recs = {
            0: "Ortam güvenli. Normal prosedürlere devam.",
            1: "Dikkatli olun. Çevreyi izlemeyi artırın.",
            2: "Savunmaya geçin. Destek çağırın. ROE kontrol edin.",
            3: "KRİTİK! Hemen tahliye veya karşı önlem alın. Komutanı bilgilendirin.",
        }
        return recs.get(level, "Belirsiz durum.")

    def list_terms(self) -> list[str]:
        return sorted(MILITARY_GLOSSARY.keys())

    def list_tactics(self) -> list[str]:
        return sorted(TACTICS.keys())

    def list_weapons(self) -> list[str]:
        return sorted(WEAPON_SYSTEMS.keys())
