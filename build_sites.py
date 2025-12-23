#!/usr/bin/env python3
"""
Build static GitHub Pages for every plumbing and electrical business listed in
``google-2025-12-23.csv``.

Running this script will regenerate the ``docs`` directory, including a
summary index page and an independent detail page for each business.
"""
from __future__ import annotations

import csv
import html
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "google-2025-12-23.csv"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
BUSINESS_DIR = DOCS_DIR / "businesses"

STYLE_CONTENT = """
:root {
  --bg: #0f172a;
  --surface: #111827;
  --card: #131c2f;
  --accent: #38bdf8;
  --accent-strong: #0ea5e9;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --border: #1f2937;
  --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  --radius: 14px;
  --radius-small: 10px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.05), transparent 35%),
              radial-gradient(circle at 80% 0%, rgba(14, 165, 233, 0.07), transparent 30%),
              var(--bg);
  color: var(--text);
  font-family: 'Inter', 'Noto Sans TC', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh;
}

header {
  padding: 36px 24px 12px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.title {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0.5px;
}

.subtitle {
  margin: 6px 0 0;
  color: var(--muted);
}

.tagline {
  padding: 8px 12px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: var(--radius-small);
  color: #bae6fd;
  font-size: 14px;
}

main {
  max-width: 1200px;
  margin: 0 auto 48px;
  padding: 0 24px 24px;
}

.filter-bar {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  position: sticky;
  top: 12px;
  z-index: 5;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  color: var(--muted);
  font-size: 13px;
}

input[type="search"],
select {
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius-small);
  border: 1px solid var(--border);
  background: #0b1220;
  color: var(--text);
  font-size: 15px;
}

input[type="search"]::placeholder {
  color: #60708c;
}

.grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow);
  transition: transform 150ms ease, box-shadow 150ms ease, border 150ms ease;
}

.card:hover {
  transform: translateY(-2px);
  border-color: rgba(56, 189, 248, 0.4);
  box-shadow: 0 14px 40px rgba(14, 165, 233, 0.15);
}

.card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  background: #0b1220;
}

.card-body {
  padding: 16px;
  display: grid;
  gap: 10px;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(74, 222, 128, 0.12);
  color: #bbf7d0;
  font-weight: 600;
  font-size: 13px;
  border: 1px solid rgba(74, 222, 128, 0.35);
}

.status.neutral {
  background: rgba(148, 163, 184, 0.1);
  color: var(--muted);
  border-color: rgba(148, 163, 184, 0.3);
}

.status.open-24 {
  background: rgba(56, 189, 248, 0.14);
  color: #bae6fd;
  border-color: rgba(56, 189, 248, 0.35);
}

.rating {
  color: #fcd34d;
  font-weight: 700;
}

h2 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 0.1px;
}

.meta,
.address {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 10px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #c2e6fb;
  border-radius: 999px;
  font-size: 12px;
}

.actions {
  margin-top: auto;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.button,
.button-ghost,
.button-call {
  padding: 10px 14px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  border: 1px solid transparent;
  transition: transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}

.button {
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #0b1220;
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.25);
}

.button-ghost {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--text);
}

.button-call {
  background: rgba(74, 222, 128, 0.14);
  border-color: rgba(74, 222, 128, 0.3);
  color: #befae2;
}

.button:hover,
.button-ghost:hover,
.button-call:hover {
  transform: translateY(-1px);
  opacity: 0.95;
}

.stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 12px 14px;
  border-radius: 12px;
  color: var(--muted);
  font-size: 14px;
}

.stat-card strong {
  color: var(--text);
  font-size: 16px;
}

.hero {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(14, 165, 233, 0.08)),
              radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.14), transparent 40%),
              var(--surface);
  padding: 32px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.detail-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 18px;
  margin-top: 18px;
}

.detail-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow);
}

@media (max-width: 900px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

.detail-meta {
  display: grid;
  gap: 10px;
}

.meta-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: var(--muted);
}

.meta-row span {
  color: var(--text);
}

.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.back-link {
  text-decoration: none;
  color: var(--muted);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.back-link:hover {
  color: var(--text);
}
"""

SCRIPT_CONTENT = """
(() => {
  const search = document.querySelector('#search');
  const statusFilter = document.querySelector('#status-filter');
  const categoryFilter = document.querySelector('#category-filter');
  const cards = Array.from(document.querySelectorAll('[data-name]'));
  const visibleCount = document.querySelector('[data-visible-count]');

  const normalize = (text) => text.toLowerCase();

  function matches(card) {
    const keyword = normalize(search.value.trim());
    const statusValue = statusFilter.value;
    const categoryValue = categoryFilter.value;
    const haystack = [
      card.dataset.name,
      card.dataset.address,
      card.dataset.category,
      card.dataset.features,
    ].join(' ').toLowerCase();

    const keywordMatch = !keyword || haystack.includes(keyword);
    const statusMatch = !statusValue || card.dataset.status === statusValue;
    const categoryMatch = !categoryValue || card.dataset.category === categoryValue;

    return keywordMatch && statusMatch && categoryMatch;
  }

  function applyFilters() {
    let count = 0;
    cards.forEach((card) => {
      if (matches(card)) {
        card.style.display = '';
        count += 1;
      } else {
        card.style.display = 'none';
      }
    });

    if (visibleCount) {
      visibleCount.textContent = count;
    }
  }

  if (search) search.addEventListener('input', applyFilters);
  if (statusFilter) statusFilter.addEventListener('change', applyFilters);
  if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);

  applyFilters();
})();
"""

@dataclass
class Business:
  slug: str
  name: str
  map_url: str
  rating: Optional[float]
  review_count: Optional[int]
  category: str
  address: str
  status: Optional[str]
  hours: Optional[str]
  phone: Optional[str]
  image_url: Optional[str]
  features: List[str]

  @property
  def status_class(self) -> str:
    if not self.status:
      return "neutral"
    if "24" in self.status:
      return "open-24"
    if "營業" in self.status:
      return ""
    return "neutral"

  @property
  def formatted_rating(self) -> str:
    if self.rating is None:
      return "--"
    stars = "★" * round(self.rating)
    reviews = f"（{self.review_count} 則評論）" if self.review_count else ""
    return f"{self.rating:.1f} {stars} {reviews}".strip()


def slugify(name: str, fallback_index: int) -> str:
  base = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", name).strip("-")
  slug = base or f"business-{fallback_index}"
  return slug


def clean_feature(cell: str) -> Optional[str]:
  text = cell.strip().strip("·").strip()
  if not text:
    return None
  if text.startswith("http"):
    return None
  if "廣告" in text:
    return None
  if len(text) <= 2 and all(not (ch.isalnum() or "\u4e00" <= ch <= "\u9fff") for ch in text):
    return None
  if all(unicodedata.category(ch).startswith("S") for ch in text):
    return None
  return text


def parse_businesses() -> List[Business]:
  businesses: List[Business] = []
  seen_slugs = set()
  with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    next(reader, None)  # header
    for idx, row in enumerate(reader, start=1):
      if not row or len(row) < 10:
        continue

      name = row[1].strip() or f"未命名店家 {idx}"
      slug = slugify(name, idx)
      if slug in seen_slugs:
        suffix = 2
        while f"{slug}-{suffix}" in seen_slugs:
          suffix += 1
        slug = f"{slug}-{suffix}"
      seen_slugs.add(slug)

      rating: Optional[float]
      try:
        rating = float(row[2]) if row[2].strip() else None
      except ValueError:
        rating = None

      review_text = row[3].strip()
      review_count: Optional[int] = None
      if review_text:
        digits = re.sub(r"[^0-9]", "", review_text)
        review_count = int(digits) if digits else None

      features = []
      for cell in row[11:]:
        cleaned = clean_feature(cell)
        if cleaned and cleaned not in features:
          features.append(cleaned)

      hours_text = row[7].replace("·", "").strip()
      business = Business(
        slug=slug,
        name=name,
        map_url=row[0].strip(),
        rating=rating,
        review_count=review_count,
        category=row[4].strip(),
        address=row[5].strip(),
        status=row[6].strip() or None,
        hours=hours_text or None,
        phone=row[9].strip() or None,
        image_url=row[10].strip() or None,
        features=features,
      )
      businesses.append(business)
  return businesses


def reset_docs_directory() -> None:
  if DOCS_DIR.exists():
    shutil.rmtree(DOCS_DIR)
  BUSINESS_DIR.mkdir(parents=True, exist_ok=True)
  ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def write_assets() -> None:
  (ASSETS_DIR / "style.css").write_text(STYLE_CONTENT, encoding="utf-8")
  (ASSETS_DIR / "main.js").write_text(SCRIPT_CONTENT, encoding="utf-8")


def build_index_page(businesses: List[Business]) -> None:
  categories = sorted({b.category for b in businesses if b.category})
  statuses = sorted({b.status for b in businesses if b.status})
  cards = "\n".join(render_card(b) for b in businesses)

  status_options = "\n".join(
    f'<option value="{html.escape(status)}">{html.escape(status)}</option>' for status in statuses
  )
  category_options = "\n".join(
    f'<option value="{html.escape(cat)}">{html.escape(cat)}</option>' for cat in categories
  )

  html_content = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>水電行獨立網站總覽</title>
  <link rel=\"stylesheet\" href=\"./assets/style.css\" />
</head>
<body>
  <header>
    <div class=\"header-top\">
      <div>
        <p class=\"tagline\">GitHub Pages 自動生成 · {len(businesses)} 家店家一次整理</p>
        <h1 class=\"title\">台中水電行獨立網站總覽</h1>
        <p class=\"subtitle\">點擊卡片可以前往每一間水電行的專屬頁面，或直接開啟 Google 地圖導航。</p>
      </div>
      <div class=\"stat-card\">
        <div>目前網站數量</div>
        <strong data-visible-count>{len(businesses)}</strong>
      </div>
    </div>
  </header>

  <main>
    <section class=\"filter-bar\">
      <div class=\"filter-group\">
        <label for=\"search\">搜尋店名、地址或服務</label>
        <input id=\"search\" type=\"search\" placeholder=\"輸入關鍵字\" />
      </div>
      <div class=\"filter-group\">
        <label for=\"status-filter\">營業狀態</label>
        <select id=\"status-filter\">
          <option value=\"\">全部</option>
          {status_options}
        </select>
      </div>
      <div class=\"filter-group\">
        <label for=\"category-filter\">服務類型</label>
        <select id=\"category-filter\">
          <option value=\"\">全部</option>
          {category_options}
        </select>
      </div>
    </section>

    <section class=\"grid\">
      {cards}
    </section>
  </main>
  <script src=\"./assets/main.js\"></script>
</body>
</html>
"""
  (DOCS_DIR / "index.html").write_text(html_content, encoding="utf-8")


def render_card(b: Business) -> str:
  features_preview = b.features[:4]
  feature_chips = "".join(
    f'<span class="chip">{html.escape(feature)}</span>' for feature in features_preview
  )
  status_text = html.escape(b.status or "營業資訊未提供")
  status_class = b.status_class
  rating_text = html.escape(b.formatted_rating)
  category = html.escape(b.category)
  address = html.escape(b.address)
  name = html.escape(b.name)
  phone_link = f'<a class="button-call" href="tel:{html.escape(b.phone)}">電話聯絡</a>' if b.phone else ""
  image_tag = (
    f'<img src="{html.escape(b.image_url or "https://via.placeholder.com/400x250?text=Plumbing")}" '
    f'alt="{name}" loading="lazy" />'
  )
  return f"""<article class=\"card\" data-name=\"{name}\" data-category=\"{category}\" data-address=\"{address}\" data-features=\"{html.escape(' '.join(b.features))}\" data-status=\"{html.escape(b.status or '')}\">\n  {image_tag}\n  <div class=\"card-body\">\n    <div class=\"card-header\">\n      <span class=\"status {status_class}\">{status_text}</span>\n      <span class=\"rating\">{rating_text}</span>\n    </div>\n    <h2>{name}</h2>\n    <p class=\"meta\">{category}</p>\n    <p class=\"address\">{address}</p>\n    <div class=\"chips\">{feature_chips}</div>\n    <div class=\"actions\">\n      <a class=\"button\" href=\"./businesses/{b.slug}/index.html\">查看專屬頁</a>\n      <a class=\"button-ghost\" href=\"{html.escape(b.map_url)}\" target=\"_blank\" rel=\"noreferrer\">Google 地圖</a>\n      {phone_link}\n    </div>\n  </div>\n</article>"""


def build_detail_page(b: Business) -> None:
  features = b.features or ["尚未提供額外服務資訊"]
  feature_items = "\n".join(f'<span class="chip">{html.escape(feature)}</span>' for feature in features)
  phone_row = (
    f'<div class="meta-row">📞 <span><a class="back-link" href="tel:{html.escape(b.phone)}">{html.escape(b.phone)}</a></span></div>'
    if b.phone else "<div class=\"meta-row\">📞 <span>未提供電話</span></div>"
  )
  rating_text = html.escape(b.formatted_rating)
  status_text = html.escape(b.status or "營業資訊未提供")
  hours_text = html.escape(b.hours or "營業時間未提供")
  map_link = html.escape(b.map_url)
  address = html.escape(b.address)
  image = html.escape(b.image_url or "https://via.placeholder.com/800x450?text=Plumbing")
  html_content = f"""<!DOCTYPE html>
<html lang=\"zh-Hant\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{html.escape(b.name)} | 水電行專屬網站</title>
  <link rel=\"stylesheet\" href=\"../../assets/style.css\" />
</head>
<body>
  <main style=\"max-width: 1100px; margin: 0 auto; padding: 24px;\">
    <a class=\"back-link\" href=\"../../index.html\">← 返回總覽</a>
    <section class=\"hero\">
      <div style=\"display: grid; grid-template-columns: 1.2fr 1fr; gap: 18px; align-items: center;\">
        <img src=\"{image}\" alt=\"{html.escape(b.name)}\" style=\"width: 100%; border-radius: var(--radius); border: 1px solid var(--border);\" loading=\"lazy\" />
        <div>
          <p class=\"status {b.status_class}\">{status_text}</p>
          <h1 style=\"margin: 10px 0 6px;\">{html.escape(b.name)}</h1>
          <p class=\"meta\">{html.escape(b.category)}</p>
          <p class=\"rating\">{rating_text}</p>
          <div class=\"chips\" style=\"margin-top: 10px;\">{feature_items}</div>
        </div>
      </div>
      <div class=\"actions\" style=\"margin-top: 16px;\">
        <a class=\"button\" href=\"{map_link}\" target=\"_blank\" rel=\"noreferrer\">在 Google 地圖開啟</a>
        {f'<a class="button-call" href="tel:{html.escape(b.phone)}">立即撥打</a>' if b.phone else ''}
      </div>
    </section>

    <section class=\"detail-layout\">
      <div class=\"detail-card\">
        <h3>聯絡與位置</h3>
        <div class=\"detail-meta\">
          <div class=\"meta-row\">📍 <span>{address}</span></div>
          {phone_row}
          <div class=\"meta-row\">⏱️ <span>{hours_text}</span></div>
          <div class=\"meta-row\">🗺️ <span><a class=\"back-link\" href=\"{map_link}\" target=\"_blank\" rel=\"noreferrer\">查看地圖路線</a></span></div>
        </div>
      </div>
      <div class=\"detail-card\">
        <h3>服務亮點</h3>
        <div class=\"feature-list\">{feature_items}</div>
      </div>
    </section>
  </main>
</body>
</html>
"""
  (BUSINESS_DIR / b.slug).mkdir(parents=True, exist_ok=True)
  (BUSINESS_DIR / b.slug / "index.html").write_text(html_content, encoding="utf-8")


def main() -> None:
  businesses = parse_businesses()
  reset_docs_directory()
  write_assets()
  for business in businesses:
    build_detail_page(business)
  build_index_page(businesses)
  print(f"Generated {len(businesses)} business pages.")


if __name__ == "__main__":
  main()
