# 第 11 章　从安装到构建与测试

看懂目录以后，你可能很想把整个项目运行起来。先给自己一个更容易确认的目标：让一个小包通过本地测试。安装成品、编译源码、连接模型，是三件不同的事。使用已发布的 Codex，只需要相应平台的发行物；研究源码，才需要编译工具。一个字符串函数的测试通常也不需要账号。

本章的命令是依据本书所选提交整理的操作路线，输出均为**预期结果**，不表示编写本书时已经在你的机器上执行成功。第一次下载依赖可能需要网络，耗时取决于机器与缓存。遇到错误，可以带着本章的目标进入下一章的练习或第 13 章的排查。

## 先分清工具的职责

| 工具 | 在这个工程里主要负责什么 |
| --- | --- |
| Rust、rustc | Rust 是语言，rustc 把 Rust 源码编译成机器能运行的程序。 |
| Cargo | 读取 Cargo.toml，解析 Rust 包的依赖，组织检查、构建和测试。 |
| just | 把常用流程写成命名配方；执行什么仍由配方内容决定。 |
| Bazel | 按工程中的构建目标组织构建、测试和发布；它也能构建 Rust 目标。 |
| Node.js、pnpm | 运行 JavaScript 工具，管理 JavaScript 与 TypeScript 包及脚本。 |
| Python、uv | 运行维护脚本与 just 配方启动器，管理 Python SDK 的开发环境与依赖。 |

它们有交集，但入口不同。`pnpm build` 能否运行，要看当前包是否定义了 build 脚本；根 package.json 没有这个脚本。just 也不是另一套 Rust 编译器。根 justfile 第一行把默认工作目录设为 codex-rs，所以从仓库根执行 `just test`，实际的 Cargo 命令通常在那个子目录里运行。

## 确认位置与版本

以下用“仓库根”表示能看到 README.md、justfile 和 codex-rs 的目录。每个命令块都是独立步骤；标注“仓库根”时，先在终端回到那里。macOS 和 Linux 可使用本章的 shell 命令；Windows 初学者可按照安装文档选择 WSL2，在其 Linux 终端内操作。仓库还包含原生 Windows 配方，具体环境需求要结合相应脚本判断。

在仓库根执行：

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
```

第一条预期显示仓库根路径，第二条显示版本，第三条列出改动。空输出通常表示工作区没有待报告的改动。你无需把自己的分支强行切到本书版本；记录差异，就能解释未来代码为什么对不上书里的行号。

Rust 工具链管理器叫 rustup。尚未安装时，先按官方 rustup 安装说明或仓库 docs/install.md 安装，再打开新终端。安装文档中的辅助工具安装步骤会下载并编译工具，不必一次装齐。已安装 rustup 后，在任意目录执行：

```bash
rustup toolchain install 1.99.1 --component rustfmt --component clippy --component rust-src
```

这是所选提交的 rust-toolchain.toml 固定的版本和组件。预期结果是安装完成或提示已安装。下载失败属于工具准备阶段，不能据此判断工程代码有问题。之后从仓库根执行：

```bash
cd codex-rs
rustup show active-toolchain
rustc --version
cargo --version
```

预期看到固定工具链处于活动状态，rustc 显示 1.99.1。Cargo 的版本号无需与 rustc 完全相同。进入目录后自动选择版本，是 rustup 读取工具链文件的结果。

## 从一个小测试开始

在 codex-rs 目录执行：

```bash
cargo test -p codex-ansi-escape --lib
```

`-p` 选择包名，`--lib` 选择库的单元测试。预期 Cargo 编译所需依赖，最后报告该测试目标的结果；它不会因为这条命令而提交模型任务。不过，小包仍可能共享工作区依赖解析，首次运行也可能下载不少文件。包名来自 ansi-escape/Cargo.toml，不是把目录名随意拼成参数。

读输出时，先区分三个阶段。下载阶段出现包名和版本，说明正在准备依赖；编译阶段出现编译器诊断，说明源码、配置或系统工具有问题；测试阶段出现断言失败，说明程序已经运行，但实际值与期望值不一致。最后的通过数字也要结合命令看：如果过滤条件选中了零个测试，即使命令成功退出，也不能说目标行为已经验证。

三个常用动词的证据范围也不同。检查通常用较少成本发现类型等问题；构建会产出编译目标；测试会运行断言。一次构建通过，无法代替有关字符串边界的测试。反过来，一个库的测试通过，也无法代替完整 CLI 在目标平台上的运行验证。把命令、目录、结果一起保存，比只记下一句“成功了”更有用。

已经装好 just、cargo-nextest，并确认 `python3 --version` 可用的读者，可在仓库根执行同一范围的日常配方。当前 justfile 使用 Python 启动 Shell 配方，因此只安装 Rust 工具还不够：

```bash
just test -p codex-ansi-escape --lib
```

预期由 nextest 运行选中的测试。配方还设置线程栈大小、选择 local profile，并允许其他测试在某项失败后继续运行。没有 nextest 时，按照安装文档安装 `cargo-nextest`；初次认识小包时直接使用上一条 Cargo 命令即可。

需要学习 CLI 构建时，再在 codex-rs 目录执行：

```bash
cargo build -p codex-cli --bin codex
```

预期生成调试版 Codex 可执行文件，通常位于该工作区的 target/debug 下；自定义目标目录或交叉编译配置会改变位置。CLI 依赖较多，这一步可能明显更慢。构建成功只证明这次构建成立，不能证明账号、网络、模型访问已经准备好。普通本地练习也不添加 `--all-features`；安装文档明确提醒它会增加时间与磁盘占用。

## 根据改动选择检查

只研究 Rust 小包时，不必先安装所有 SDK 的工具。以后真正修改该包，可在 codex-rs 执行：

```bash
cargo clippy -p codex-utils-string --tests
```

预期得到静态检查结果；警告要结合信息判断。根目录的 `just fix -p codex-utils-string` 会调用带 `--fix` 的 Clippy，可能改文件，使用前先查看工作区状态。`just fmt-check` 是只检查格式的入口，却会组织 Rust、Bazel、Python 等多组格式工具；因此它要求的环境比一个 Rust 单元测试更广。`just fmt` 则可能修改多个文件。

暂时没有准备好完整开发环境，也可以继续读测试、预测输入输出、在纸上画调用关系。把环境准备失败与知识理解失败分开记录，后续就能集中补齐缺少的工具。如果实际改了源码，再以相关测试的真实结果作为提交依据；本书的预期说明只能帮助你判断下一步，不能代替这份依据。

若你学习 TypeScript SDK，根 package.json 的仓库开发要求是 Node.js 至少 22、pnpm 至少 10.34.5，并固定了 pnpm 版本。SDK 包自身的 Node.js 至少 18 是包的运行声明，不应代替仓库开发要求。在仓库根执行：

```bash
pnpm install --frozen-lockfile
pnpm --filter @openai/codex-sdk build
```

第一条按锁文件安装工作区依赖，可能触发允许的生命周期脚本；第二条选择 SDK 包运行 tsup。预期产出 sdk/typescript/dist 中的 ESM JavaScript、类型声明等文件。它没有重新编译 Rust CLI，也没有执行 README 的模型示例。

Python SDK 使用另一套 pyproject.toml，要求 Python 至少 3.10，测试依赖放在 test 组，协议生成源指向 app-server-protocol 的 schema。先读这些配置，再决定是否安装 uv。Bazel 学习则从具体 BUILD.bazel 与目标开始；justfile 的 `bazel-codex` 配方对应 `//codex-rs/cli:codex`。现在知道这条路线在哪里即可，无需为了入门执行全仓 Bazel 测试。

## 自测与参考答案

题目一：只改了 ansi-escape 的库函数，第一条验证命令选什么？参考答案：在 codex-rs 中运行 `cargo test -p codex-ansi-escape --lib`，先确认相关目标，再依据改动扩大范围。

题目二：SDK 的 dist 已生成，是否说明 Rust CLI 已成功构建？参考答案：不能。两者对应不同工具、输入与产物，证据必须与要证明的结论对应。

题目三：为什么只检查格式也会提示缺少 uv 或 DotSlash？参考答案：根格式配方把多个语言的格式检查组织在一起。应根据失败分组补工具，不能把它误判成刚改的 Rust 函数无法编译。

本章源码入口：[`docs/install.md`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/docs/install.md#L15)、[`justfile`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/justfile#L1)、[`codex-rs/rust-toolchain.toml`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/rust-toolchain.toml#L1)、[`package.json`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/package.json#L34)、[`sdk/typescript/package.json`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/sdk/typescript/package.json#L34)、[`sdk/typescript/tsup.config.ts`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/sdk/typescript/tsup.config.ts#L3)、[`sdk/python/pyproject.toml`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/sdk/python/pyproject.toml#L27)。
