# tinyhttpd 代码阅读教程

参考资料：

- tinyhttpd 源码镜像：<https://gist.github.com/ShaneTsui/ecac1dac085e4c7bd2c051752cb489ff>
- 代码流程分析文章：<https://cloud.tencent.com/developer/article/1150656>

## 先看入口

`tinyhttpd` 的核心是一个很小的 `httpd.c` 文件。阅读顺序最适合按下面这条主线：

1. `main`
2. `setup_server` 或 `startup`
3. `accept_request`
4. `serve_file`
5. `execute_cgi`
6. `headers / not_found / bad_request / unimplemented`

## 整体运行流程

### 1. 启动监听

`main` 负责：

- 创建监听 socket
- 绑定端口
- 开始 `listen`
- 循环 `accept`

每当有客户端接入，就把连接交给 `accept_request` 处理。

### 2. 解析 HTTP 请求

`accept_request` 是 tinyhttpd 的核心调度函数。它主要做 4 件事：

1. 读取请求行
2. 解析方法和 URL
3. 判断请求是静态文件还是 CGI
4. 分派给 `serve_file` 或 `execute_cgi`

源码里最关键的逻辑是：

- 只重点处理 `GET` 和 `POST`
- `POST` 一律当成 CGI
- `GET` 如果带查询串 `?`，也当成 CGI
- 否则按静态文件处理

它还会把 URL 拼成 `htdocs/...` 路径。如果 URL 以 `/` 结尾，就默认补成 `index.html`。

## 静态文件流程

静态文件请求会走 `serve_file`：

1. 先把剩余请求头读掉
2. 发送状态行和响应头
3. 打开目标文件
4. 用 `cat` 把文件内容写到 socket

这是 tinyhttpd 最适合入门学习的一段，因为它完整展示了：

- 如何从 URL 找到本地文件
- 如何生成 HTTP 响应头
- 如何把文件内容回写给浏览器

## CGI 动态处理流程

如果请求被判定为 CGI，则进入 `execute_cgi`：

1. 继续读取请求头
2. 对 `POST` 找到 `Content-Length`
3. 创建两个管道
4. `fork` 子进程
5. 子进程里设置环境变量，例如：
   - `REQUEST_METHOD`
   - `QUERY_STRING`
   - `CONTENT_LENGTH`
6. 子进程把标准输入输出重定向到管道
7. 调用 `execl` 执行 CGI 程序
8. 父进程把请求体写给 CGI，并把 CGI 输出再转发给客户端

这部分展示了 tinyhttpd 最经典的设计：

- Web 服务器本身不直接生成动态内容
- 它只是把 HTTP 请求转换成 CGI 进程可理解的输入与环境变量
- 再把 CGI 进程的输出当作 HTTP 响应体返回

## 辅助函数怎么读

### `get_line`

按行读取 HTTP 请求内容，并兼容 `\r\n` 与 `\n`。

这是 tinyhttpd 解析请求头的基础函数。

### `headers`

给静态文件发送标准响应头，例如：

- `HTTP/1.0 200 OK`
- `Server: jdbhttpd/0.1.0`
- `Content-Type: text/html`

### `not_found`

目标文件不存在时返回 `404 NOT FOUND`。

### `bad_request`

请求格式有问题时返回 `400 BAD REQUEST`。

### `unimplemented`

请求方法不支持时返回 `501 Method Not Implemented`。

### `cannot_execute`

CGI 程序执行失败时返回 `500 Internal Server Error`。

## 读 tinyhttpd 时最该抓住的 3 个点

### 1. 它把 HTTP 服务器最小闭环写全了

- 接受连接
- 读请求
- 判静态/动态
- 发响应

### 2. CGI 的本质非常清楚

`tinyhttpd` 不是“自己解释脚本”，而是：

- 设置环境变量
- 建立管道
- 启动外部程序
- 转发程序输出

### 3. 代码小，所以非常适合入门 HTTP 服务器

它虽然简单，但足够把下面这些基础概念串起来：

- HTTP 请求行与响应行
- 请求头读取
- 状态码
- 静态文件服务
- CGI 动态执行
- socket / fork / pipe / exec 的配合

## 一句话总结

可以把 tinyhttpd 理解成：

“一个用 C 写成的最小可运行 Web 服务器样本，它先解析请求，再决定是直接回文件，还是把请求交给 CGI 程序执行，然后把结果返回给浏览器。”
