# 附录 B　按问题查源码

本书各章已经列出对应的固定提交链接。下面再提供一份按问题组织的阅读入口，方便你在实际使用时回到代码。

## 我想解释哪个行为

| 问题 | 从这里开始 | 读的时候记什么 |
|---|---|---|
| npm 装出的命令怎么启动原生程序 | `codex-cli/bin/codex.js` | 平台选择、二进制路径、进程转发 |
| 输入 `codex` 后走哪个分支 | `codex-rs/cli/src/main.rs` | 参数解析、子命令、启动函数 |
| 终端界面如何使用服务 | `codex-rs/tui/src/` | app-server 连接与事件消费 |
| 非交互执行如何启动回合 | `codex-rs/exec/src/lib.rs` | ThreadStart、TurnStart、事件输出 |
| 客户端与服务端约定哪些消息 | `codex-rs/app-server-protocol/src/` | 请求、响应、通知各自的类型 |
| 一轮工作如何组织 | `codex-rs/core/src/` | thread、session、step、取消和完成 |
| 模型服务通信如何封装 | `codex-rs/codex-api/`、`codex-rs/codex-client/` | 请求类型、事件流、重试和错误 |
| 工具怎样执行 | `codex-rs/core/src/tools/`、`codex-rs/exec-server/` | 分发、运行时、进程结果 |
| 补丁怎样成为文件变化 | `codex-rs/apply-patch/` | 补丁解析、适用性、测试夹具 |
| 命令规则如何匹配 | `codex-rs/execpolicy/` | 决策、前缀匹配、测试样例 |
| 配置来自哪里 | `codex-rs/config/src/` | 来源、优先级与约束 |
| Python SDK 如何启动服务 | `sdk/python/src/openai_codex/client.py` | 子进程、stdio 协议、生命周期 |
| TS SDK 如何解析结果 | `sdk/typescript/src/exec.ts`、`thread.ts` | exec 参数、逐行 JSON、事件汇总 |
| 本地检查有哪些入口 | `justfile`、`docs/install.md` | 工作目录、目标范围、依赖工具 |

先读一条路径，再观察横向关系。例如追完 exec 发起一轮工作以后，再比较 Python 发起相似请求时少了哪些手写步骤。这样更容易分清“能力相同”与“包装相同”。

## 给自己建立一张证据卡

每调查一个问题，都可以保存下面五行。不必写很长，但每行最好能落到实际文件或输出。

```text
问题：我想解释哪个可观察行为？
基准：提交编号、平台、启动方式是什么？
路径：入口 -> 请求 -> 处理函数 -> 结果。
证据：文件位置、相关测试、实际运行结果。
边界：哪些分支尚未读到，哪些现象还不能解释？
```

当你发现旧文章提到的文件已经消失时，不用立刻认定自己操作错了。先核对提交，再搜索仍然存在的类型或函数名称。拆分大文件、引入服务层、调整协议，都会改变书面调用图。

## 继续查阅的官方文档

以下链接是仓库文档相关主题的官方阅读入口。它们会随产品更新；本书没有把无法抓取的动态页面当作已验证的源码证据。

- [Codex 文档入口](https://developers.openai.com/codex)
- [CLI 功能](https://developers.openai.com/codex/cli/features)
- [基础配置](https://developers.openai.com/codex/config-basic)
- [认证](https://developers.openai.com/codex/auth)
- [非交互使用](https://developers.openai.com/codex/noninteractive)

需要了解具体套餐、价格、模型可用性和当前操作系统支持时，使用这些官方入口继续核对，避免把一次源码快照推断成所有安装版本的保证。

## 本书文件在哪里

本书独立仓库是 [Aias00/codex-engineering-book](https://github.com/Aias00/codex-engineering-book)。从本书仓库根目录看，主要文件如下：

| 路径 | 用途 |
|---|---|
| `book/chapters/` | 可编辑的 Markdown 章节 |
| `book/assets/` | 封面与四张示意图 |
| `book/book.css`、`book/book.yaml` | 阅读样式与书籍元数据 |
| `book/build_epub.py` | 生成 EPUB、单页 HTML 与产物哈希清单 |
| `book/verify_epub.py` | 核验打包结构、目录、内部跳转、HTML 图片内嵌和源码引用 |
| `book/source-references.json` | 固定上游提交中 65 个引用文件的行数与 SHA-256，不含源码正文 |
| `book/README.md` | 构建方法、校验命令与验证范围 |
| `web/` | GitHub Pages 在线阅读页面与下载文件 |
| `licenses/` | 上游许可与版权声明副本 |

安装 Python 3.10+ 与 Pandoc 3.x 后，在**本书仓库根目录**执行：

```sh
python3 book/build_epub.py
python3 book/verify_epub.py
```

默认核验不依赖另一份源码仓库，会对照已保存的统计清单检查固定提交、引用路径和行号范围。它不能证明本次运行重新读取了上游源码。如果本机另有包含本书基准提交的 `openai/codex` 仓库，可以传入它的真实路径，同时核对该提交中文件的行数与 SHA-256：

```sh
python3 book/verify_epub.py --source-repo /path/to/codex
```

这里的 `/path/to/codex` 是源码仓库的占位路径，应替换成你自己的目录。它与保存本书的目录不同。上述命令只构建或检查书稿，不编译 Rust，也不发起模型请求；完整 EPUB 标准校验另见 `book/README.md`。

阅读时可以直接使用 EPUB；希望修改文字时先编辑 Markdown 章节，再运行构建脚本。EPUB 内部是许多文件组成的压缩包，直接修改压缩包通常比维护书稿更容易出错。

## 走到这里以后

你现在不必宣称“已经读懂整个工程”。更扎实的成果是：你知道自己正在读哪份代码，能够从一条输入找到相关边界，知道哪些结果有工具证据支持，并且能在一个小范围内提出、验证和解释改动。接下来选一个具体问题，把证据卡填写完整，这本书就从一次阅读变成了你可以反复使用的工作方法。
