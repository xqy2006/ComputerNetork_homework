# ReactOS nslookup 处理流程整理

参考源码与文档：

- ReactOS `nslookup.c` 源码文档：<https://doxygen.reactos.org/d8/d89/nslookup_8c_source.html>
- ReactOS 仓库：<https://github.com/reactos/reactos>

## 目录位置

ReactOS 的 `nslookup` 位于：

- `base/applications/network/nslookup/`

从 Doxygen 可见核心入口文件是：

- `nslookup.c`
- `nslookup.h`

## 整体处理流程

1. `main`

- 初始化全局状态 `State`、进程堆 `ProcessHeap` 和请求编号 `RequestID`。
- 通过 `GetNetworkParams` 读取系统网络参数，获取默认 DNS 服务器等信息。
- 调用 `ParseCommandLine` 解析命令行参数，例如服务器、查询类型、类、超时、重试和递归开关。
- 如果命令行里给了目标主机名或地址，就直接调用 `PerformLookup`。
- 如果没有给出目标，则进入 `InteractiveMode`，等待用户反复输入查询命令。

2. `ParseCommandLine`

- 识别是否指定了查询目标和要使用的 DNS 服务器。
- 解析 `type`、`class`、`timeout`、`retry`、`port`、`recurse` 等选项并写入 `State`。
- 决定程序是一次性查询还是交互模式。

3. `PerformLookup`

- 根据当前状态选择查询类型。
- 如果查询对象本身是 IP 地址，则把查询类型切换为 `PTR`，做反向解析。
- 调用底层发送逻辑构造 DNS 请求并发往当前 DNS 服务器。
- 收到响应后解析回答区、授权区和附加信息区，并按 `nslookup` 风格格式化输出。

4. `PerformInternalLookup`

- 这是更底层的单次查询实现。
- 先判断输入是主机名还是 IP。
- 若是 IP，则先调用 `ReverseIP` 把地址倒写，再拼接 `in-addr.arpa` 后缀。
- 按 DNS 报文格式手工构造请求头、QNAME、QTYPE、QCLASS。
- 调用 `SendRequest` 发包并等待接收缓冲区返回数据。
- 解析响应报文中的问题数、回答记录和资源记录类型，并把结果输出到调用者。

5. `SendRequest`

- 使用当前 `State` 中的服务器地址、端口、超时和重试参数建立 UDP 查询。
- 把构造好的 DNS 请求报文发送到指定 DNS 服务器。
- 在超时与重试策略下等待响应。
- 成功时把响应数据写回接收缓冲区，供上层解析。

6. `InteractiveMode`

- 按当前 ReactOS 源码命名，程序里保留了 `InteractiveMode` 入口。
- 但从当前 Doxygen 可见，这部分仍标注为 `TODO`，实际会输出“Feature not implemented.”，并不是一个已经完整可用的交互式命令循环。
- 因此阅读源码时，应把重点放在一次性查询路径，也就是参数解析、正反向判断、DNS 请求构造、发送与响应解析。

## 和 Windows 下 nslookup 的对应关系

- 启动后先确定默认 DNS 服务器。
- 支持“直接查一次”和“进入交互模式”两种工作方式。
- 查询主机名时默认做 `A` 或 `AAAA` 查询。
- 查询 IP 地址时自动转成 `PTR` 反向解析。
- 命令行和交互状态都集中保存在全局 `State` 中。

## 可以概括成一句话的流程

ReactOS 的 `nslookup` 本质上是：

“读取默认 DNS 配置和用户参数 -> 确定查询类型 -> 手工拼装 DNS 请求报文 -> 通过 `SendRequest` 发给 DNS 服务器 -> 解析返回的资源记录并输出结果；源码里虽然保留了交互模式入口，但当前版本并未完整实现。”
