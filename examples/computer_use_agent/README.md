<a id="computer-use-agent-examples"></a>
# Computer Use Agent 示例

<a id="overview"></a>
## 概述

本仓库包含使用 **LangGraph** 和 **Anthropic** 构建 **Computer Use（计算机操作）Agent** 的示例。Agent 使用 Anthropic 的 **Beta API** 执行各种计算机相关任务，包括执行 Bash 命令、编辑文件和进行系统操作。

**⚠️ 重要提示：** Agent 能够执行系统级操作，因此出于安全考虑，建议在**虚拟机（VM）**中运行。为此，我们提供了 **Docker 文件**，用于配置 **Ubuntu 虚拟机**和 **noVNC**，以便通过浏览器访问虚拟机。

**💡 说明：** 本示例使用的所有工具均**兼容 Ubuntu**。

---  

<a id="features"></a>
## 功能
- **界面：** 使用 Gradio 应用构建。
- **Computer Use Agent 工作流：** 使用 **LangGraph** 构建。
- **Anthropic 模型集成：** 使用 **Anthropic 的 Computer Use Beta 模型**。
- **预置工具：** 包含用于 **Bash 执行、文件编辑和系统操作**的工具。
- **Phoenix 插桩：** 使用 OpenInference 装饰器自动插桩，全面追踪 Agent。
- **端到端追踪：** 使用 Phoenix 跟踪 Agent 性能。


---  

<a id="requirements"></a>
## 环境要求

- **Anthropic API 密钥**
- **Python 3.x**
- **LangGraph 库**
- **Phoenix，用于插桩**
- **Gradio，用于界面**
---  

<a id="installation"></a>
## 安装

💡 **无需手动安装依赖！** 所需库已包含在 **Docker 镜像**中。
只需使用 Docker 命令运行镜像，然后打开浏览器，通过 **noVNC** 访问 Ubuntu 环境。

---  

<a id="usage"></a>
## 使用方法

<a id="1-start-the-virtual-machine-using-docker"></a>
### 1. 使用 Docker 启动虚拟机
首先构建 Docker 镜像：
```sh  
docker build -t computer-use-agent:1.0 .  
```  
运行容器：
```sh  
docker run -v $HOME/.anthropic:/home/computeruse/.anthropic \  
           -p 5900:5900 -p 7860:7860 -p 6080:6080 -p 8080:8080 \  
           -it computer-use-agent:1.0  
```  

<a id="2-access-the-virtual-machine"></a>
### 2. 访问虚拟机
容器运行后，使用 **noVNC** 访问 Ubuntu 环境：

- 打开浏览器并访问：
  ```  
  http://localhost:8080  
  ```  

<a id="3-input-all-the-required-configurations-in-the-webpage"></a>
### 3. 在网页中输入全部必需配置

* **Anthropic API 密钥**
* **Phoenix API 密钥**
* **Phoenix 采集器端点**
* **Phoenix 项目名称**

<a id="4-run-the-agent"></a>
### 4. 运行 Agent
- 输入命令后，Agent 会在 **Ubuntu 虚拟机**中执行。
- 通过 **VNC 界面**监控系统操作。

---  

<a id="file-structure"></a>
## 文件结构
- **`app.py`**：运行 Agent 的主脚本。
- **`agent.py`**：Agent 脚本。
- **`tools/`**：包含计算机操作、Bash 和文件编辑工具的辅助功能。
- **`requirements.txt`**：所需依赖清单（**已包含在 Docker 镜像中**）。

---  

<a id="notes"></a>
## 注意事项

- 请确保在**虚拟机**中运行 Agent，以防意外修改系统。
- **此模型使用的所有工具均兼容 Ubuntu。**
