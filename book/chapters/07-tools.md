# 第 7 章　工具怎样连接真实电脑

## 工具调用是一张有格式的申请单

模型可以输出“我会检查文件”，也可以发出一个带名字和参数的工具调用。只有后一种被程序识别、找到实现并执行，才真正触及文件、进程或外部服务。自然语言中的承诺本身不会修改电脑。

可以把工具系统想成维修店的领用柜台：申请单写明工具名称和用途，柜台核对可用项目，把申请交给相应工作人员。读文件、运行命令、应用补丁的具体工作不同，共用的登记和调度规则则可以集中管理。

对新手最有用的三个问题是：模型怎样知道有这个工具？程序怎样找到它？它最终在哪里执行？本章依次回答，并用新建文本文件的案例把三者连起来。

## 名称、参数说明与实现各司其职

工具通常有一份说明，列出名称、用途和参数格式；模型根据它构造调用。说明像电器接口的标签，实现才是接口背后的线路。仅仅新增一段工具说明，并不会自动产生执行能力。

当前 `exec_command` 的参数类型在 [`codex-rs/core/src/tools/handlers/unified_exec.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/handlers/unified_exec.rs#L26)，其中真实字段包括：

```rust
pub(crate) cmd: String,
```

这表示命令文本是一个字符串。其他字段描述 shell、工作目录相关处理、等待时间、终端方式和输出限制等。真正向模型展示的说明还要看对应的工具规格构造和当前工具集合，不能把 Rust 结构体当作完整的模型说明书。

可用工具会受到模型能力、配置、功能开关和所选环境影响。注册在工程里、当前步骤可见、当前调用能够执行，是三个不同条件。你在源码中搜到某个工具，不代表当前运行必然会向模型公布它。

## 从响应项走到具体处理器

上一章已经看到，`handle_output_item_done` 会尝试将输出项转换为 `ToolCall`。调用携带工具名、参数以及调用标识 `call_id`。这个标识用于把结果对应回正确的请求，像取件号码；如果同一步有多个工具，仅靠名字无法区分每一次调用。

接着 `ToolCallRuntime` 组织异步执行，通过 `ToolRouter` 分发。路由器构造 `ToolInvocation`，放入会话、步骤上下文、取消信号、变更跟踪器和调用参数，再交给 `ToolRegistry::dispatch_any_with_state`。

注册表按工具名寻找实现。如果没找到，返回可供模型处理的错误；不会把任何陌生名字直接当作 shell 命令运行。找到后，还会进行相关状态处理和记录，再调用具体工具的 `handle`，由处理器解析参数并执行对应业务。

定位源码时，可沿着这条路线读：`ToolCallRuntime` → `ToolRouter` → `ToolRegistry` → 对应 handler。这里 handler 就是“处理这一类调用的代码”。有了这张地图，你要查运行命令，就去找 `ExecCommandHandler`；要查补丁，就找 `ApplyPatchHandler`，无需从所有工具文件逐个猜。

## 运行命令还要经过进程管理与执行环境

`ExecCommandHandler` 解析模型参数，解析目标环境、工作目录和 shell，准备权限信息，并组装 `ExecCommandRequest`。普通交互生命周期下，它调用 `UnifiedExecProcessManager::exec_command`；一次性模式另有执行到完成的路径。

进程管理器的工作比“调用一次系统命令”多。它要分配运行标识、启动进程、收集输出、记录退出状态，并在命令没有立即结束时保留可继续交互的会话。

启动前，它进入 `open_session_with_sandbox`，建立 `ToolOrchestrator` 和 `UnifiedExecRuntime`。orchestrator 可以译作“执行协调器”：它组织审批判断、选择沙箱尝试和按规则处理失败；runtime 负责这类工具实际如何运行。两者分开，便于命令工具和补丁工具复用共同流程。

审批解决“这项动作是否被允许”，沙箱解决“执行时能访问哪些资源”。配置允许某项动作，不代表动作一定成功；命令本身、路径、环境依赖也都可能出错。反过来，沙箱拒绝也不能随便改成无限权限重跑，协调器依据策略决定下一步。

执行环境也不一定就是界面所在的电脑。核心层使用环境对象取得执行后端或文件系统；远程工作区和本地工作区因此可以共享上层工具逻辑。

源码中的真实分支尤其值得注意：[`codex-rs/core/src/unified_exec/process_manager.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/unified_exec/process_manager.rs#L1351) 在环境为远程，或者请求带 exec-server shell 快照时，使用环境的执行后端启动进程；其余路径还可以在本地调用 `codex_sandboxing::spawn_process`。所以不能说“所有命令都必须经独立 exec-server 进程”。

同样，app-server 与 exec-server 也不是一个东西。前者处理对话和轮次等应用请求，后者提供执行环境能力。名称都带 server，只说明它们提供服务，职责并不相同。

## 命令还在运行时发生什么

有的命令几毫秒结束，有的测试或构建需要很久。交互式执行可以先返回已获得的输出以及仍在运行的会话标识，之后用 `write_stdin` 继续读取，或者向进程写入输入。

`write_stdin` 的实现把工具参数中的 `session_id` 映射到进程管理器使用的进程标识。空输入可以表示轮询，也就是“看看又产生了什么输出”；非空输入则有机会送给正在等待输入的程序。是否可以继续交互，还取决于进程状态和权限等条件。

这里有三个不同问题：工具调用是否返回、对应进程是否退出、用户任务是否完成。首次调用已经返回，但进程仍在运行，是正常情况。进程退出，也可能只是完成了中间的一次检查，核心循环还要继续生成最终回答。

输出还可能被截断。模型看到一段日志，不代表它看到了整个日志。查故障时应同时关心退出码、是否有后续会话、输出是否完整，避免只看到几行正常信息就宣布成功。

## apply_patch 如何真正写入文件

`apply_patch` 适合表达明确的文本文件变更，例如新增文件、删除文件或修改匹配的内容。它的输入使用补丁格式。下面是一个最小教学示例，语法可与 `apply-patch` crate 的新增文件测试对照：

```text
*** Begin Patch
*** Add File: greeting.txt
+你好，Codex！
*** End Patch
```

每行开头的 `+` 表示新增内容，不属于最终文件正文。这里的相对路径要根据所选环境的工作目录解释；它不是永远相对于你最初打开终端的位置。

`ApplyPatchHandler` 首先解析补丁，选择环境，再通过该环境的文件系统验证预期变更。验证成功后，`execute_verified_patch` 准备权限和变更事件，把请求交给 `ToolOrchestrator` 与 `ApplyPatchRuntime`。

实际运行点在 [`codex-rs/core/src/tools/runtimes/apply_patch.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/runtimes/apply_patch.rs#L170)：runtime 调用 `codex_apply_patch::apply_patch_with_options`，传入目标文件系统和沙箱上下文。当前实现不是简单把一段补丁文本拼进 shell 命令后交给任意外部程序。

命令处理器还会识别某些通过命令提交的 apply_patch 请求，并转交补丁处理路径。这个兼容入口并没有取消补丁校验和权限处理。

成功应用补丁，只能证明相应文本变更已经发生，不能证明改动符合需求或程序正确。多文件操作发生后续失败时，也可能留下已写入的部分变更；代码专门跟踪实际 delta。因而应检查变更，再运行与任务有关的验证，不能把补丁当作自动回滚的数据库事务。

## 在独立目录完成一次小任务

下面的案例适合已经安装、登录的读者，在 macOS 或 Linux 终端中尝试。它创建一个单独的演示 Git 仓库，不需要修改 Codex 源码。`mktemp` 返回临时目录路径，`cd` 切换进去：

```sh
demo_dir="$(mktemp -d)"
cd "$demo_dir"
git init
codex exec --sandbox workspace-write "请用 apply_patch 创建 greeting.txt，内容只有一行：你好，Codex！然后读取文件确认内容。"
cat greeting.txt
git status --short
```

这是动手示例，未把某次模型运行伪装成固定实测输出。完成后，`cat` 应显示目标文字，Git 状态通常会显示 `greeting.txt` 为未跟踪文件。临时仓库没有提交历史也不影响查看这次新增文件。

从内部看，请求先进入一轮任务。模型发出 apply_patch 调用，路由器找到补丁处理器，处理器验证新增文件，协调器依据当前策略安排运行，补丁 runtime 使用环境文件系统写入。结果回到模型后，模型继续请求读取确认，最后说明完成情况。若当前模型工具集或配置不支持这一方式，应以实际工具事件和错误为准，不能只凭最终文字认定经过了上述全部步骤。

从验收看，你只需回答三个具体问题：文件是否存在、内容是否一致、是否出现了额外文件或改动。这个小任务说明，使用工具的过程和验证工具结果是两件连续的工作。

## 小练习与参考答案

练习一：工具名不存在时，会不会直接当作命令执行？参考答案：不会。注册表查找失败会生成相应错误，工具名不是任意系统命令入口。

练习二：一次 exec_command 返回了输出和仍在运行的会话标识，是否应立刻重新启动相同命令？参考答案：通常应先通过该会话继续观察；首次返回不等于进程已经退出，重复启动可能产生重复任务。

练习三：补丁成功后能否直接说“需求完成”？参考答案：还要检查实际内容，并执行与需求有关的验证。补丁机制完成文件变更，不替代需求验收。

## 本章源码清单

- [`codex-rs/core/src/tools/router.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/router.rs#L359)：组装调用并分发到注册表。
- [`codex-rs/core/src/tools/registry.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/registry.rs#L615)：查找工具；第 912 行的 `handle_any_tool` 调用具体实现。
- [`codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L148)：命令参数处理；第 358 行拦截补丁，第 418 行选择执行生命周期。
- [`codex-rs/core/src/unified_exec/process_manager.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/unified_exec/process_manager.rs#L1464)：建立协调器和命令 runtime；本地启动见第 1441 行。
- [`codex-rs/core/src/tools/orchestrator.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/orchestrator.rs#L125)：审批与沙箱尝试的共同流程。
- [`codex-rs/core/src/tools/handlers/apply_patch.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/handlers/apply_patch.rs#L302)：解析、验证与执行补丁入口；底层新增文件测试见 `apply-patch/src/lib.rs:857`。
- [`codex-rs/core/src/tools/handlers/unified_exec/write_stdin.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/handlers/unified_exec/write_stdin.rs#L59)：向已有执行会话写入或读取后续结果。
- [`codex-rs/core/src/tools/runtimes/apply_patch.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/core/src/tools/runtimes/apply_patch.rs#L181)：通过环境文件系统与沙箱上下文实际应用补丁。
