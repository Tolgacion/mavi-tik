"""
web.py — Web araştırma motoru

Özellikler:
  - Ürün fiyat/performans karşılaştırması
  - DuckDuckGo arama (API key gerekmez)
  - Haber özeti
  - Genel web scraping
  - Wikipedia özeti

Kurulum:
  pip install requests beautifulsoup4 lxml duckduckgo-search
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("VONSENY.web")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 10


# ── DuckDuckGo Arama ──────────────────────────────────────────────────────────
@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def search_web(query: str, max_results: int = 5) -> list[SearchResult]:
    """DuckDuckGo ile web araması yap (API key gerekmez)."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
        logger.info("Arama '%s': %d sonuç", query, len(results))
        return results
    except ImportError:
        logger.warning("duckduckgo-search kurulu değil: pip install duckduckgo-search")
        return _fallback_search(query, max_results)
    except Exception as exc:
        logger.error("Arama hatası: %s", exc)
        return []


def _fallback_search(query: str, max_results: int = 5) -> list[SearchResult]:
    """DuckDuckGo HTML fallback."""
    try:
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "b": "", "kl": "tr-tr"}
        r = requests.post(url, data=data, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "lxml")
        results = []
        for item in soup.select(".result__body")[:max_results]:
            title_el = item.select_one(".result__title")
            snippet_el = item.select_one(".result__snippet")
            link_el = item.select_one(".result__url")
            results.append(SearchResult(
                title=title_el.get_text(strip=True) if title_el else "",
                url=link_el.get_text(strip=True) if link_el else "",
                snippet=snippet_el.get_text(strip=True) if snippet_el else "",
            ))
        return results
    except Exception as exc:
        logger.error("Fallback arama hatası: %s", exc)
        return []


# ── Wikipedia ────────────────────────────────────────────────────────────────
def wikipedia_summary(topic: str, lang: str = "tr", sentences: int = 5) -> str:
    """Wikipedia'dan özet al (API key gerekmez)."""
    try:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", "Bilgi bulunamadı.")
        # Türkçe yoksa İngilizceye düş
        if lang != "en":
            return wikipedia_summary(topic, lang="en", sentences=sentences)
        return "Wikipedia'da bilgi bulunamadı."
    except Exception as exc:
        logger.error("Wikipedia hatası: %s", exc)
        return f"Hata: {exc}"


# ── Sayfa İçeriği ─────────────────────────────────────────────────────────────
def fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """Web sayfasının temizlenmiş metnini al."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # Gereksiz tagları kaldır
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception as exc:
        logger.error("Sayfa çekme hatası: %s", exc)
        return ""


# ── Ürün Karşılaştırma ────────────────────────────────────────────────────────
@dataclass
class Product:
    name: str
    price: str
    specs: str
    url: str
    source: str


def compare_products(query: str, category: str = "telefon") -> list[Product]:
    """
    Ürün karşılaştırması için arama yap ve sonuçları yapılandır.
    Örnek: compare_products("en iyi telefon 2024 fiyat performans")
    """
    search_query = f"{query} {category} fiyat teknik özellikleri"
    results = search_web(search_query, max_results=8)
    products: list[Product] = []

    for result in results:
        # Fiyat bilgisi çıkarmaya çalış (₺ veya TL içerenlere öncelik ver)
        price = _extract_price(result.snippet)
        products.append(Product(
            name=result.title,
            price=price or "Fiyat bilgisi için tıklayın",
            specs=result.snippet[:200],
            url=result.url,
            source="Web",
        ))

    logger.info("%d ürün bulundu: %s", len(products), query)
    return products


def _extract_price(text: str) -> str:
    """Metin içinden fiyat bilgisi çıkar."""
    patterns = [
        r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s*(?:TL|₺|USD|\$|EUR|€))",
        r"((?:TL|₺|USD|\$|EUR|€)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def find_best_value_phone(budget_tl: int | None = None) -> str:
    """Fiyat-performans en iyi telefonu bul."""
    query = "en iyi fiyat performans telefon 2024"
    if budget_tl:
        query += f" {budget_tl} TL altı"

    results = search_web(query, max_results=5)
    if not results:
        return "Sonuç bulunamadı."

    summary = "📱 **Fiyat-Performans Telefon Önerileri:**\n\n"
    for i, r in enumerate(results[:5], 1):
        summary += f"{i}. **{r.title}**\n   {r.snippet[:150]}\n   🔗 {r.url}\n\n"
    return summary


# ── Haber ─────────────────────────────────────────────────────────────────────
def get_news(topic: str, max_items: int = 5) -> list[dict]:
    """Belirli konuda güncel haberleri getir."""
    results = search_web(f"{topic} haber son dakika", max_results=max_items)
    return [
        {"başlık": r.title, "özet": r.snippet[:200], "url": r.url}
        for r in results
    ]


# ── Araştırma Özeti ────────────────────────────────────────────────────────────
def deep_research(topic: str) -> str:
    """
    Bir konu hakkında derin araştırma yap:
    1. Wikipedia özeti
    2. Web araması
    3. İlk birkaç sayfanın metnini çek
    4. Birleşik özet döndür
    """
    logger.info("Derin araştırma: %s", topic)
    parts: list[str] = []

    # 1. Wikipedia
    wiki = wikipedia_summary(topic)
    if wiki and "bulunamadı" not in wiki:
        parts.append(f"📖 Wikipedia:\n{wiki}\n")

    # 2. Web araması
    results = search_web(topic, max_results=5)
    if results:
        parts.append("🌐 Web Kaynakları:")
        for r in results[:3]:
            page_text = fetch_page_text(r.url, max_chars=800) if r.url.startswith("http") else ""
            content = page_text if page_text else r.snippet
            parts.append(f"\n• **{r.title}**\n  {content[:300]}\n  ({r.url})")

    return "\n".join(parts) if parts else "Araştırma sonucu bulunamadı."
