# 第 12 章　完成你的第一次小改动

第一次练习的合适规模，是你能说清输入、预期、改动和退回方法的一个函数。我们选择真实工程中的 codex-utils-string 包。它导出了字符串截取、标签清理、位置后缀转换等工具，比从完整会话引擎起步更容易观察。本章只让你创建独立演练文件；仓库里的业务函数保持原样。

## 读懂一个真实函数的约定

打开 codex-rs/utils/string/src/lib.rs，找到 `take_bytes_at_char_boundary`。名字可拆成“取一些字节”和“保持字符边界”。它接收字符串与字节预算，返回原字符串的一个前缀。Rust 字符串使用 UTF-8，英文 a 通常占一个字节，中文“中”占三个字节。随意从第二个字节切开“中”，无法得到合法字符串。

以 `a中b` 为例：三个字符总计五个字节。预算为一，能保留 a；预算为二，仍然只能保留 a；预算为四，能保留 a中。预算是上限，不要求每个字节都用满。这一约定比“截几个字符”更精确。

这里的字符边界是 UTF-8 编码边界。它没有承诺保留完整的用户视觉字符，例如某些 emoji 组合或字母加组合重音。也没有按终端显示宽度计数。遇到这类需求，应先确认产品要求，再选择适当算法，不能由函数名猜出额外保证。

原函数先处理“预算已经足够”的情况，再遍历字符起始位置，计算每个字符结束的字节位置，只记录预算允许的最后一个结束点。返回的 `&str` 借用了原输入，没有另外分配字符串。暂时记住“返回一个原字符串片段”就能理解这次练习，不必先掌握全部生命周期语法。

同文件后面的测试展示了 `#[test]` 与 `assert_eq!` 的写法，但该提交的这些测试主要覆盖 UUID、指标标签与位置后缀。不要因为文件里有测试，就假定每个导出函数的每一种边界都已覆盖。

## 建立自己的演练区

先在仓库根运行：

```bash
git status --short
mkdir -p book-lab
```

第一条帮助你记住原有改动；第二条创建练习目录。若已有同名目录或文件，先查看内容，选择一个新目录，后续命令同步替换路径。然后用编辑器新建 book-lab/boundary.rs，输入下面的完整内容。第一版故意有缺陷，是题目给出的起点，并不是仓库中的真实实现。

```rust
fn take_bytes_at_char_boundary(s: &str, maxb: usize) -> &str {
    &s[..s.len().min(maxb)]
}

#[test]
fn ascii_prefix() {
    assert_eq!(take_bytes_at_char_boundary("hello", 3), "hel");
}

#[test]
fn stops_before_partial_chinese() {
    assert_eq!(take_bytes_at_char_boundary("a中b", 2), "a");
}

#[test]
fn includes_complete_chinese() {
    assert_eq!(take_bytes_at_char_boundary("a中b", 4), "a中");
}

#[test]
fn zero_budget_and_empty_input() {
    assert_eq!(take_bytes_at_char_boundary("a中b", 0), "");
    assert_eq!(take_bytes_at_char_boundary("", 9), "");
}

#[test]
fn enough_budget_keeps_all() {
    assert_eq!(take_bytes_at_char_boundary("a中b", 99), "a中b");
}
```

每个测试把一种约定写成可执行的例子。它们没有读取工程配置，没有创建 SDK 客户端，也没有调用模型。这样，当结果不符合预期时，你首先需要解释的是这个函数，而不是一整套运行环境。

已按上一章准备固定工具链后，在仓库根执行：

```bash
rustc +1.99.1 --edition=2024 --test book-lab/boundary.rs -o book-lab/boundary-tests
./book-lab/boundary-tests
```

第一条把独立文件编译为测试程序，预期生成指定路径的可执行文件；只有第一条成功后才执行第二条，以免运行先前残留的旧程序。第二条运行测试，预期至少 `stops_before_partial_chinese` 失败，报告索引落在字符内部。其他测试预期通过。以上是由题目推导出的结果，你仍应以自己终端的输出为准。原生 Windows 的可执行文件命名与启动方式有所不同，初学者沿用 WSL2 路线即可。

编译成功与测试通过在这里分开出现：编译器接受了这种切片表达式，但特定输入使运行时检查失败。不要删除失败的测试，也不要把期望值改成程序碰巧输出的内容。测试失败的价值，在于把“中文截断有问题”缩小成一个明确输入。

注意测试数量按带测试标记的函数计数，而不是按断言行数计数。“零预算与空输入”放在同一个测试函数里，所以这里共有五项测试。若其中第一条断言失败，这个函数后面的断言就不会继续执行；需要分别观察的行为，可以以后拆成不同测试。

## 做一个有边界的小修复

现在只改演练文件的函数体，保持五个测试原样。任务要求是：结果必须是原输入的前缀，字节数不超过预算，且截断位置必须合法。先在纸上列出 `a中b` 的字符结束点：一、四、五。再想一想，预算为二时应该选择哪个结束点。

可以参照源码中的算法，也可以自行实现。参考答案如下：

```rust
fn take_bytes_at_char_boundary(s: &str, maxb: usize) -> &str {
    if s.len() <= maxb {
        return s;
    }
    let mut last_ok = 0;
    for (i, ch) in s.char_indices() {
        let end = i + ch.len_utf8();
        if end > maxb {
            break;
        }
        last_ok = end;
    }
    &s[..last_ok]
}
```

`char_indices` 同时提供字符与其起始字节位置，`len_utf8` 给出这个字符占几个字节。我们记录结束点，而不是累计“第几个字符”。初始值为零，使预算小到放不下第一个字符时自然返回空前缀。先处理完整输入，也使超大预算无需遍历。

在仓库根重新编译，确认成功后再运行测试程序，预期五个测试通过。重新编译不可省略，否则你可能再次运行旧二进制。接着自行补一个 `"中a"`、预算二的断言；参考结果是空字符串。再补一个预算三的断言；参考结果是“中”。这两个输入能检查首字符已经是多字节字符的情形。

## 留下可以复述的证据

在自己的笔记中写四句话：原约定是什么；哪个输入揭示了问题；为什么新的结束点合法；实际跑了哪些测试。再在仓库根执行：

```bash
git diff -- codex-rs/utils/string/src/lib.rs
git status --short -- book-lab
```

如果开始时业务文件没有改动，第一条预期仍为空；第二条预期显示新练习目录。普通 git diff 不会显示未跟踪文件的内容，所以请用编辑器检查 boundary.rs，不能把“diff 为空”理解成没有练习文件。仓库的忽略规则也可能影响状态显示，文件是否存在应直接检查路径。

要退回练习，只需恢复自己记录的第一版函数体；要结束练习，先保存笔记，再删除自己新建的演练源文件与测试程序。不要对整个仓库运行清理或恢复命令。以后真正提交修复时，应把测试放进目标包的合适位置，并遵守项目要求；本章的独立练习不能代替包内集成验证。

## 自测与参考答案

题目一：`s.chars().take(2)` 能实现两字节预算吗？参考答案：不能，它按 Unicode 标量值计数，两者单位不同；“中a”的前两个字符需要四个字节。

题目二：五项测试全绿能证明所有 Unicode 显示都正确吗？参考答案：不能，只证明这些例子符合约定。组合字符、显示宽度与性能需要各自的需求和证据。

题目三：这次改动应怎样描述？参考答案：“在独立练习中修复 UTF-8 前缀截断，加入 ASCII、中文、空输入及预算边界断言。”这比“修好了 Codex”更准确，也更容易复查。

本章源码入口：[`codex-rs/utils/string/Cargo.toml`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/utils/string/Cargo.toml#L1)、[`codex-rs/utils/string/src/lib.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/utils/string/src/lib.rs#L15)、[`codex-rs/utils/string/src/lib.rs`](https://github.com/openai/codex/blob/57d4fac64adbcaed0523ca6bf8d58c4ef6875157/codex-rs/utils/string/src/lib.rs#L106)。
