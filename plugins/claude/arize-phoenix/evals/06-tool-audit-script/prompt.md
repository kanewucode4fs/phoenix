---
max_turns: 12
timeout_seconds: 300
allowed_tools: [Skill, Write]
runs: 3
tags: [phoenix-cli]
---
在当前目录编写名为 `tool-audit.sh` 的 bash 脚本。它接收 Phoenix 追踪 ID 作为第一个参数，并按时间顺序将该追踪中的每个 TOOL 跨度输出为 JSON，包含跨度名称、status_code、工具输入参数和工具输出。我用它发现智能体向工具传入虚构参数的问题，因此必须包含状态为 OK 的工具跨度，不能只包含出错的跨度：错误参数正藏在这些跨度中。假定已经安装 `px` CLI，并导出了 `PHOENIX_ENDPOINT`。只编写脚本，不要运行。
