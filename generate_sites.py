#!/usr/bin/env python3
"""Generate static pages for each plumbing shop entry using GitHub Pages.

The script reads ``google-2025-12-23.csv`` and produces an ``index`` plus
per-shop detail pages inside ``docs/`` so the repository can be published via
GitHub Pages ("Deploy from a branch" > ``/docs``).
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


DATA_FILE = Path(__file__).with_name("google-2025-12-23.csv")
OUTPUT_DIR = Path("docs")
STORE_DIR = OUTPUT_DIR / "stores"

SERVICE_FIELDS = ["ah5Ghc", "ah5Ghc (2)", "ah5Ghc (3)"]
HIGHLIGHT_FIELDS = ["LDHnMb", "c2ePGf", "c2ePGf (2)", "c2ePGf (3)"]


@dataclass
class Store:
    """Normalized view of a single row from the CSV."""

    name: str
    slug: str
    map_url: str
    category: str | None
    address: str | None
    status: str | None
    hours_note: str | None
    rating: str | None
    review_count: str | None
    phone: str | None
    image_url: str | None
    services: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    sponsored: bool = False
    external_site: str | None = None


def slugify(name: str, existing: set[str], fallback_index: int) -> str:
    """Create a URL-friendly slug.

    The data is primarily in Chinese; we normalize to ASCII so file names stay
    portable. If the stripped ASCII name is empty we fall back to a stable
    ``store-###`` slug.
    """

    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    if not slug:
        slug = f"store-{fallback_index:03d}"

    base = slug
    counter = 2
    while slug in existing:
        slug = f"{base}-{counter}"
        counter += 1
    existing.add(slug)
    return slug


def dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen = set()
    ordered: list[str] = []
    for item in items:
        clean = item.strip()
        if not clean or clean == "·":
            continue
        if clean in seen:
            continue
        seen.add(clean)
        ordered.append(clean)
    return ordered


def clean_review_count(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    return value or None


def load_stores() -> list[Store]:
    stores: list[Store] = []
    used_slugs: set[str] = set()
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            name = row.get("qBF1Pd", "").strip() or f"未命名店家 {index}"
            slug = slugify(name, used_slugs, index)
            store = Store(
                name=name,
                slug=slug,
                map_url=row.get("hfpxzc href", "").strip(),
                category=row.get("W4Efsd", "").strip() or None,
                address=row.get("W4Efsd (3)", "").strip() or None,
                status=row.get("W4Efsd (4)", "").strip() or None,
                hours_note=row.get("W4Efsd (5)", "").strip() or None,
                rating=row.get("MW4etd", "").strip() or None,
                review_count=clean_review_count(row.get("UY7F9")),
                phone=row.get("UsdlK", "").strip() or None,
                image_url=row.get("FQ2IWe src", "").strip() or None,
                services=dedupe_preserve(row.get(field, "") for field in SERVICE_FIELDS),
                highlights=dedupe_preserve(row.get(field, "") for field in HIGHLIGHT_FIELDS),
                sponsored=bool(row.get("jHLihd", "").strip()),
                external_site=row.get("bm892c href", "").strip() or None,
            )
            stores.append(store)
    return stores


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def render_store(store: Store) -> str:
    rating_block = ""
    if store.rating:
        reviews = f"（{store.review_count} 則評論）" if store.review_count else ""
        rating_block = f"<p class=\"rating\">⭐ {html.escape(store.rating)} {reviews}</p>"

    services_block = ""
    if store.services:
        services_list = "\n".join(
            f"            <li>{html.escape(service)}</li>" for service in store.services
        )
        services_block = f"""
          <div class="info-tile">
            <h3>提供服務</h3>
            <ul>
{services_list}
            </ul>
          </div>
        """

    highlights_block = ""
    if store.highlights:
        highlights_list = "\n".join(
            f"            <li>{html.escape(highlight)}</li>" for highlight in store.highlights
        )
        highlights_block = f"""
          <div class="info-tile">
            <h3>服務重點</h3>
            <ul>
{highlights_list}
            </ul>
          </div>
        """

    status_line = " ".join(
        part
        for part in [store.status or "", store.hours_note or ""]
        if part and part != "·"
    )

    phone_block = (
        f"<a class=\"button\" href=\"tel:{html.escape(store.phone)}\">撥打電話</a>"
        if store.phone
        else ""
    )
    map_block = (
        f"<a class=\"button secondary\" href=\"{html.escape(store.map_url)}\" target=\"_blank\" rel=\"noopener\">查看 Google 地圖</a>"
        if store.map_url
        else ""
    )
    external_block = (
        f"<a class=\"button ghost\" href=\"{html.escape(store.external_site)}\" target=\"_blank\" rel=\"noopener\">造訪網站</a>"
        if store.external_site
        else ""
    )

    sponsorship = "<span class=\"pill\">贊助商</span>" if store.sponsored else ""

    return f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(store.name)} | 台中水電行指南</title>
  <link rel=\"stylesheet\" href=\"../styles.css\" />
</head>
<body>
  <header class=\"top-bar\">
    <div class=\"container\">
      <a class=\"back-link\" href=\"../index.html\">← 返回總覽</a>
    </div>
  </header>
  <main class=\"container\">
    <section class=\"store-hero\">
      <div class=\"store-text\">
        <div class=\"eyebrow\">台中水電行</div>
        <h1>{html.escape(store.name)} {sponsorship}</h1>
        {rating_block}
        <p class=\"subtitle\">{html.escape(store.category or '水電服務')}</p>
        <p class=\"status\">{html.escape(status_line or '歡迎來電洽詢')}</p>
        <div class=\"store-actions\">
          {phone_block}
          {map_block}
          {external_block}
        </div>
      </div>
      <div class=\"store-media\">
        <div class=\"image-frame\">
          {f'<img src="{html.escape(store.image_url)}" alt="{html.escape(store.name)}" loading="lazy" />' if store.image_url else '<div class="placeholder">無照片</div>'}
        </div>
        <div class=\"meta\">
          <div><strong>地址：</strong>{html.escape(store.address or '未提供')}</div>
          <div><strong>電話：</strong>{html.escape(store.phone or '未提供')}</div>
        </div>
      </div>
    </section>

    <section class=\"info-grid\">
      <div class=\"info-tile\">
        <h3>營業資訊</h3>
        <p><strong>營業狀態：</strong>{html.escape(store.status or '歡迎洽詢')}</p>
        <p><strong>營業時間：</strong>{html.escape(store.hours_note or '請電洽確認')}</p>
      </div>
      {services_block}
      {highlights_block}
    </section>
  </main>
  <footer class=\"footer\">
    <div class=\"container\">以 Google 地圖公開資訊彙整，實際資訊以店家公告為準。</div>
  </footer>
</body>
</html>
"""


def render_index(stores: list[Store]) -> str:
    cards = []
    for store in stores:
        status_line = " ".join(
            part
            for part in [store.status or "", store.hours_note or ""]
            if part and part != "·"
        )
        rating_text = (
            f"⭐ {html.escape(store.rating)}"
            + (f"（{html.escape(store.review_count)} 則）" if store.review_count else "")
            if store.rating
            else "未提供評分"
        )
        image_tag = (
            f"<img src=\"{html.escape(store.image_url)}\" alt=\"{html.escape(store.name)}\" loading=\"lazy\" />"
            if store.image_url
            else "<div class=\"placeholder\">無照片</div>"
        )
        cards.append(
            f"""
        <article class=\"card\">
          <div class=\"card-media\">{image_tag}</div>
          <div class=\"card-body\">
            <div class=\"eyebrow\">{html.escape(store.category or '水電服務')}</div>
            <h2>{html.escape(store.name)}</h2>
            <p class=\"rating\">{rating_text}</p>
            <p class=\"address\">{html.escape(store.address or '尚未提供地址')}</p>
            <p class=\"status\">{html.escape(status_line or '歡迎來電洽詢')}</p>
            <a class=\"button\" href=\"stores/{html.escape(store.slug)}.html\">查看店家</a>
          </div>
        </article>
        """
        )

    cards_html = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>台中水電行指南 | GitHub Pages</title>
  <link rel=\"stylesheet\" href=\"styles.css\" />
</head>
<body>
  <header class=\"hero\">
    <div class=\"container\">
      <p class=\"eyebrow\">GitHub Pages</p>
      <h1>台中水電行指南</h1>
      <p class=\"lead\">將 CSV 內的 64 間水電行轉成靜態網站，方便在 GitHub Pages 上瀏覽與分享。</p>
    </div>
  </header>
  <main class=\"container\">
    <section class=\"grid\">
{cards_html}
    </section>
  </main>
  <footer class=\"footer\">
    <div class=\"container\">資料來源：Google 地圖公開資訊。</div>
  </footer>
</body>
</html>
"""


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    ensure_output_dirs()
    stores = load_stores()
    stores.sort(key=lambda s: s.name)
    for store in stores:
        html_page = render_store(store)
        write_file(STORE_DIR / f"{store.slug}.html", html_page)
    index_page = render_index(stores)
    write_file(OUTPUT_DIR / "index.html", index_page)


if __name__ == "__main__":
    main()
