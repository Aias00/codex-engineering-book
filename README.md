# 从零读懂 Codex 工程

面向初学者的中文工程导读：约 **3.1 万汉字、14 章、2 个附录**，配有目录地图、源码导读、示意图、练习与参考答案。

**[在线阅读](https://aias00.github.io/codex-engineering-book/)** · **[下载 EPUB](https://aias00.github.io/codex-engineering-book/downloads/codex-engineering-book.epub)** · [阅读书稿](book/chapters/00-preface.md)

从终端与 Git 基础开始，逐步认识 Rust 主工程、app-server、代理循环、工具执行、权限与沙箱，以及 Python / TypeScript SDK。最后通过一个独立的 UTF-8 截断练习，学习如何提出假设、修改代码并用测试验证。

本书依据 [OpenAI Codex 提交 57d4fac](https://github.com/openai/codex/commit/57d4fac64adbcaed0523ca6bf8d58c4ef6875157)，是独立编写的工程导读。书中源码链接固定到该快照。

## 从哪里开始

零基础建议先读前四章，再看会话与安全章节。希望用 Python 或 JavaScript 调用 Codex，可以直接查第 10 章；准备动手改代码，可以沿第 11—14 章学习。

在线阅读支持章节导航、移动端阅读、字号与主题设置。所有正文和插图由本站提供，无需登录；EPUB 下载后可以离线阅读。

| 内容 | 位置 |
| --- | --- |
| 可编辑的 Markdown 章节 | [book/chapters/](book/chapters/) |
| 封面与四幅示意图 | [book/assets/](book/assets/) |
| EPUB 与离线 HTML | [book/](book/) |
| 电子书构建与检查 | [book/build_epub.py](book/build_epub.py)、[book/verify_epub.py](book/verify_epub.py) |
| 在线阅读页的生成器与样式 | [web/](web/) |
| GitHub Pages 自动发布流程 | [.github/workflows/pages.yml](.github/workflows/pages.yml) |

## 本地生成与预览

在**本书仓库根目录**执行，需要 Python 3.10+ 和 Pandoc 3.12.1：

```sh
python3 book/build_epub.py
python3 book/verify_epub.py
python3 web/build_site.py
python3 scripts/verify_site.py
python3 -m http.server 8000 --directory _site
```

浏览器访问 `http://localhost:8000/`。生成目录 `_site/` 不提交 Git；GitHub Actions 在推送到 `main` 后会重新生成并发布。

只修改网页样式时，可以直接从 `python3 web/build_site.py` 开始。修改 `book/chapters/` 后，应先重新生成电子书，让在线版与 EPUB 使用相同正文。

书中涉及 `codex-rs/`、`sdk/` 的学习命令，执行位置是 **OpenAI Codex 源码仓库**。本书仓库保存书稿与阅读网站，两个仓库的根目录请分别辨认。要用本地 Codex 源码重新核对引用，可执行：

```sh
python3 book/verify_epub.py --source-repo /path/to/codex
```

不指定时，验证器使用随书保存的固定快照引用清单进行离线核验；相关来源与核验范围见 [book/README.md](book/README.md)。

## 校验与发布

GitHub Actions 使用 Pandoc 生成 EPUB 与 HTML，检查电子书内部链接、目录、资源与源码引用，再用 EPUBCheck 5.3.0 做标准检查，最后构建并部署 GitHub Pages。`main` 后续更新会触发同一流程。

本次 EPUB 标准检查结果为 **0 错误、0 警告**。书中模型调用、Rust 构建和练习结果均按实际核验范围说明，没有把未执行的示例写成运行记录。

上游源码摘录的版权及许可见 [第三方说明](THIRD_PARTY_NOTICES.md) 与 [licenses/](licenses/)。
