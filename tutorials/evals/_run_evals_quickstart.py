# ruff: noqa: E402
# mypy: ignore-errors
"""
从 evals_quickstart.ipynb 自动生成的脚本。
跳过 pip 安装、getpass、px.launch_app() 和云认证。
连接 localhost:6006。
"""

import asyncio
import os

os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"

from urllib.request import urlopen

from phoenix.client import AsyncClient, Client
from phoenix.client.helpers.spans import get_input_output_context, get_retrieved_documents
from phoenix.evals import async_evaluate_dataframe, bind_evaluator
from phoenix.evals.llm import LLM
from phoenix.evals.metrics import (  # type: ignore[attr-defined]
    CorrectnessEvaluator,
    FaithfulnessEvaluator,
    RetrievalRelevanceEvaluator,
)
from phoenix.evals.utils import to_annotation_dataframe

from phoenix.trace.trace_dataset import TraceDataset
from phoenix.trace.utils import json_lines_to_df

# ── 单元 2：下载已有追踪数据 ──
print("=== 单元 2：正在下载追踪数据 ===")

traces_url = "https://storage.googleapis.com/arize-phoenix-assets/datasets/unstructured/llm/context-retrieval/trace.jsonl"
with urlopen(traces_url) as response:
    lines = [line.decode("utf-8") for line in response.readlines()]
trace_ds = TraceDataset(json_lines_to_df(lines))
print(f"已加载包含 {len(trace_ds.dataframe)} 个 span 的追踪数据集")

# ── 单元 4：（跳过）px.launch_app() ──
print("=== 单元 4：已跳过 px.launch_app ===")

# ── 单元 7：导出检索文档与查询 ──
print("=== 单元 7：正在导出检索文档与查询 ===")

retrieved_documents_df = get_retrieved_documents(Client())
queries_df = get_input_output_context(Client())
print(f"检索文档形状：{retrieved_documents_df.shape}")  # type: ignore[union-attr]
print(f"查询形状：{queries_df.shape}")  # type: ignore[union-attr]

# ── 单元 9：实例化评估模型 ──
print("=== 单元 9：正在实例化评估模型 ===")

api_key = None  # 使用 OPENAI_API_KEY 环境变量
eval_model = LLM(provider="openai", model="gpt-4o-mini", api_key=api_key)
print("评估模型已创建")

# ── 单元 11：定义评估器 ──
print("=== 单元 11：正在定义评估器 ===")

faithfulness_evaluator = FaithfulnessEvaluator(eval_model)
qa_correctness_evaluator = CorrectnessEvaluator(eval_model)
relevance_evaluator = bind_evaluator(
    evaluator=RetrievalRelevanceEvaluator(eval_model),
    input_mapping={"context": "document"},
)
print("评估器已创建")

# ── 单元 13：运行评估 ──
print("=== 单元 13：正在运行评估 ===")


async def run_evals():  # type: ignore[no-untyped-def]
    faithfulness_and_qa_df = await async_evaluate_dataframe(
        dataframe=queries_df,
        evaluators=[faithfulness_evaluator, qa_correctness_evaluator],
    )
    print(f"忠实性与问答评估形状：{faithfulness_and_qa_df.shape}")
    print(faithfulness_and_qa_df.head())

    relevance_eval_df = await async_evaluate_dataframe(
        dataframe=retrieved_documents_df,
        evaluators=[relevance_evaluator],
    )
    print(f"相关性评估形状：{relevance_eval_df.shape}")
    print(relevance_eval_df.head())

    return faithfulness_and_qa_df, relevance_eval_df


faithfulness_and_qa_df, relevance_eval_df = asyncio.run(run_evals())  # type: ignore[no-untyped-call]

# ── 单元 15：将评估记录到 Phoenix ──
print("=== 单元 15：正在将评估记录到 Phoenix ===")


async def log_evals() -> None:
    px_client = AsyncClient()

    faithfulness_and_qa_annotations = to_annotation_dataframe(faithfulness_and_qa_df)
    print(f"忠实性与问答标注形状：{faithfulness_and_qa_annotations.shape}")

    await px_client.spans.log_span_annotations_dataframe(
        dataframe=faithfulness_and_qa_annotations,
        annotator_kind="LLM",
    )
    print("已记录忠实性与问答标注")

    relevance_annotations = to_annotation_dataframe(relevance_eval_df)
    print(f"相关性标注形状：{relevance_annotations.shape}")

    await px_client.spans.log_span_annotations_dataframe(
        dataframe=relevance_annotations,
        annotator_kind="LLM",
    )
    print("已记录相关性标注")


asyncio.run(log_evals())

# ── 单元 17：（跳过）session.url 引用 ──
print("=== 单元 17：已跳过 session.url ===")
print("=== 完成 ===")
