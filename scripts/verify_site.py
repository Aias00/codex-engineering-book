#!/usr/bin/env python3
"""Verify the built static reader, its anchors, assets and EPUB download."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.chapter_titles: list[str] = []
        self.chapter_title: list[str] | None = None
        self.in_book = False
        self.book_text: list[str] = []
        self.in_toc = False
        self.toc_links = 0
        self.stack: list[tuple[str, bool, bool]] = []
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            assert element_id not in self.ids, f"Duplicate HTML id: {element_id}"
            self.ids.add(element_id)
        if tag not in VOID:
            self.stack.append((tag, self.in_book, self.in_toc))
        if tag == "article" and element_id == "book-content":
            self.in_book = True
        if tag == "nav" and element_id == "TOC":
            self.in_toc = True
        if tag == "h1" and self.in_book:
            self.chapter_title = []
        if tag == "a" and self.in_toc and (values.get("href") or "").startswith("#"):
            self.toc_links += 1
        if tag == "meta" and values.get("name"):
            self.meta[values["name"]] = values.get("content") or ""
        if tag == "img":
            assert (values.get("alt") or "").strip(), "Image lacks alternative text"
        for attr in ("href", "src"):
            if values.get(attr):
                self.links.append((attr, values[attr]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self.chapter_title is not None:
            self.chapter_titles.append(" ".join("".join(self.chapter_title).split()))
            self.chapter_title = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                _, self.in_book, self.in_toc = self.stack[index]
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.in_book:
            self.book_text.append(data)
        if self.chapter_title is not None:
            self.chapter_title.append(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    site = args.site.resolve()
    pages: dict[Path, Page] = {}
    for path in site.rglob("*.html"):
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path] = page
    index = pages[site / "index.html"]
    expected_titles = [" ".join(p.read_text(encoding="utf-8").splitlines()[0][2:].split())
                       for p in sorted((ROOT / "book/chapters").glob("*.md"))]
    assert index.chapter_titles == expected_titles, "Online chapter order or content differs from the book"
    assert len(index.chapter_titles) == 17, "Missing chapter-level headings"
    assert index.toc_links == 128, "Missing TOC links"
    assert len(re.findall(r"[\u3400-\u9fff]", "".join(index.book_text))) >= 25000, "Book text is incomplete"
    checked = 0
    for path, page in pages.items():
        for attr, value in page.links:
            url = urlsplit(value)
            if url.scheme or url.netloc:
                assert attr != "src" or url.scheme == "data", f"Remote dependency: {value}"
                continue
            assert not url.path.startswith("/"), f"Root-relative URL breaks project Pages: {value}"
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            assert target == site or site in target.parents, f"URL leaves the website: {value}"
            if target.is_dir():
                target /= "index.html"
            assert target.is_file(), f"Broken local link: {path.name} -> {value}"
            if url.fragment:
                assert target in pages and unquote(url.fragment) in pages[target].ids, f"Broken anchor: {value}"
            checked += 1
    download = site / "downloads/codex-engineering-book.epub"
    digest = hashlib.sha256(download.read_bytes()).hexdigest()
    assert digest == hashlib.sha256((ROOT / "book/codex工程入门.epub").read_bytes()).hexdigest(), "Download differs from verified EPUB"
    assert index.meta.get("book-epub-sha256") == digest, "Website EPUB hash metadata is missing or stale"
    assert index.meta.get("book-source-commit") == "57d4fac64adbcaed0523ca6bf8d58c4ef6875157", "Missing source snapshot metadata"
    assert (site / ".nojekyll").is_file(), "Missing .nojekyll"
    print(json.dumps({"status": "passed", "chapters": len(index.chapter_titles),
                      "toc_links": index.toc_links, "local_links_checked": checked,
                      "html_pages": len(pages), "epub_sha256": digest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
