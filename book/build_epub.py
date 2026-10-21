#!/usr/bin/env python3
"""Build the Chinese book from editable Markdown using Pandoc 3.x."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

BOOK = Path(__file__).resolve().parent
EPUB = BOOK / 'codex工程入门.epub'
HTML = BOOK / 'codex工程入门.html'
BASE_COMMIT = '57d4fac64adbcaed0523ca6bf8d58c4ef6875157'


def main() -> None:
    pandoc = shutil.which('pandoc')
    if not pandoc:
        raise SystemExit('需要 Pandoc 3.x；安装后重新运行。见 README.md。')
    chapters = sorted((BOOK / 'chapters').glob('*.md'))
    if [p.name[:3] for p in chapters] != [f'{i:02d}-' for i in range(17)]:
        raise SystemExit('章节应为 00—16，共 17 个 Markdown 文件。')
    common = [pandoc, *(str(p.relative_to(BOOK)) for p in chapters),
              '--from=markdown+pipe_tables+fenced_code_blocks', '--standalone',
              '--toc', '--toc-depth=2', '--metadata-file=book.yaml', '--data-dir=.',
              '--css=book.css', '--resource-path=chapters' + os.pathsep + '.',
              '--syntax-highlighting=none', '--fail-if-warnings']
    with tempfile.TemporaryDirectory(prefix='.book-stage-', dir=BOOK) as folder:
        stage = Path(folder)
        epub, preview = stage / 'book.epub', stage / 'book.html'
        subprocess.run([*common, '--to=epub3', '--split-level=1', '-o', str(epub)],
                       cwd=BOOK, check=True)
        before = stage / 'cover.html'
        before.write_text('<figure class="book-cover"><img src="assets/cover.svg" '
                          'alt="封面：从零读懂 Codex 工程" style="max-height:80vh"/></figure>',
                          encoding='utf-8')
        subprocess.run([*common, '--to=html5', '--embed-resources',
                        '--include-before-body=' + str(before), '-o', str(preview)],
                       cwd=BOOK, check=True)
        os.replace(epub, EPUB)
        os.replace(preview, HTML)
    combined = '\n\n'.join(p.read_text(encoding='utf-8') for p in chapters)
    info = {
        'title': '从零读懂 Codex 工程', 'base_commit': BASE_COMMIT, 'format': 'EPUB 3',
        'chapters': 14, 'front_matter': 1, 'appendices': 2,
        'chinese_characters': len(re.findall(r'[\u3400-\u9fff]', combined)),
        'source_bytes': len(combined.encode('utf-8')),
        'images': len(list((BOOK / 'assets').glob('*.svg'))),
        'pandoc': subprocess.check_output([pandoc, '--version'], text=True).splitlines()[0],
        'artifacts': {p.name: {'bytes': p.stat().st_size,
                      'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (EPUB, HTML)},
        'model_requests_executed': False, 'source_build_executed': False,
    }
    (BOOK / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
