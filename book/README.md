# 《从零读懂 Codex 工程》书稿

给初学者的中文工程导读，介绍上游 [openai/codex](https://github.com/openai/codex) 在提交 `57d4fac64adbcaed0523ca6bf8d58c4ef6875157` 的代码。

- [在线阅读](https://aias00.github.io/codex-engineering-book/)
- [EPUB 电子书](codex工程入门.epub)
- [单页 HTML](codex工程入门.html)

EPUB 可以导入 Apple Books、Calibre、Thorium 等支持 EPUB 3 的阅读器。EPUB 与单页 HTML 均已打包图片，离线可读；打开源码或官方文档链接需要网络。

## 先分清两个仓库

本书的独立仓库是 [Aias00/codex-engineering-book](https://github.com/Aias00/codex-engineering-book)，保存书稿与阅读网站。它不包含 Codex 的完整实现。正文所说的“仓库根目录”始终指 `openai/codex` 源码仓库，包含 `codex-rs/`、`sdk/` 等目录。运行书中的 Rust 练习或 Codex 构建命令，应另行克隆源码仓库并进入对应目录。

本 README 中的命令则明确从**本书仓库根目录**执行。只想阅读时，不需要克隆仓库或安装构建工具。

## 内容

全书约 3.1 万汉字，包含前言、14 章、2 个附录，以及封面和 4 张 SVG 示意图：

1. 这个工程到底做什么
2. 先学会在工程里走路
3. 把大仓库缩成一张地图
4. 读懂 Rust 所需的最少知识
5. 程序从哪里启动
6. 一轮对话如何变成行动
7. 工具怎样连接真实电脑
8. 权限、策略与沙箱
9. 配置、认证与工程约定
10. 让其他程序调用 Codex
11. 从安装到构建与测试
12. 完成你的第一次小改动
13. 用证据定位问题
14. 接下来两周怎么学

附录提供术语解释和按问题查源码的地图。正文含练习与参考答案；源码链接固定到书稿所用提交。示意图省略了实现分支，不能替代完整调用图。

## 文件布局

以下路径相对于本书仓库根目录：

| 路径 | 内容 |
|---|---|
| `book/chapters/` | 可编辑章节 |
| `book/assets/` | 封面和图示 |
| `book/book.css`、`book/book.yaml` | 样式与书籍元数据 |
| `book/build_epub.py` | 构建 EPUB、单页 HTML 与 `build-info.json` |
| `book/verify_epub.py` | 产物与引用核验 |
| `book/source-references.json` | 固定上游提交中文件行数与 SHA-256 统计 |
| `book/translations/zh.yaml` | Pandoc 中文术语 |
| `web/` | GitHub Pages 在线阅读与下载文件 |
| `licenses/` | 上游许可与版权声明副本 |

## 编辑与再生成

安装 Python 3.10+、Pandoc 3.12.1 后，在**本书仓库根目录**执行：

```sh
python3 book/build_epub.py
python3 book/verify_epub.py
```

脚本不调用模型，也不构建 Rust。构建会更新 `book/` 中的 EPUB、HTML 和 `build-info.json`；成功核验后写入 `book/validation.json`。构建保留 Pandoc 警告即失败规则。

默认核验可离线运行，不要求克隆上游源码。脚本对照 `source-references.json` 检查 84 处固定提交引用的路径与行号范围。清单包含 65 个引用文件的行数与 SHA-256，生成时来自对应上游 Git 提交，只保存统计、不复制源码。**默认运行没有重新读取上游源码**；它只能证明书稿引用与已保存的清单相符。

如需实证核对该清单，准备一份包含固定提交的 `openai/codex` Git 仓库，把下列占位路径换成实际路径：

```sh
python3 book/verify_epub.py --source-repo /path/to/codex
```

此模式使用 `git show` 读取该固定提交中的 65 个文件，逐一比对行数与 SHA-256；不会切换源码工作区或修改其中的文件。结果中的 `source_verification` 明确区分 `offline_manifest_only` 与 `git_snapshot_and_manifest`，`source_blobs_read` 记录本次实际读取数量。

两种模式都会检查 EPUB 的 ZIP 结构、XML、完整资源清单、封面、图片替代文本、目录、内部跳转、章节是否进入阅读顺序、最低正文汉字数量，以及产物哈希；同时检查单页 HTML 的内部锚点、图片替代文本与 5 张 SVG 的完整内嵌。它不代替完整 EPUB 标准校验。

## EPUB 标准校验

需要 Java 与官方 EPUBCheck 发行包。解压后，在本书仓库根目录执行；先把 `/path/to/epubcheck.jar` 换成真实路径：

```sh
java -jar /path/to/epubcheck.jar book/codex工程入门.epub \
  --failonwarnings --json book/epubcheck.json
```

报告保存在 `book/epubcheck.json`。标准检查通过不等于在所有阅读器上实测；排版会受字体、字号和分页设置影响。封面与四张图在书稿制作时另经系统 SVG 渲染并人工查看。

## 内容核验范围

书稿制作时交叉审阅了入口、会话循环、工具执行、安全边界、配置和 SDK 路径，并核对 84 处固定提交源码引用。正文区分了当前快照中 TUI/exec 的 app-server 通路，以及 Python app-server 与 TypeScript exec JSONL 两种 SDK 实现。

Python、JavaScript 和 TOML 示例已做静态语法检查。制作环境没有 Rust 编译器，书中的 Rust 练习和构建命令未实际编译执行，正文相应结果均标为“预期”。没有运行模型请求、安装 SDK、使用真实密钥或修改上游业务代码。

制作时访问相关官方动态文档受到访问限制，因此书中以固定源码与仓库文档为依据，并保留官方链接供继续阅读。账户额度、模型可用性和当前产品行为需要读者结合实际版本查阅。

本书是独立工程导读，并非 OpenAI 官方产品手册。原项目和短小源码摘录的许可与版权见上游仓库的 `LICENSE`、`NOTICE`，本书仓库的 `licenses/` 目录保留对应副本。
