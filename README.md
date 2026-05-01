# JARVIS — Yapay Zeka Asistanı 🤖

Iron Man'in JARVIS'inden ilham alınan, Türkçe destekli yapay zeka asistanı.

## Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# OpenAI API anahtarını ayarla (isteğe bağlı — tam AI için gerekli)
export OPENAI_API_KEY="sk-..."
```

## Çalıştırma

```bash
python jarvis.py
```

## Özellikler

| Komut | Açıklama |
|-------|----------|
| `saat kaç` | Mevcut saati söyler |
| `bugün ne günü` | Tarih ve günü söyler |
| `sistem bilgisi` | İşletim sistemi bilgisi verir |
| `şaka yap` | Komik bir şaka söyler |
| `yardım` | Tüm komutları listeler |
| `çıkış` | Programı kapatır |
| *herhangi soru* | OpenAI ile akıllıca yanıtlar |

## Notlar

- `OPENAI_API_KEY` olmadan da temel komutlar çalışır.
- OpenAI API anahtarı ile her türlü soruyu yanıtlayabilir.
- Konuşma geçmişi oturum boyunca hatırlanır.
