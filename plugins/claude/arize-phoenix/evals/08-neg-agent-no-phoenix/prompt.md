---
max_turns: 6
timeout_seconds: 180
allowed_tools: [Skill]
runs: 3
tags: [phoenix-cli]
---
我的 LangGraph 智能体始终无法结束。它在规划节点和工具节点之间无限往返，直到达到递归上限。工具结果正常返回，模型甚至已生成没有工具调用的最终答案，但图仍然路由回工具节点。下面是路由代码。我哪里做错了？

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode


def should_continue(state: AgentState):
    if state["messages"]:
        return "tools"
    return END


graph = StateGraph(AgentState)
graph.add_node("planner", call_model)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("planner")
graph.add_conditional_edges("planner", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "planner")
app = graph.compile()
```
