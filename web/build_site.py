#!/usr/bin/env python3
"""Build the self-contained reader from the reviewed book, using only stdlib.

Run from any directory: python3 web/build_site.py
The EPUB is copied byte for byte; this script never rebuilds the publication.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
TITLE = "从零读懂 Codex 工程"
DESCRIPTION = "给初学者的目录地图、源码导读与动手练习。约 3.1 万字，14 章与 2 个附录，从终端基础走到 Rust、代理循环、工具、安全与 SDK。"


class Inventory(HTMLParser):
    """Inspect actual elements rather than counting strings in the document."""

    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "img":
            self.images.append(attrs.get("src", ""))


def inventory(html: str) -> Inventory:
    result = Inventory()
    result.feed(html)
    return result


def extract_book(source: str) -> tuple[str, str, str]:
    body = re.search(r"<body\b[^>]*>(.*?)</body>", source, flags=re.S)
    if body is None:
        raise ValueError("Book HTML has no body")
    toc = re.search(r'<nav\b[^>]*\bid="TOC"[^>]*>.*?</nav>', body[1], flags=re.S)
    cover = re.search(r'<figure\b[^>]*class="book-cover"[^>]*>.*?</figure>', body[1], flags=re.S)
    if toc is None or cover is None:
        raise ValueError("Book HTML must contain its original TOC and cover")
    cover_image = re.search(r"<img\b[^>]*>", cover[0])
    if cover_image is None:
        raise ValueError("Book cover image is missing")
    content = body[1][toc.end():].strip()
    # The overflow container is present in HTML so wide tables work without JS.
    content = re.sub(
        r"(<table\b.*?</table>)",
        '<div class="table-scroll" role="region" aria-label="可横向滚动的表格" tabindex="0">\\1</div>',
        content,
        flags=re.S,
    )
    cover_image = re.sub(r'\sstyle="[^"]*"', "", cover_image[0])
    return toc[0], content, cover_image


def build(args: argparse.Namespace) -> None:
    book_dir = ROOT / "book"
    source = (book_dir / "codex工程入门.html").read_text(encoding="utf-8")
    toc, content, cover = extract_book(source)
    book_inventory = inventory(content)
    toc_inventory = inventory(toc)
    first_anchor = next(link for link in toc_inventory.links if link.startswith("#"))
    build_info = json.loads((book_dir / "build-info.json").read_text(encoding="utf-8"))
    source_commit = escape(build_info["base_commit"], quote=True)
    epub = book_dir / "codex工程入门.epub"
    epub_sha256 = hashlib.sha256(epub.read_bytes()).hexdigest()
    repo = escape(args.repo_url.rstrip("/"), quote=True)
    canonical = escape(args.site_url.rstrip("/") + "/", quote=True)
    download = "downloads/codex-engineering-book.epub"
    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{DESCRIPTION}">
  <meta name="book-source-commit" content="{source_commit}">
  <meta name="book-epub-sha256" content="{epub_sha256}">
  <meta name="theme-color" content="#f7f6f2">
  <meta property="og:type" content="book">
  <meta property="og:title" content="{TITLE}">
  <meta property="og:description" content="{DESCRIPTION}">
  <meta property="og:url" content="{canonical}">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/reader.css">
  <script src="assets/reader.js" defer></script>
  <title>{TITLE} · 在线阅读</title>
</head>
<body>
  <a class="skip-link" href="#book-content">跳到正文</a>
  <header class="site-header">
    <a class="site-brand" href="./" aria-label="从零读懂 Codex 工程首页"><span class="brand-mark" aria-hidden="true">C<span>_</span></span><span>Codex 工程导读</span></a>
    <nav class="header-links" aria-label="站点导航">
      <a href="{repo}">GitHub <span aria-hidden="true">↗</span></a>
      <a class="header-download" href="{download}" download>下载 EPUB <span aria-hidden="true">↓</span></a>
    </nav>
    <div class="reading-progress" aria-hidden="true"><span id="progress-bar"></span></div>
  </header>
  <div class="reader-layout">
    <aside class="sidebar" aria-label="阅读导航">
      <details id="chapter-menu" class="chapter-menu" open>
        <summary><span>全书目录</span><span class="chapter-count">14 章 · 2 附录</span><span class="menu-chevron" aria-hidden="true">⌄</span></summary>
        <div class="toc-scroll">{toc}</div>
      </details>
      <div class="sidebar-footer"><span class="status-dot" aria-hidden="true"></span> 中文 · 面向初学者<br><a href="{repo}#readme">关于本书与源码 ↗</a></div>
    </aside>
    <main id="main-content">
      <section class="book-intro" id="title-block-header" aria-labelledby="book-title">
        <div class="intro-copy">
          <p class="eyebrow"><span aria-hidden="true">◈</span> 从目录出发，读懂一座工程</p>
          <h1 id="book-title">从零读懂<br><span>Codex 工程</span></h1>
          <p class="intro-description">给初学者的目录地图、源码导读与动手练习。<br class="desktop-break">从一个文件、一条命令开始，看清 AI 编程助手如何工作。</p>
          <p class="book-facts"><span>约 3.1 万字</span><span>14 章 + 2 附录</span><span>图解 · 练习 · 答案</span></p>
          <div class="intro-actions"><a class="button button-primary" id="start-reading" href="{escape(first_anchor, quote=True)}">开始阅读 <span aria-hidden="true">→</span></a><a class="button button-secondary" href="{download}" download>下载 EPUB <span aria-hidden="true">↓</span></a></div>
          <p id="resume-note" class="resume-note" hidden></p>
        </div>
        <div class="cover-preview" aria-label="书籍封面">{cover}</div>
      </section>
      <div class="reader-tools" aria-label="阅读设置">
        <span class="reader-label">在线阅读 <span id="progress-label" aria-live="off"></span></span>
        <div class="enhanced-controls" hidden>
          <div class="font-controls" role="group" aria-label="正文字号"><button type="button" id="font-smaller" aria-label="减小正文字号">A−</button><button type="button" id="font-larger" aria-label="增大正文字号">A+</button></div>
          <button type="button" id="theme-toggle" aria-label="切换阅读主题" title="切换阅读主题"><span aria-hidden="true">◐</span><span id="theme-label">主题</span></button>
        </div>
      </div>
      <p class="edition-note">独立工程导读，非官方出版物。源码解读基于 <a href="https://github.com/openai/codex/tree/{source_commit}"><code>{source_commit[:7]}</code></a>；初次阅读建议先读前四章。</p>
      <article class="book-content" id="book-content" aria-label="全书正文" tabindex="-1">
{content}
      </article>
      <footer class="book-footer"><p class="eyebrow">把阅读变成自己的第一步</p><p>选一个问题，找到源码，留下你的证据卡。</p><div><a href="{download}" download>下载 EPUB 离线阅读 ↓</a><a href="{repo}">在 GitHub 查看书稿 ↗</a><a href="#book-title">回到书首 ↑</a></div></footer>
    </main>
  </div>
</body>
</html>
'''
    output_inventory = inventory(html)
    counts = Counter(output_inventory.ids)
    duplicates = [item for item, count in counts.items() if count > 1]
    missing = [link for link in toc_inventory.links if link.startswith("#") and link[1:] not in counts]
    if duplicates or missing:
        raise ValueError(f"Broken reader anchors: duplicate IDs={duplicates}, missing targets={missing}")
    # All original body headings, images and external citations must survive.
    if not set(book_inventory.ids).issubset(output_inventory.ids):
        raise ValueError("Original body anchors were lost")
    if not Counter(book_inventory.images) <= Counter(output_inventory.images):
        raise ValueError("Original illustrations were lost")
    if not Counter(book_inventory.links) <= Counter(output_inventory.links):
        raise ValueError("Original links were lost")
    output = args.output.resolve()
    if output == ROOT or output == book_dir or book_dir in output.parents:
        raise ValueError("Output must not overwrite repository or book sources")
    (output / "assets").mkdir(parents=True, exist_ok=True)
    (output / "downloads").mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(html, encoding="utf-8")
    for name in ("reader.css", "reader.js", "favicon.svg"):
        shutil.copyfile(ROOT / "web" / name, output / "assets" / name)
    shutil.copyfile(epub, output / download)
    # Keep ordinary GitHub Pages serving and dotfile handling predictable.
    (output / ".nojekyll").touch()
    print(f"Built {output}")
    print(f"Preserved {len(toc_inventory.links)} TOC links, {len(book_inventory.ids)} body anchors, "
          f"{len(book_inventory.images)} illustrations, {len(book_inventory.links)} body links.")
    print(f"EPUB copied unchanged ({epub.stat().st_size:,} bytes).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--repo-url", default="https://github.com/Aias00/codex-engineering-book")
    parser.add_argument("--site-url", default="https://aias00.github.io/codex-engineering-book/")
    build(parser.parse_args())
