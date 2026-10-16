"""验证示例的问答行为与实际追踪导出，不需要 Phoenix 服务或模型密钥。"""

from collections.abc import Iterator

import pytest
from demo import build_graph
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.mark.parametrize(
    ("question", "expected_terms"),
    [
        ("Phoenix 可以做什么？", ("追踪", "评测")),
        ("LangGraph 是什么？", ("节点", "状态")),
    ],
    ids=["phoenix_question", "langgraph_question"],
)
def test_answer_uses_retrieved_knowledge(question: str, expected_terms: tuple[str, str]) -> None:
    """错误检索或丢失节点状态时，回答不应再满足知识库契约。"""
    result = build_graph().invoke({"question": question})

    assert result["question"] == question
    for term in expected_terms:
        assert term in result["context"]
        assert term in result["answer"]


def test_unknown_question_has_no_fabricated_answer() -> None:
    """未命中时不得返回无关知识或伪装成真实模型推理。"""
    result = build_graph().invoke({"question": "月球上有多少只猫？"})

    assert result["answer"] == "演示知识库中没有相关信息。"


@pytest.fixture
def span_exporter() -> Iterator[InMemorySpanExporter]:
    """把真实埋点导出到内存，以检查父子关系和消息内容。"""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = LangChainInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    try:
        yield exporter
    finally:
        instrumentor.uninstrument()
        provider.shutdown()


def test_graph_exports_connected_trace_with_model_input(
    span_exporter: InMemorySpanExporter,
) -> None:
    """埋点丢失、追踪断裂或 Prompt 丢失问题／上下文时应失败。"""
    question = "Phoenix 可以做什么？"
    build_graph().invoke({"question": question})
    spans = span_exporter.get_finished_spans()

    assert {"retrieve", "answer"}.issubset({span.name for span in spans})
    assert len({span.context.trace_id for span in spans}) == 1
    roots = [span for span in spans if span.parent is None]
    assert len(roots) == 1
    span_ids = {span.context.span_id for span in spans}
    assert all(span.parent is None or span.parent.span_id in span_ids for span in spans)
    model_spans = [
        span for span in spans if (span.attributes or {}).get("openinference.span.kind") == "LLM"
    ]
    assert len(model_spans) == 1
    model_input = str(model_spans[0].attributes)
    assert question in model_input
    assert "追踪" in model_input
