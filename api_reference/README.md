<a id="maintenance-readme-for-phoenix-sphinx-api-documentation"></a>

# Phoenix Sphinx API 文档维护指南

本 API 参考文档详细介绍 Phoenix 的 API，仅涵盖 Phoenix 面向用户提供的公开 API 接口。Phoenix 基于 GitBook 的主要文档位于 `phoenix/docs`。

API 参考文档的维护分为两部分：

1. 使用 Sphinx 构建文档。
2. 使用 Read the Docs 托管文档并进行持续集成（CI）。

<a id="configuration"></a>

## 配置

```
api_reference
 ┣ source
 ┃ ┃ ┣ custom.css
 ┃ ┃ ┣ logo.png
 ┃ ┃ ┗ switcher.json
 ┃ ┣ api
 ┃ ┃ ┣ client.rst
 ┃ ┃ ┣ evals.rst
 ┃ ┃ ┣ experiments.rst
 ┃ ┃ ┗ session.rst
 ┃ ┃ ┗ ...
 ┃ ┣ conf.py
 ┃ ┗ index.md
 ┣ Makefile
 ┣ README.md
 ┣ make.bat
 ┗ requirements.txt
```

- `conf.py`：包含运行 Sphinx 所需的全部相关配置。
- `index.md`：API 参考文档的主入口，必须位于 `source` 目录。要让目标文档出现在 API 参考中，必须在 `index.md` 中定义一条能够到达该文档的路径，也可以通过其他文档间接引用。
- `requirements.txt`：用于管理 Read the Docs 平台及其构建过程所需的依赖。
- Make 构建文件：并非必需，但方便在本地生成静态 HTML 页面。

`requirements.txt` 包含所有 Sphinx 相关依赖。虽然该文件主要用于 Read the Docs 的构建流程，但本地运行和构建也必须安装其中的全部依赖。本地 Phoenix 包（如 `packages/phoenix-evals`）应使用 `-e` 以可编辑模式安装为开发依赖。文件中的本地依赖路径必须相对于 `.readthedocs.yaml` 所在位置定义，该位置通常是仓库根目录。

<a id="building-the-documentation"></a>

## 构建文档

### Sphinx-apidoc

如果 `api` 目录中已经存在 API 的 reStructuredText（rst）或 Markdown（md）文件，可以跳过 apidoc 生成步骤，直接修改这些文件。

如果从零开始，或者需要重置、重新生成 API 文档，则必须先生成包含 Sphinx autodoc 指令的 Markdown 或 reStructuredText 文件。`sphinx-apidoc` 命令会自动生成 rst 文件，并将其放入 `source/output`。请注意，如果用生成的文件替换 `source/api` 中的文件，手动添加的示例、页面结构和模块 autodoc 设置等内容都会被覆盖。

生成 API 参考文件的常用命令如下：

```
sphinx-apidoc -o ./source/output ../path/to/module --separate -M
```

其中，`path/to/module` 表示目标模块。上述命令应在 `/api_reference` 目录中执行；调整路径后，也可以在其他目录执行。

- 命令选项：https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

此过程会为指定包中的所有模块生成包含 autodoc 指令的 reStructuredText 文件。这些文件告诉 Sphinx 如何根据代码库中的文档字符串构建文档。命令执行后，生成的文档位于 `api_reference/source/output`。将需要的文件从 `source/output` 移至 `source/api`。目前采用的 `source/api` 目录结构并非强制要求，其目的是避免 `sphinx-apidoc` 的输出意外覆盖需要保留的文档。将生成目录与正式文档目录分开，可以防止手工编辑的示例或特定页面结构在自动生成 API 参考文件时被覆盖。

<a id="autodoc"></a>

### Autodoc 自动文档

可以编辑 apidoc 生成的文件，通过指令选项指定文档生成行为。autodoc 指令会让 autodoc 扩展从文件中提取文档字符串，并自动生成 API 文档。rst 中的 autodoc 指令通常如下所示：

```
.. automodule:: module_name
   :members:
   :no-undoc-members:
   :exclude-members:
   ...

.. autoclass:: module_name::class_name
   :members:
   ...

.. automethod:: module_name.class_name::function_name
```

其中，`.. automodule:: module_name` 是 autodoc 指令，`:members` 是指令选项。

Sphinx autodoc 的文档及完整指令选项列表见：

- https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

<a id="indexmd"></a>

### index.md 入口文件

将新生成的文件放入 `source/api` 后，还需要在 `index.md` 的 `{toctree}` 下添加模块路径，新文档才会显示。例如下面的路径，文件扩展名可省略，Sphinx 会自动识别：

```
api/module
```

路径也可以通过其他文档间接到达。例如，入口文件引用 `evals.rst`，而 `evals.rst` 再引用多个 evals 子模块。

### conf.py

Sphinx 的全部配置都放在此文件中，包括页面主题、导航栏和侧边栏、扩展及其选项、自定义 CSS 文件等设置。

自定义 CSS 和 JavaScript 文件应放在 `_static` 中。

<a id="html-static-sites"></a>

### HTML 静态站点

使用 autodoc 创建 rst 文件，且 `index.md` 能通过其目录树到达这些文件后，就可以将文档渲染为静态 HTML 页面。构建命令如下：

```
make clean
make html
```

或者：

```
make clean html
```

生成的 HTML 站点位于 `api_reference/build` 目录。

注意：所有自定义静态文件都应放在 `source/_static` 中。

<a id="pydata-theme"></a>

## PyData 主题

API 参考文档使用 PyData 主题。该主题有自己的配置项，可以调整 Sphinx 的行为。配置说明见：https://pydata-sphinx-theme.readthedocs.io/en/stable/

<a id="read-the-docs"></a>

## Read the Docs 文档托管

Sphinx 仅用于生成文档，不提供文档托管功能。要托管文档并在 GitHub 仓库发生变化时自动更新，需要使用 Read the Docs。Phoenix 是开源项目，可以使用 Read the Docs 的免费社区版。

### .readthedocs.yaml

Read the Docs 的配置位于仓库根目录的 `/.readthedocs.yaml`。文件中必须正确指定 Sphinx 的 `conf.py` 路径，以及 API 参考目录中的 `requirements.txt` 路径。只要具备有效的 Phoenix 模块 rst 或 md 文件、`.readthedocs.yaml` 和 `conf.py`，Read the Docs 就会自动构建文档。新提交推送到 Phoenix 仓库后，Read the Docs 会收到 Webhook，并重新构建与该提交对应的参考文档。仓库更新标签时，也会按照 Read the Docs 中 `Automation Rules`（自动化规则）的设置，自动构建并公开相应标签的文档。

### api_reference/requirements.txt

Read the Docs 使用此文件安装构建和渲染 API 文档所需的依赖，其中也包括本地 Phoenix 包。此文件以仓库根目录为基准读取，因此本地依赖的引用路径也应以仓库根目录为基准。

<a id="versioning"></a>

### 版本管理

Read the Docs 的版本自动构建在平台管理设置的 `Automation Rules`（自动化规则）中配置。`Automatic Version Build and Activation (Tag)`（按标签自动构建并启用版本）规则负责在 Phoenix 发布新版本时自动构建并归类对应文档。该规则不负责主分支更新触发的持续集成（CI）流程，而是确保用户能够访问 Phoenix 的历史版本。Phoenix GitHub 仓库主分支的当前状态始终标记为 `latest`，与实际版本号无关。要更新参考文档导航栏中的版本下拉选项，必须手动编辑 `switcher.json`。

参考文档：

- https://docs.readthedocs.io/en/stable/automation-rules.html
