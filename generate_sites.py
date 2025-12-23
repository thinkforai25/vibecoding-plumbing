"""Generate static GitHub Pages for each plumbing business in the CSV file."""
from __future__ import annotations

import csv
import html
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

DATA_FILE = Path("google-2025-12-23.csv")
DOCS_DIR = Path("docs")
ASSETS_DIR = DOCS_DIR / "assets"
SHOPS_DIR = DOCS_DIR / "shops"
PLACEHOLDER_IMAGE = "https://placehold.co/800x500?text=Plumbing+Service"


@dataclass
class Shop:
    slug: str
    name: str
    map_url: str
    rating: float | None
    review_count: int | None
    category: str | None
    address: str | None
    status: str | None
    hours: str | None
    phone: str | None
    image_url: str | None
    highlights: List[str] = field(default_factory=list)
    sponsored: bool = False


def slugify(name: str, fallback_index: int, existing: set[str]) -> str:
    """Create a unique, URL-friendly slug for each shop."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    base = ascii_slug or f"shop-{fallback_index+1}"

    candidate = base
    suffix = 2
    while candidate in existing:
        candidate = f"{base}-{suffix}"
        suffix += 1

    existing.add(candidate)
    return candidate


def parse_rating(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_reviews(value: str) -> int | None:
    if not value:
        return None
    cleaned = value.strip().strip("()")
    try:
        return int(cleaned.replace(",", ""))
    except ValueError:
        return None


def tidy(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip().lstrip("·").strip()
    return cleaned or None


def collect_highlights(raw_values: Iterable[str]) -> tuple[list[str], bool]:
    highlights: list[str] = []
    sponsored = False
    for value in raw_values:
        cleaned = tidy(value)
        if not cleaned or cleaned == "·":
            continue
        if "贊助商廣告" in cleaned:
            sponsored = True
            continue
        if cleaned not in highlights:
            highlights.append(cleaned)
    return highlights, sponsored


def build_shops() -> list[Shop]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Cannot find data file: {DATA_FILE}")

    used_slugs: set[str] = set()
    shops: list[Shop] = []

    with DATA_FILE.open(encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        for index, row in enumerate(reader):
            name = row[1].strip() if len(row) > 1 and row[1].strip() else f"未命名店家-{index+1}"
            slug = slugify(name, index, used_slugs)
            highlights, sponsored = collect_highlights(row[11:])
            shops.append(
                Shop(
                    slug=slug,
                    name=name,
                    map_url=tidy(row[0]) or "#",
                    rating=parse_rating(row[2]) if len(row) > 2 else None,
                    review_count=parse_reviews(row[3]) if len(row) > 3 else None,
                    category=tidy(row[4]) if len(row) > 4 else None,
                    address=tidy(row[5]) if len(row) > 5 else None,
                    status=tidy(row[6]) if len(row) > 6 else None,
                    hours=tidy(row[7]) if len(row) > 7 else None,
                    phone=tidy(row[9]) if len(row) > 9 else None,
                    image_url=tidy(row[10]) if len(row) > 10 else None,
                    highlights=highlights,
                    sponsored=sponsored,
                )
            )
    return shops


def ensure_dirs() -> None:
    for path in (ASSETS_DIR, SHOPS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_stylesheet() -> None:
    styles = """
:root {
  color-scheme: light;
  --bg: #f7f8fb;
  --card: #ffffff;
  --primary: #0c6cf2;
  --accent: #0b9d79;
  --text: #1f2933;
  --muted: #5f6b76;
  --border: #e5e7eb;
  --shadow: 0 20px 45px rgba(31, 41, 51, 0.08);
  font-family: "Noto Sans TC", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
}

a { color: inherit; }

.page {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.hero {
  background: linear-gradient(120deg, #0c6cf2, #0ab1c5);
  color: #fff;
  padding: 64px 24px 48px;
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.2), transparent 35%),
              radial-gradient(circle at 80% 10%, rgba(255, 255, 255, 0.18), transparent 30%),
              radial-gradient(circle at 40% 80%, rgba(255, 255, 255, 0.12), transparent 30%);
  pointer-events: none;
}

.hero__content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero__title {
  margin: 0 0 12px;
  font-size: clamp(28px, 3vw, 38px);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.hero__subtitle {
  margin: 0 0 24px;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.92);
}

.hero__stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.pill {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  padding: 10px 14px;
  border-radius: 999px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.content {
  max-width: 1200px;
  margin: -40px auto 48px;
  padding: 0 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.card {
  background: var(--card);
  border-radius: 16px;
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
}

.card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  background: #dfe6f0;
}

.card__body {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 14px;
}

.badge {
  background: #eef2ff;
  color: #243b77;
  padding: 6px 10px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 13px;
}

.tag-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.button {
  text-decoration: none;
  background: var(--primary);
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px;
  font-weight: 700;
  box-shadow: 0 10px 30px rgba(12, 108, 242, 0.25);
  text-align: center;
  flex: 1;
}

.button.secondary {
  background: var(--accent);
  box-shadow: 0 10px 30px rgba(11, 157, 121, 0.22);
}

.footer {
  padding: 18px;
  text-align: center;
  color: var(--muted);
  border-top: 1px solid var(--border);
  background: #fff;
}

.detail-header {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
  background: var(--card);
  padding: 20px;
  border-radius: 18px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}

.detail-header img {
  width: 100%;
  border-radius: 14px;
  height: 100%;
  object-fit: cover;
}

.detail-body {
  display: grid;
  gap: 12px;
}

.stat-line {
  display: flex;
  gap: 12px;
  color: var(--muted);
  font-size: 15px;
}

.tag-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 820px) {
  .detail-header {
    grid-template-columns: 1fr;
  }
}
"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "styles.css").write_text(styles, encoding="utf-8")


def render_badges(shop: Shop) -> str:
    badges = []
    if shop.category:
        badges.append(f"<span class=\"badge\">{html.escape(shop.category)}</span>")
    if shop.status:
        badges.append(f"<span class=\"badge\">{html.escape(shop.status)}</span>")
    if shop.hours:
        badges.append(f"<span class=\"badge\">{html.escape(shop.hours)}</span>")
    if shop.sponsored:
        badges.append("<span class=\"badge\">贊助商</span>")
    return "\n        ".join(badges)


def render_tags(shop: Shop, limit: int | None = None) -> str:
    tags = shop.highlights if limit is None else shop.highlights[:limit]
    if not tags:
        return ""
    items = "".join(f"<span class=\"badge\">{html.escape(tag)}</span>" for tag in tags)
    return f"<div class=\"tag-row\">{items}</div>"


def render_card(shop: Shop) -> str:
    rating = f"⭐ {shop.rating:.1f}" if shop.rating is not None else "尚無評分"
    reviews = f"{shop.review_count} 則評論" if shop.review_count is not None else "評論數未知"
    badges = render_badges(shop)
    tags = render_tags(shop, limit=3)
    phone_label = html.escape(shop.phone) if shop.phone else "尚無電話"
    image = shop.image_url or PLACEHOLDER_IMAGE

    return f"""
<article class=\"card\">
  <img src=\"{html.escape(image)}\" alt=\"{html.escape(shop.name)}\"> 
  <div class=\"card__body\">
    <h2 class=\"name\">{html.escape(shop.name)}</h2>
    <div class=\"meta\">{rating} · {reviews}</div>
    <div class=\"meta\">{html.escape(shop.address or '地址未提供')}</div>
    <div class=\"tag-row\">{badges}</div>
    {tags}
    <div class=\"actions\">
      <a class=\"button\" href=\"shops/{shop.slug}/index.html\">查看店家頁面</a>
      <a class=\"button secondary\" href=\"{html.escape(shop.map_url)}\" target=\"_blank\" rel=\"noopener\">Google 地圖</a>
    </div>
    <div class=\"meta\">☎ {phone_label}</div>
  </div>
</article>
"""


def write_index(shops: list[Shop]) -> None:
    cards = "\n".join(render_card(shop) for shop in shops)
    index_html = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>台中水電行索引</title>
  <link rel=\"stylesheet\" href=\"assets/styles.css\">
</head>
<body class=\"page\">
  <header class=\"hero\">
    <div class=\"hero__content\">
      <p class=\"pill\">GitHub Pages 專案</p>
      <h1 class=\"hero__title\">台中水電服務地圖</h1>
      <p class=\"hero__subtitle\">共 {len(shops)} 間水電行，每間都有專屬的簡介頁面與聯絡方式。</p>
      <div class=\"hero__stats\">
        <span class=\"pill\">⚙️ 營業狀態一覽</span>
        <span class=\"pill\">📞 電話、地圖、特色服務</span>
        <span class=\"pill\">🛠️ GitHub Pages 可直接部署</span>
      </div>
    </div>
  </header>
  <main class=\"content\">
    <section class=\"grid\">
      {cards}
    </section>
  </main>
  <footer class=\"footer\">由 CSV 資料自動產生，適用於 GitHub Pages。</footer>
</body>
</html>
"""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")


def write_shop_page(shop: Shop) -> None:
    badges = render_badges(shop)
    tags = render_tags(shop)
    rating = f"⭐ {shop.rating:.1f}" if shop.rating is not None else "尚無評分"
    reviews = f"{shop.review_count} 則評論" if shop.review_count is not None else "評論數未知"
    phone_link = f"tel:{shop.phone}" if shop.phone else None
    phone_label = html.escape(shop.phone) if shop.phone else "尚無電話資訊"
    image = shop.image_url or PLACEHOLDER_IMAGE
    category_chip = (
        f"<span class=\"pill\">{html.escape(shop.category)}</span>" if shop.category else ""
    )

    actions: list[str] = []
    if phone_link:
        actions.append(f"<a class=\"button\" href=\"{phone_link}\">立即撥打</a>")
    actions.append(
        f"<a class=\"button secondary\" href=\"{html.escape(shop.map_url)}\" target=\"_blank\" rel=\"noopener\">在 Google 地圖開啟</a>"
    )
    action_block = "\n        ".join(actions)
    highlight_block = tags or "<p class=\"meta\">尚無特色資料</p>"

    html_body = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(shop.name)} | 台中水電行</title>
  <link rel=\"stylesheet\" href=\"../assets/styles.css\">
</head>
<body class=\"page\">
  <header class=\"hero\">
    <div class=\"hero__content\">
      <p class=\"pill\">獨立店家頁面</p>
      <h1 class=\"hero__title\">{html.escape(shop.name)}</h1>
      <p class=\"hero__subtitle\">{html.escape(shop.address or '尚無地址資料')}</p>
      <div class=\"hero__stats\">
        <span class=\"pill\">{rating}</span>
        <span class=\"pill\">{reviews}</span>
        {category_chip}
      </div>
    </div>
  </header>
  <main class=\"content\">
    <div class=\"detail-header\">
      <img src=\"{html.escape(image)}\" alt=\"{html.escape(shop.name)}\">
      <div class=\"detail-body\">
        <h2 class=\"name\">{html.escape(shop.name)}</h2>
        <div class=\"meta\">{html.escape(shop.status or '營業資訊未提供')}</div>
        <div class=\"tag-row\">{badges}</div>
        <div class=\"stat-line\">📍 {html.escape(shop.address or '尚無地址')}</div>
        <div class=\"stat-line\">☎ {phone_label}</div>
        <div class=\"stat-line\">🔗 <a href=\"{html.escape(shop.map_url)}\" target=\"_blank\" rel=\"noopener\">前往 Google 地圖</a></div>
        <div class=\"actions\">{action_block}</div>
      </div>
    </div>
    <section style=\"margin-top:24px;\">
      <h3>特色與服務</h3>
      {highlight_block}
    </section>
    <p style=\"margin-top:18px;\"><a href=\"../index.html\">← 返回店家列表</a></p>
  </main>
  <footer class=\"footer\">由 CSV 資料自動產生，適用於 GitHub Pages。</footer>
</body>
</html>
"""

    shop_dir = SHOPS_DIR / shop.slug
    shop_dir.mkdir(parents=True, exist_ok=True)
    (shop_dir / "index.html").write_text(html_body, encoding="utf-8")


def main() -> None:
    shops = build_shops()
    ensure_dirs()
    write_stylesheet()
    write_index(shops)
    for shop in shops:
        write_shop_page(shop)
    print(f"Generated {len(shops)} shop pages in {SHOPS_DIR}/")


if __name__ == "__main__":
    main()
