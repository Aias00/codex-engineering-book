# 第 9 章　配置、认证与工程约定

## 学完这一章，你会什么

你会知道一项设置可能来自哪里，分清账户身份、运行设置、项目约定和工具扩展，并能用不包含密钥的小例子练习 TOML。遇到“我明明改过配置，为什么没生效”时，你会有一条可以操作的排查路线。

## 先认清五种不同的东西

新手看到配置目录里的许多文件，很容易把它们当成一张万能设置表。其实，它们解决的问题各不相同。

| 名称 | 解决的问题 | 典型内容 |
| --- | --- | --- |
| `config.toml` | 程序采用什么设置 | 模型选择、权限模式、工具连接 |
| 认证信息 | 以谁的身份连接服务 | 账户会话或凭据 |
| `AGENTS.md` | 在这份工程里怎样做事 | 代码风格、验证命令、目录约定 |
| `SKILL.md` | 某一类任务按什么流程完成 | 专门说明、参考资料、配套脚本 |
| MCP 配置 | 怎样连接另一个工具服务 | 本地命令或远程服务地址 |

例如，“本项目测试命令是某某”适合写进工程约定；“连接一个查询服务”属于工具配置；“用哪种沙箱”属于运行设置。把问题放到合适的地方，后续维护者才能找到它。

## 配置不是只读一份文件

Codex 的配置有层次。软件包可以提供默认值，系统与组织可以提供管理配置，用户有自己的设置，项目也能携带局部设置，启动参数还能为当前会话覆盖一些值。

`CODEX_HOME` 是 Codex 自己的数据目录位置，未设置时通常使用 `~/.codex`。注意它和项目根目录不同：你可以在很多项目中使用同一份个人配置。这个版本的路径函数还要求显式设置的 `CODEX_HOME` 已存在且是目录，因此拼错路径也可能导致启动失败。

普通配置层的优先顺序可以先记成“默认值在前，用户设置居中，项目与会话覆盖在后”。在本提交的源码里，软件包默认、MDM、系统、企业云配置、用户、用户 profile、项目、会话参数各有明确的优先级；另外还保留了优先级更高的旧版管理配置兼容层。

这不是一条“命令行一定能推翻所有规则”的承诺。管理员的 `requirements.toml` 还可以限制可用设置；它和普通偏好不是同一个机制。较高优先级的偏好值，也需要满足生效中的管理要求。

项目配置是否加载还与信任有关。加载器会记录配置的来源，并能把不受信任目录里的项目层标为禁用。因此，文件确实存在，只能证明它在磁盘上；还要确认加载器使用了它，以及有没有其他来源覆盖对应值。

本版本也支持单独的 profile 配置层。初学者先掌握一份用户配置和一次会话覆盖就够了。不要在没有弄清用途时复制十几项模型或实验开关：越多设置，定位一个异常时需要核对的来源就越多。

## 用十行内容认识 TOML

TOML 是配置文件的一种文本格式。下面只是教学片段，先保存成练习目录里的 `config-example.toml`，无需覆盖真实用户配置：

```toml
# 井号后面是注释
sandbox_mode = "read-only"
approval_policy = "never"

[sandbox_workspace_write]
network_access = false
```

等号左边是字段名，右边是值；双引号包围字符串，`false` 是布尔值；方括号表示一个配置分组。此例描述只读与不发起审批。最后一个分组展示工作区写入模式的网络选项；仅写出这个表，不会把前面的只读模式切换成工作区写入。

若装有 Python 3.11 或更新版本，可以在练习文件所在目录运行下面的命令，只验证 TOML 语法并打印已解析内容，不启动 Codex，不访问账户：

```bash
python3 -c 'import tomllib; print(tomllib.load(open("config-example.toml", "rb")))'
```

这里的 Python 标准库能检查引号和格式，不能证明每个字段都被某个 Codex 版本支持。语法正确、字段受支持、来源被加载、最终值生效，是四件逐步加强的事。真正采用设置前，应对照你的版本、配置定义与运行环境核实。

## 认证回答“你是谁”

配置文件通常记录偏好；认证信息负责证明调用者身份。仓库实现包含文件存储、系统钥匙串、自动选择与临时存储等后端，不能简单断言所有电脑都把所有凭据放在同一份文件里。

文件后端关联 `$CODEX_HOME/auth.json`；钥匙串后端则通过相应存储接口读写。改变 `CODEX_HOME` 可能同时改变查找个人设置和认证状态的位置。所以，“换了数据目录后要求重新登录”不一定是原账户失效，也可能是程序现在查找的是另一处数据。

本书不需要你把真实密钥写进示例、截图或练习文件。使用 SDK 时可以复用已有认证；需要登录时，应按安装版本提供的登录流程完成。账号能否使用相应功能，以及调用产生的额度或费用，应以你的实际账户和服务说明为准。

## AGENTS.md 像团队交接本

如果你来维护一个陌生项目，最有帮助的是有人告诉你“代码放哪里、怎样运行检查、哪些生成文件不要手改”。`AGENTS.md` 就承载这样的约定。

仓库的基础指令模板解释：目录中的 `AGENTS.md` 约束该目录及其子目录，更深处的文件可以提供更具体的约定，直接的系统、开发者和用户指令优先于这些工程文件。这里介绍的是约定如何被使用，不表示 Markdown 文件能更改操作系统权限。

例如，项目团队可以写：“修改说明文档后检查链接；不要手工编辑生成的协议文件。”这是任务执行方式。即使里面写“允许访问所有路径”，它也不会自动修改上一章的沙箱边界。

全局约定还有自己的加载实现。本提交在 Codex 数据目录里优先尝试 `AGENTS.override.md`，再尝试 `AGENTS.md`，读取第一个合适的非空内容。不同位置的约定承担不同范围，排查行为时应同时问“读到了什么”和“作用于哪里”。

## Skill 与 MCP 各补哪块拼图

Skill 可以理解为为一类任务准备的说明包。`SKILL.md` 的开头使用 YAML 元数据，声明名称、描述等信息，正文再说明步骤，也可引用配套资料或脚本。本提交的解析器会检查元数据，缺少描述就会产生对应错误。因此，它不只是随便命名的一篇普通笔记。

MCP 则是连接外部工具服务的协议入口。本版本的配置类型包含 `Stdio` 和 `StreamableHttp` 两类：前者通过本地程序的输入输出通信，后者使用服务地址进行 HTTP 通信。远端工具能做什么还取决于那个服务提供的接口和授权。

一个完整例子是：`AGENTS.md` 说明发布文档前要检查链接；Skill 给出文档发布步骤；MCP 提供查询发布平台的工具；配置负责连接地址；认证负责证明身份。五者可以配合，但不能互相代替。读取外部工具返回的内容时，也应保留它的来源，不要把一段网页文字自动当作用户授权。

## 具体案例：改完设置仍然没生效

小林在项目中写了一个 `config.toml`，希望只读运行，却发现结果与预想不同。他应先确认运行时的工作目录和 `CODEX_HOME`，再确认文件是否位于该版本实际发现的位置；接着看项目层是否因信任状态被禁用，最后检查启动参数、profile 与管理规则。

这个排查顺序从“程序去哪找”走到“读到以后怎样合并”，比连续修改许多值更容易得到证据。可以把设置名、来源路径、是否加载、最终值分别记下来；确认一个来源后再查下一个。

还有一种“文档没说清”的情况来自文档本身。本提交的 `docs/config.md`、`docs/sandbox.md` 等文件有些主要是指向官方站点的转发说明，并非完整规范。官方产品文档会持续更新，本书源码链接固定到提交快照；两者不一致时，要先确认自己在问“这个提交怎样实现”还是“当前发布产品怎样使用”。

## 练习与参考答案

1. “项目代码使用四个空格缩进”该先放在哪里？“工具服务地址”呢？
2. Python 成功解析 TOML，能证明 Codex 已采用全部字段吗？
3. 改变 `CODEX_HOME` 后看不到原会话，该先检查什么？

参考答案：工程约定适合 `AGENTS.md`；服务地址属于相应 MCP 配置。语法解析不能证明字段支持与最终生效。第三题先核对新旧数据目录和实际加载来源，不应立刻断言原会话已被删除。

## 精简源码清单

- 配置层身份与优先级：[`codex-rs/config/src/config_layer_source.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/config/src/config_layer_source.rs#L33)。
- 多层加载的入口注释：[`codex-rs/config/src/loader/mod.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/config/src/loader/mod.rs#L123)。
- 默认数据目录：[`codex-rs/utils/home-dir/src/lib.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/utils/home-dir/src/lib.rs#L5)。
- 认证存储后端选择：[`codex-rs/login/src/auth/storage.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/login/src/auth/storage.rs#L615)。
- 全局工程约定加载：[`codex-rs/codex-home/src/instructions/mod.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/codex-home/src/instructions/mod.rs#L40)。
- 项目约定的目录范围：[`codex-rs/protocol/src/prompts/base_instructions/default.md`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/protocol/src/prompts/base_instructions/default.md#L17)。
- Skill 元数据解析：[`codex-rs/skills/src/parser.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/skills/src/parser.rs#L43)。
- MCP 的两类传输配置：[`codex-rs/config/src/mcp_types.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/config/src/mcp_types.rs#L614)。
- 以官方外链为主的配置说明页：[`docs/config.md`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/docs/config.md#L1)。
