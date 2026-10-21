#!/usr/bin/env python3
"""Check EPUB/HTML packaging and pinned source-reference statistics.

Runs offline by default. --source-repo additionally checks the pinned Git blobs.
Complements EPUBCheck; does not execute model examples or Rust builds.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import posixpath
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET
from zipfile import ZIP_STORED, ZipFile

BOOK = Path(__file__).resolve().parent
EPUB = BOOK / "codex工程入门.epub"
HTML = BOOK / "codex工程入门.html"
SOURCE_MANIFEST = BOOK / "source-references.json"
COMMIT = "57d4fac64adbcaed0523ca6bf8d58c4ef6875157"
XHTML = "http://www.w3.org/1999/xhtml"
OPF = "http://www.idpf.org/2007/opf"
EPUB_NS = "http://www.idpf.org/2007/ops"
LINK = re.compile(r"https://github\.com/openai/codex/blob/([0-9a-f]{40})/([^\s)]+)")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("验证失败：" + message)


class PreviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[tuple[str, str, str]] = []
        self.images: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        for key in ("href", "src"):
            if attributes.get(key):
                self.links.append((tag, key, attributes[key]))
        if tag == "img":
            self.images.append(attributes)

    handle_startendtag = handle_starttag


def check_html(expected_images: int) -> dict[str, int]:
    preview = PreviewParser()
    preview.feed(HTML.read_text(encoding="utf-8"))
    preview.close()
    require(len(preview.ids) == len(set(preview.ids)), "HTML 中有重复锚点")
    ids = set(preview.ids)
    anchors = 0
    for tag, attribute, value in preview.links:
        url = urlsplit(value)
        if attribute == "src" or tag == "link":
            require(url.scheme == "data", f"HTML 资源没有内嵌：{tag}[{attribute}]")
        if url.scheme or url.netloc:
            continue
        require(unquote(url.path) in ("", HTML.name), f"HTML 引用了其他本地文件：{value}")
        if url.fragment:
            require(unquote(url.fragment) in ids, f"HTML 内部锚点不存在：{value}")
            anchors += 1
    require(anchors > 0, "HTML 没有内部目录跳转")
    require(len(preview.images) == expected_images, "HTML 封面与四张图片数量不符")
    for index, image in enumerate(preview.images, 1):
        require(bool((image.get("alt") or "").strip()), f"HTML 第 {index} 张图片缺少替代文本")
        source = image.get("src") or ""
        header, separator, payload = source.partition(",")
        require(separator == "," and header == "data:image/svg+xml;base64", f"HTML 第 {index} 张图片不是内嵌 SVG")
        try:
            svg = ET.fromstring(base64.b64decode(payload, validate=True))
        except (binascii.Error, ET.ParseError, ValueError) as error:
            raise SystemExit(f"验证失败：HTML 第 {index} 张图片无法解析：{error}") from error
        require(svg.tag == "{http://www.w3.org/2000/svg}svg", f"HTML 第 {index} 张图片不是 SVG 根元素")
    return {"html_internal_anchors": anchors, "html_embedded_images": len(preview.images)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path,
                        help="可选：包含固定提交的 openai/codex Git 仓库；省略时仅用离线统计清单核验源码引用")
    args = parser.parse_args()
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    require(manifest.get("schema_version") == 1, "源码统计清单版本不符")
    require(manifest.get("repository") == "https://github.com/openai/codex", "源码统计清单仓库不符")
    require(manifest.get("commit") == COMMIT, "源码统计清单提交不符")
    file_statistics = manifest.get("files")
    require(isinstance(file_statistics, dict) and len(file_statistics) == 65, "源码统计清单应包含 65 个引用文件")
    for path, statistics in file_statistics.items():
        require(isinstance(statistics, dict), f"源码统计格式不符：{path}")
        require(type(statistics.get("lines")) is int and statistics["lines"] > 0, f"源码统计行数不符：{path}")
        require(isinstance(statistics.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", statistics["sha256"]) is not None,
                f"源码统计 SHA-256 格式不符：{path}")
    if args.source_repo is not None:
        require(args.source_repo.is_dir(), "--source-repo 不是存在的目录")
        for path, statistics in file_statistics.items():
            try:
                content = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"],
                                                  cwd=args.source_repo, stderr=subprocess.PIPE)
            except (OSError, subprocess.CalledProcessError) as error:
                raise SystemExit(f"验证失败：无法从 --source-repo 读取固定提交中的 {path}") from error
            require(len(content.splitlines()) == statistics["lines"], f"源码实证行数与清单不符：{path}")
            require(hashlib.sha256(content).hexdigest() == statistics["sha256"], f"源码实证 SHA-256 与清单不符：{path}")
    checked = 0
    reference_files: dict[str, int] = {}
    chapters = sorted((BOOK / "chapters").glob("*.md"))
    require(len(chapters) == 17, "章节数量不符")
    for chapter in chapters:
        source = chapter.read_text(encoding="utf-8")
        require(len(re.findall(r"^# ", re.sub(r"```[^\n]*\n.*?```", "", source, flags=re.S), re.M)) == 1, f"{chapter.name} 章标题数量不符")
        require(source.count("```") % 2 == 0, f"{chapter.name} 代码围栏不成对")
        for commit, suffix in LINK.findall(source):
            require(commit == COMMIT, f"{chapter.name} 引用了不同快照")
            path, _, anchor = unquote(suffix).partition("#")
            require(path in file_statistics, f"源码统计清单没有引用文件：{path}")
            if path not in reference_files:
                reference_files[path] = file_statistics[path]["lines"]
            if anchor:
                match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", anchor)
                require(match is not None, f"无法识别源码行号：{suffix}")
                require(1 <= int(match[1]) <= reference_files[path], f"行号越界：{suffix}")
                if match[2]:
                    require(int(match[1]) <= int(match[2]) <= reference_files[path], f"行号范围越界：{suffix}")
            checked += 1
    require(set(reference_files) == set(file_statistics), "源码引用与统计清单文件范围不一致")

    with ZipFile(EPUB) as archive:
        require(archive.testzip() is None, "ZIP CRC 不正确")
        members = archive.namelist()
        require(len(members) == len(set(members)), "ZIP 中有重复路径")
        require(members[0] == "mimetype", "mimetype 不是第一项")
        require(archive.getinfo("mimetype").compress_type == ZIP_STORED, "mimetype 被压缩")
        require(archive.read("mimetype") == b"application/epub+zip", "mimetype 内容错误")
        parsed = {n: ET.fromstring(archive.read(n)) for n in members
                  if n.endswith((".xhtml", ".xml", ".opf", ".ncx", ".svg"))}
        rootfile = parsed["META-INF/container.xml"].find("{*}rootfiles/{*}rootfile")
        require(rootfile is not None, "没有 rootfile")
        package_path = rootfile.attrib["full-path"]
        package = parsed[package_path]
        require(package.attrib["version"] == "3.0", "不是 EPUB 3")
        base = posixpath.dirname(package_path)
        manifest = {i.attrib["id"]: i for i in package.findall(f"{{{OPF}}}manifest/{{{OPF}}}item")}
        resources = {}
        for key, item in manifest.items():
            path = posixpath.normpath(posixpath.join(base, unquote(item.attrib["href"])))
            require(path in members, f"清单资源不存在：{path}")
            resources[key] = path
        payload = {p for p in members if p.startswith(base + "/") and not p.endswith("/")}
        require(payload - {package_path} == set(resources.values()), "文件与资源清单不一致")
        require(any(i.attrib["media-type"] == "text/css" for i in manifest.values()), "缺少 CSS 清单项")
        covers = [k for k, i in manifest.items() if "cover-image" in i.get("properties", "").split()]
        require(len(covers) == 1, "封面图声明数量不符")
        navs = [k for k, i in manifest.items() if "nav" in i.get("properties", "").split()]
        require(len(navs) == 1, "nav 目录声明数量不符")
        nav = parsed[resources[navs[0]]]
        toc = next((e for e in nav.iter(f"{{{XHTML}}}nav")
                    if "toc" in e.get(f"{{{EPUB_NS}}}type", "").split()), None)
        require(toc is not None, "缺少 EPUB TOC")
        top = toc.find(f"{{{XHTML}}}ol")
        require(top is not None and len(top.findall(f"{{{XHTML}}}li")) == 17, "章级目录不是 17 项")
        ids = {path: {e.get("id") for e in tree.iter() if e.get("id")} for path, tree in parsed.items()}
        for path, tree in parsed.items():
            for element in tree.iter():
                if element.tag == f"{{{XHTML}}}img":
                    require(bool(element.get("alt", "").strip()), f"图片没有替代文本：{path}")
                for attribute in ("href", "src"):
                    value = element.get(attribute)
                    if not value:
                        continue
                    url = urlsplit(value)
                    if url.scheme or url.netloc:
                        require(attribute != "src" or url.scheme == "data", f"外部加载资源：{value}")
                        continue
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(url.path))) if url.path else path
                    require(target in members, f"内部引用不存在：{path} -> {value}")
                    if url.fragment:
                        require(unquote(url.fragment) in ids.get(target, set()), f"内部锚点不存在：{path} -> {value}")
        spine = package.findall(f"{{{OPF}}}spine/{{{OPF}}}itemref")
        spine_paths = [resources[i.attrib["idref"]] for i in spine]
        book_text = "\n".join("".join(parsed[p].itertext()) for p in spine_paths if p in parsed)
        for chapter in chapters:
            title = chapter.read_text(encoding="utf-8").splitlines()[0][2:]
            require(title in book_text, f"阅读顺序遗漏章节：{title}")
        require(len(re.findall(r"[\u3400-\u9fff]", book_text)) >= 25000, "正文内容意外缺失")
        svg_images = [p for p in members if p.endswith(".svg")]
        require(len(svg_images) == 5, "封面和四张图未完整打包")

    html_result = check_html(len(svg_images))
    info = json.loads((BOOK / "build-info.json").read_text(encoding="utf-8"))
    for name, details in info["artifacts"].items():
        require(hashlib.sha256((BOOK / name).read_bytes()).hexdigest() == details["sha256"], f"产物哈希不符：{name}")
    result = {
        "status": "passed", "epub_sha256": hashlib.sha256(EPUB.read_bytes()).hexdigest(),
        "source_commit": COMMIT, "source_references_checked": checked,
        "unique_source_files": len(reference_files), "chapter_level_toc_entries": 17,
        "source_verification": "git_snapshot_and_manifest" if args.source_repo is not None else "offline_manifest_only",
        "source_blobs_read": len(file_statistics) if args.source_repo is not None else 0,
        "source_manifest_sha256": hashlib.sha256(SOURCE_MANIFEST.read_bytes()).hexdigest(),
        "images": len(svg_images), "spine_items": len(spine_paths),
        **html_result,
        "checks": ["zip_crc", "mimetype", "xml_parse", "manifest_coverage", "css", "cover",
                   "navigation", "internal_links", "image_alt", "chapter_presence", "pinned_source_lines_from_manifest",
                   "html_internal_anchors", "html_embedded_images", "artifact_hashes"]
                  + (["source_blob_lines_and_sha256"] if args.source_repo is not None else []),
        "scope": ("已读取上游固定 Git 快照，文件行数与 SHA-256 均与统计清单一致。"
                  if args.source_repo is not None else
                  "离线对照统计清单核验源码引用路径与行号；本次未读取上游源码，不能据此声称重新核验了源码内容。")
                 + " EPUB/HTML 本地结构已检查；完整 EPUB 标准校验由 EPUBCheck 单独执行。",
    }
    (BOOK / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
