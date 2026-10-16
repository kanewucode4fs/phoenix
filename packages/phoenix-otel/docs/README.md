<a id="phoenix-otel-documentation"></a>

# Phoenix OTEL 文档

本目录包含 `arize-phoenix-otel` 包的 Sphinx 文档。

<a id="setup"></a>

## 配置

在本地构建文档：

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   pip install -e ..  # Install phoenix-otel package in development mode
   ```

2. 构建文档：
   ```bash
   make html
   ```

3. 查看文档：
   ```bash
   open build/html/index.html
   ```

<a id="structure"></a>

## 结构

- `source/conf.py` - Sphinx 配置
- `source/index.md` - 文档主页
- `source/api/` - API 参考文件
- `source/_static/` - 静态资源（CSS、图片等）
- `requirements.txt` - 构建文档的 Python 依赖

## Read the Docs

以下情况会自动构建本文档并部署到 Read the Docs：
- 变更推送到 main 分支
- 创建新标签

Read the Docs 配置位于包根目录的 `.readthedocs.yaml`。

<a id="updating-documentation"></a>

## 更新文档

更新 API 文档：

1. 若添加新模块，运行 `sphinx-apidoc` 生成新的 `.rst` 文件
2. 更新 `source/api/otel.rst`，纳入新类/函数
3. 根据需要更新 `source/index.md`
4. 使用 `make html` 在本地测试
5. 提交并推送变更
