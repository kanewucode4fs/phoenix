---
type: llm
focus: {source: file, path: validate_judge.py}
weight: 0.5
---
用户有 80 个由两位分析人员人工标注为 pass/fail 的示例，以及 LLM 裁判对同一批 80 个示例的预测，希望判断裁判是否可信。

只评定下面这一条判断条件。文件满足条件则为 PASS，否则为 FAIL；忽略文件中的其他内容。

判断条件：脚本检查或报告人工标签中 pass/fail 的类别平衡，例如指出 70 个 pass、10 个 fail 这样的倾斜数据会让准确率显得很好而 TNR 很差，或说明数据应大致平衡。如果只提及 TPR/TNR，却没有将其与类别平衡联系起来，则失败。
