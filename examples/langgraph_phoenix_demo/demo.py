"""LangChain 与 LangGraph 接入 Phoenix 的最小问答示例。"""

import argparse
import os
from typing import NotRequired, TypedDict

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

KNOWLEDGE = {
    "phoenix": "Phoenix 可以采集应用追踪、查看节点输入输出，并管理数据集、离线评测和实验对比。",
    "langgraph": "LangGraph 用共享状态、节点和边组织工作流，适合编排包含多个步骤的应用。",
}


class DemoState(TypedDict):
    """两个节点共享的问题、检索结果和最终回答。"""

    question: str
    context: NotRequired[str]
    answer: NotRequired[str]


def build_graph() -> CompiledStateGraph:
    """构建检索知识后调用 LangChain 演示模型的工作流。

    Returns:
        可通过 invoke 输入 question 的已编译 LangGraph。
    """

    def retrieve(state: DemoState) -> dict[str, str]:
        """按关键词查找本地知识，未命中时明确返回无相关信息。"""
        context = next(
            (
                text
                for keyword, text in KNOWLEDGE.items()
                if keyword in state["question"].casefold()
            ),
            "演示知识库中没有相关信息。",
        )
        return {"context": context}

    def answer(state: DemoState) -> dict[str, str]:
        """通过真实 LangChain 调用链演示 Prompt、模型与输出解析。"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "只使用参考资料回答问题；资料不足时明确说明。"),
                ("human", "问题：{question}\n参考资料：{context}"),
            ]
        )
        # 演示模型固定返回检索内容，不执行真实推理，不需要模型 API Key。
        model = FakeListChatModel(responses=[state["context"]])
        chain = prompt | model | StrOutputParser()
        return {
            "answer": chain.invoke({"question": state["question"], "context": state["context"]})
        }

    graph = StateGraph(DemoState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("answer", answer)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def main() -> None:
    """运行问题并将整条工作流及 LangChain 子调用导出到 Phoenix。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="Phoenix 可以做什么？", help="要演示的问题")
    args = parser.parse_args()

    project_name = os.environ.get("PHOENIX_PROJECT", "langgraph-phoenix-demo")
    provider = register(
        project_name=project_name, protocol="http/protobuf", batch=True, verbose=False
    )
    instrumentor = LangChainInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    tracer = provider.get_tracer(__name__)
    try:
        with tracer.start_as_current_span(
            "qa_demo",
            attributes={"openinference.span.kind": "CHAIN", "input.value": args.question},
        ) as span:
            result = build_graph().invoke({"question": args.question})
            span.set_attribute("output.value", result["answer"])
            trace_id = format(span.get_span_context().trace_id, "032x")
        print(f"问题：{args.question}")
        print(f"回答：{result['answer']}")
        print("模型：FakeListChatModel（模拟输出，无真实推理及模型费用）")
        print(f"Phoenix 项目：{project_name}")
        print(f"Trace ID：{trace_id}")
        if not provider.force_flush(timeout_millis=10_000):
            raise RuntimeError("等待追踪导出超时，请检查 Phoenix 连接。")
    finally:
        instrumentor.uninstrument()
        provider.shutdown()


if __name__ == "__main__":
    main()
