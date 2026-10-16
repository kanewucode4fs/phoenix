# arize-phoenix-sqlean

此包提供捆绑 [sqlean](https://github.com/nalgeon/sqlean) 扩展的 SQLite Python 封装，可直接替代标准库的 [sqlite3](https://docs.python.org/3/library/sqlite3.html) 模块。

> [!NOTE]
> 这是 [nalgeon/sqlean.py](https://github.com/nalgeon/sqlean.py) 的修改版分支，上游于 2026 年 2 月归档。此分支基于上游提交 [`bdd7097`](https://github.com/nalgeon/sqlean.py/commit/bdd7097f8d5777bc9e3ac3235d9be66b9db34519) 导入，作为 Phoenix 单体仓库的一部分由 [Arize AI](https://arize.com) 维护。
> 原始作品由 Anton Zhiyanov 及贡献者编写，采用 [zlib 许可证](https://github.com/Arize-ai/phoenix/blob/main/packages/phoenix-sqlean/LICENSE)。
> `src/` 目录包含源自 CPython `sqlite3` 模块的代码（PSF License 2.0）。构建时会下载 SQLite 合并源码（公有领域）及 [sqlean](https://github.com/nalgeon/sqlean) 扩展源码（MIT 许可证），其中包含 PCRE2（BSD 3-Clause）、STC（MIT）以及基于 Go time 包的代码（BSD 3-Clause）。完整声明和 CPython 修改摘要见 [THIRD_PARTY_LICENSES](https://github.com/Arize-ai/phoenix/blob/main/packages/phoenix-sqlean/THIRD_PARTY_LICENSES)。

```
pip install arize-phoenix-sqlean
```

```python
import sqlean

# enable all extensions
sqlean.extensions.enable_all()

# has the same API as the default sqlite3 module
conn = sqlean.connect(":memory:")
conn.execute("create table employees(id, name)")

# and comes with sqlean extensions
cur = conn.execute("select median(value) from generate_series(1, 99)")
print(cur.fetchone())
# (50.0,)

conn.close()
```

<a id="extensions"></a>

## 扩展

此包捆绑以下常用 SQLite 扩展：

-   [crypto](https://github.com/nalgeon/sqlean/blob/main/docs/crypto.md): 数据哈希、编码和解码
-   [define](https://github.com/nalgeon/sqlean/blob/main/docs/define.md): 用户自定义函数和动态 SQL
-   [fileio](https://github.com/nalgeon/sqlean/blob/main/docs/fileio.md): 文件读写
-   [fuzzy](https://github.com/nalgeon/sqlean/blob/main/docs/fuzzy.md): 模糊字符串匹配和语音学处理
-   [ipaddr](https://github.com/nalgeon/sqlean/blob/main/docs/ipaddr.md): IP 地址操作
-   [regexp](https://github.com/nalgeon/sqlean/blob/main/docs/regexp.md): 正则表达式
-   [stats](https://github.com/nalgeon/sqlean/blob/main/docs/stats.md): 数学统计
-   [text](https://github.com/nalgeon/sqlean/blob/main/docs/text.md): 字符串函数
-   [time](https://github.com/nalgeon/sqlean/blob/main/docs/time.md): 高精度日期/时间
-   [uuid](https://github.com/nalgeon/sqlean/blob/main/docs/uuid.md): 通用唯一标识符
-   [vsv](https://github.com/nalgeon/sqlean/blob/main/docs/vsv.md): 将 CSV 文件作为虚拟表

<a id="installation"></a>

## 安装

```
pip install arize-phoenix-sqlean
```

注意，包名为 `arize-phoenix-sqlean`，代码导入名则仅为 `sqlean`，与上游 `sqlean.py` 包相同。因此，此分支可直接替代上游包（同一环境中两者只能安装一个）。

以下操作系统提供二进制包（wheel）：

-   Linux (x86_64/aarch64)
-   macOS (x86_64/arm64)
-   Windows (x86_64)

<a id="usage"></a>

## 用法

所有扩展默认禁用。你仍可直接用 `sqlean` 替代 `sqlite3`：

```python
import sqlean as sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.execute("select 'sql is awesome'")
print(cur.fetchone())
conn.close()
```

要启用全部扩展，请在调用 `connect()` 前调用 `sqlean.extensions.enable_all()`：

```python
import sqlean

sqlean.extensions.enable_all()

conn = sqlean.connect(":memory:")
cur = conn.execute("select median(value) from generate_series(1, 99)")
print(cur.fetchone())
conn.close()
```

要启用指定扩展，请调用 `sqlean.extensions.enable()`：

```python
import sqlean

sqlean.extensions.enable("stats", "text")

conn = sqlean.connect(":memory:")
cur = conn.execute("select median(value) from generate_series(1, 99)")
print(cur.fetchone())
conn.close()
```

<a id="building-from-source"></a>

## 从源码构建

准备源文件：

```
make prepare-src
make download-sqlite
make download-sqlean
```

构建并测试包：

```
make clean build
```

<a id="credits"></a>

## 致谢

基于 Charles Leifer 的 [pysqlite3](https://github.com/coleifer/pysqlite3) 项目，后者又基于 Gerhard Häring 的 [pysqlite](https://github.com/ghaering/pysqlite)。采用 [zlib 许可证](https://github.com/Arize-ai/phoenix/blob/main/packages/phoenix-sqlean/LICENSE)。
