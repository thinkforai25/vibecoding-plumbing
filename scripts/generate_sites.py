"""Generate static pages for each plumbing/electrical shop.

Run this script to transform ``google-2025-12-23.csv`` into a GitHub Pages
static site under ``docs``:

    python scripts/generate_sites.py
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Iterable, List

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "google-2025-12-23.csv"
DOCS_DIR = ROOT_DIR / "docs"


@dataclass
class Store:
    slug: str
    name: str
    map_url: str | None
    rating: str | None
    reviews: str | None
    category: str | None
    address: str | None
    status: str | None
    hours: str | None
    phone: str | None
    image_url: str | None
    badges: List[str]
    highlights: List[str]
    ad_link: str | None


def _clean(value: str | None) -> str:
    """Return a tidy string without bullet characters or leading/trailing space."""

    if not value:
        return ""
    return value.replace("·", "").strip()


def _collect(row: dict, keys: Iterable[str]) -> List[str]:
    values: List[str] = []
    for key in keys:
        cleaned = _clean(row.get(key))
        if cleaned:
            values.append(cleaned)
    return values


def _slugify(name: str, existing: set[str], fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    base = slug or fallback
    candidate = base
    suffix = 2
    while candidate in existing:
        candidate = f"{base}-{suffix}"
        suffix += 1
    existing.add(candidate)
    return candidate


def _parse_stores() -> List[Store]:
    existing_slugs: set[str] = set()
    stores: List[Store] = []

    with DATA_FILE.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for index, row in enumerate(reader, start=1):
            name = row.get("qBF1Pd", "").strip() or f"未命名店家 {index}"
            slug = _slugify(name, existing_slugs, fallback=f"store-{index}")

            store = Store(
                slug=slug,
                name=name,
                map_url=_clean(row.get("hfpxzc href")) or None,
                rating=_clean(row.get("MW4etd")) or None,
                reviews=_clean(row.get("UY7F9")).strip("()"),
                category=_clean(row.get("W4Efsd")) or None,
                address=_clean(row.get("W4Efsd (3)")) or None,
                status=_clean(row.get("W4Efsd (4)")) or None,
                hours=_clean(row.get("W4Efsd (5)")) or None,
                phone=_clean(row.get("UsdlK")) or None,
                image_url=_clean(row.get("FQ2IWe src")) or None,
                badges=_collect(
                    row,
                    (
                        "ah5Ghc",
                        "M4A5Cf",
                        "ah5Ghc (2)",
                        "M4A5Cf (2)",
                        "ah5Ghc (3)",
                    ),
                ),
                highlights=_collect(
                    row,
                    (
                        "LDHnMb",
                        "c2ePGf",
                        "c2ePGf (2)",
                        "c2ePGf (3)",
                        "W4Efsd (7)",
                        "doJOZc",
                    ),
                ),
                ad_link=_clean(row.get("bm892c href")) or None,
            )

            stores.append(store)

    return stores


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_index(stores: List[Store]) -> str:
    card_items = []
    for store in stores:
        card_items.append(
            Template(
                """
        <article class="card" data-name="$name" data-category="$category" data-address="$address">
            <div class="card-image" style="background-image:url('$image');" aria-hidden="true"></div>
            <div class="card-body">
                <div class="card-header">
                    <h2>$name</h2>
                    <p class="card-meta">$category_label</p>
                </div>
                <p class="card-rating">$rating ⭐ | $reviews 則評論</p>
                <p class="card-address">📍 $address_label</p>
                <p class="card-status">$status $hours</p>
                <div class="card-actions">
                    <a class="button primary" href="stores/$slug.html">查看店家</a>
                    $map_button
                </div>
            </div>
        </article>
        """
            ).substitute(
                name=html.escape(store.name),
                category=html.escape(store.category or ""),
                address=html.escape(store.address or ""),
                image=html.escape(store.image_url or ""),
                category_label=html.escape(store.category or "服務類別未提供"),
                rating=html.escape(store.rating or "無評分"),
                reviews=html.escape(store.reviews or "0"),
                address_label=html.escape(store.address or "未提供地址"),
                status=html.escape(store.status or "營業資訊未提供"),
                hours=html.escape(store.hours or ""),
                slug=store.slug,
                map_button=(
                    f'<a class="button secondary" href="{html.escape(store.map_url)}" target="_blank" rel="noopener">Google 地圖</a>'
                    if store.map_url
                    else ""
                ),
            )
        )

    cards = "".join(card_items)

    template = Template(
        """
<!doctype html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>水電行索引 | GitHub Pages</title>
    <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
    <header class="hero">
        <div class="hero__content">
            <p class="eyebrow">台中水電資訊匯總</p>
            <h1>水電行一覽</h1>
            <p class="lede">在 GitHub Pages 上快速瀏覽 64 家水電行，查看評價、地址、營業狀態與聯絡方式。</p>
            <div class="search">
                <label for="search-box">搜尋店家</label>
                <input id="search-box" type="search" placeholder="輸入名稱、地址或服務關鍵字" autocomplete="off">
                <p class="search__hint">即時篩選卡片以找到附近的水電服務。</p>
            </div>
        </div>
    </header>

    <main class="content">
        <section class="summary">
            <p id="result-count">共 $count 家店家</p>
            <a class="button secondary" href="https://github.com/" target="_blank" rel="noopener">GitHub Pages 說明</a>
        </section>
        <section id="cards" class="card-grid">
            $cards
        </section>
        <p id="empty-state" class="empty" hidden>找不到符合的店家，請嘗試其他關鍵字。</p>
    </main>

    <script>
    const cards = Array.from(document.querySelectorAll('.card'));
    const searchBox = document.getElementById('search-box');
    const resultCount = document.getElementById('result-count');
    const emptyState = document.getElementById('empty-state');

    function normalize(text) {
        return text.toLowerCase();
    }

    function filterCards() {
        const term = normalize(searchBox.value.trim());
        let visible = 0;
        cards.forEach(card => {
            const haystack = [
                card.dataset.name,
                card.dataset.category,
                card.dataset.address,
            ].join(' ').toLowerCase();
            const match = !term || haystack.includes(term);
            card.style.display = match ? '' : 'none';
            if (match) visible += 1;
        });
        resultCount.textContent = '共 ' + visible + ' 家店家';
        emptyState.hidden = visible !== 0;
    }

    searchBox.addEventListener('input', filterCards);
    </script>
</body>
</html>
"""
    )

    return template.substitute(count=len(stores), cards=cards)


def _render_store(store: Store) -> str:
    badges = "".join(f'<span class="badge">{html.escape(badge)}</span>' for badge in store.badges)
    highlights = "".join(f"<li>{html.escape(text)}</li>" for text in store.highlights)

    map_button = (
        f'<a class="button secondary" href="{html.escape(store.map_url)}" target="_blank" rel="noopener">在 Google 地圖查看</a>'
        if store.map_url
        else ""
    )

    phone_link = (
        f'<a class="button primary" href="tel:{html.escape(store.phone)}">撥打 {html.escape(store.phone)}</a>'
        if store.phone
        else ""
    )

    ad_link = (
        f'<a class="button tertiary" href="{html.escape(store.ad_link)}" target="_blank" rel="noopener">造訪網站</a>'
        if store.ad_link
        else ""
    )

    template = Template(
        """
<!doctype html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>$title | 水電行介紹</title>
    <link rel="stylesheet" href="../assets/styles.css">
</head>
<body>
    <nav class="top-bar">
        <a href="../index.html" class="back-link">← 返回列表</a>
        <span class="brand">GitHub Pages</span>
    </nav>
    <header class="store-hero">
        <div class="store-hero__image" style="background-image:url('$image');"></div>
        <div class="store-hero__body">
            <p class="eyebrow">$category</p>
            <h1>$title</h1>
            <p class="lede">$address</p>
            <div class="meta">
                <span>⭐ $rating</span>
                <span>$reviews 則評論</span>
                <span>$status</span>
                <span>$hours</span>
            </div>
            <div class="actions">
                $phone_link
                $map_button
                $ad_link
            </div>
            <div class="badges">$badges</div>
        </div>
    </header>

    <main class="content content--narrow">
        <section class="panel">
            <h2>店家重點</h2>
            $highlights
        </section>
        <section class="panel">
            <h2>聯絡資訊</h2>
            <dl class="info">
                <div><dt>電話</dt><dd>$phone</dd></div>
                <div><dt>地址</dt><dd>$address</dd></div>
                <div><dt>Google 地圖</dt><dd>$map_link</dd></div>
                <div><dt>廣告/官網</dt><dd>$ad_link_short</dd></div>
            </dl>
        </section>
    </main>
</body>
</html>
"""
    )

    return template.substitute(
        title=html.escape(store.name),
        category=html.escape(store.category or "服務類別未提供"),
        address=html.escape(store.address or "未提供地址"),
        image=html.escape(store.image_url or ""),
        rating=html.escape(store.rating or "無評分"),
        reviews=html.escape(store.reviews or "0"),
        status=html.escape(store.status or "營業資訊未提供"),
        hours=html.escape(store.hours or ""),
        phone_link=phone_link,
        map_button=map_button,
        ad_link=ad_link,
        badges=badges,
        highlights=f'<ul class="highlight-list">{highlights}</ul>' if highlights else "<p>尚無補充描述。</p>",
        phone=html.escape(store.phone or "未提供"),
        map_link=(
            f'<a href="{html.escape(store.map_url)}" target="_blank" rel="noopener">前往</a>'
            if store.map_url
            else "未提供"
        ),
        ad_link_short=(
            f'<a href="{html.escape(store.ad_link)}" target="_blank" rel="noopener">造訪</a>'
            if store.ad_link
            else "未提供"
        ),
    )


def main() -> None:
    stores = _parse_stores()

    _write_file(DOCS_DIR / "index.html", _render_index(stores))
    for store in stores:
        _write_file(DOCS_DIR / "stores" / f"{store.slug}.html", _render_store(store))

    print(f"Generated {len(stores)} store pages in {DOCS_DIR}/stores")


if __name__ == "__main__":
    main()
