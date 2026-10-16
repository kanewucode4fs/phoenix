"""
FastMCP 金融分析服务端
"""

import json
import os
from datetime import datetime, timedelta

import openai
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from phoenix.otel import register
from pydantic import BaseModel

load_dotenv()

tracer_provider = register(auto_instrument=True)

# 获取追踪器
tracer = tracer_provider.get_tracer("financial-analysis-server")

# 配置 OpenAI 客户端
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-4-turbo"

# 创建服务端
mcp = FastMCP("金融分析服务端")


class StockAnalysisRequest(BaseModel):
    ticker: str
    time_period: str = (
        "short-term"  # 可选值：short-term（短期）、medium-term（中期）、long-term（长期）
    )


@mcp.tool()
@tracer.tool(name="MCP.analyze_stock")
def analyze_stock(request: StockAnalysisRequest) -> dict:
    """根据股票代码分析股票，并提供投资建议。"""

    # 调用 LLM API 分析股票
    prompt = f"""
    为以下股票代码提供详细财务分析： {request.ticker}
    投资期限： {request.time_period}

    请包含：
    1. 公司概况
    2. 近期财务表现
    3. 关键指标（市盈率、市值等）
    4. 风险评估
    5. 投资建议

    请按以下结构返回 JSON 对象，保留英文字段名：
    {{
        "ticker": "{request.ticker}",
        "company_name": "公司全称",
        "overview": "公司简介",
        "financial_performance": "近期表现分析",
        "key_metrics": {{
            "market_cap": "数值，单位为十亿",
            "pe_ratio": "当前市盈率",
            "dividend_yield": "当前收益率百分比",
            "52_week_high": "数值",
            "52_week_low": "数值"
        }},
        "risk_assessment": "风险分析",
        "recommendation": "买入、持有或卖出建议及解释",
        "time_horizon": "{request.time_period}"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    analysis = json.loads(response.choices[0].message.content)
    return analysis


class PortfolioOptimizationRequest(BaseModel):
    stocks: list
    risk_tolerance: str = (
        "moderate"  # 可选值：conservative（保守）、moderate（适中）、aggressive（激进）
    )
    investment_horizon: str = "medium"  # 可选值：short（短期）、medium（中期）、long（长期）


@mcp.tool()
@tracer.tool(name="MCP.optimize_portfolio")
def optimize_portfolio(request: PortfolioOptimizationRequest) -> dict:
    """根据股票、风险承受能力和投资期限优化投资组合。"""

    prompt = f"""
    使用以下股票优化投资组合： {", ".join(request.stocks)}
    风险承受能力： {request.risk_tolerance}
    投资期限： {request.investment_horizon}

    请提供：
    1. 每只股票的建议配置比例
    2. 预期收益与风险评估
    3. 分散化分析
    4. 再平衡建议

    请按以下结构返回 JSON 对象，保留英文字段名：
    {{
        "portfolio_allocation": [
            {{"ticker": "TICKER1", "allocation_percentage": XX.X}},
            {{"ticker": "TICKER2", "allocation_percentage": XX.X}},
            ...
        ],
        "expected_annual_return": "X.X%",
        "risk_level": "投资组合风险等级说明",
        "diversification_analysis": "行业与地域分散化分析",
        "rebalancing_recommendation": "再平衡频率",
        "risk_tolerance": "{request.risk_tolerance}",
        "investment_horizon": "{request.investment_horizon}"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    optimization = json.loads(response.choices[0].message.content)

    return optimization


@mcp.tool()
@tracer.tool(name="MCP.forecast_market_trends")
def forecast_market_trends(sector: str, timeframe: int = 6) -> dict:
    """预测指定行业在给定时间范围内的市场趋势，时间单位为月。"""

    end_date = (datetime.now() + timedelta(days=30 * timeframe)).strftime("%B %Y")

    prompt = f"""
    预测 {sector} 行业在未来 {timeframe} 个月内的市场趋势
    （截至 {end_date}）。

    请提供：
    1. 行业总体展望
    2. 主要驱动因素与催化因素
    3. 潜在风险与挑战
    4. 表现突出的细分行业或公司
    5. 投资启示

    请按以下结构返回 JSON 对象，保留英文字段名：
    {{
        "sector": "{sector}",
        "timeframe": "{timeframe} 个月（截至 {end_date}）",
        "overall_outlook": "看涨、中性或看跌及原因",
        "key_drivers": ["驱动因素一", "驱动因素二", "驱动因素三"],
        "potential_risks": ["风险一", "风险二", "风险三"],
        "top_performers": ["细分行业或公司一", "细分行业或公司二", "细分行业或公司三"],
        "investment_implications": "根据预测提出的投资策略建议"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    forecast = json.loads(response.choices[0].message.content)
    return forecast


@mcp.tool()
@tracer.tool(name="MCP.analyze_economic_indicator")
def analyze_economic_indicator(indicator: str, country: str = "United States") -> dict:
    """分析经济指标及其对金融市场的影响。"""

    prompt = f"""
    分析经济指标“{indicator}”（国家或地区：{country}）及其对金融市场的影响。

    请提供：
    1. 指标说明
    2. 当前状态与近期趋势
    3. 对不同资产类别（股票、债券、大宗商品等）的影响
    4. 未来 6 至 12 个月预测
    5. 投资启示

    请按以下结构返回 JSON 对象，保留英文字段名：
    {{
        "indicator": "{indicator}",
        "country": "{country}",
        "description": "指标的衡量内容",
        "current_status": "当前数值与近期趋势",
        "impact": {{
            "stocks": "影响说明",
            "bonds": "影响说明",
            "commodities": "影响说明",
            "currencies": "影响说明"
        }},
        "forecast": "未来 6 至 12 个月预测",
        "investment_implications": "投资者如何根据该指标配置头寸"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    analysis = json.loads(response.choices[0].message.content)
    return analysis


@mcp.tool()
@tracer.tool(name="MCP.generate_investment_report")
def generate_investment_report(client_profile: dict, market_analysis: dict) -> dict:
    """根据客户资料和市场分析生成综合投资报告。"""

    prompt = f"""
    根据以下客户资料生成综合投资报告：
    {json.dumps(client_profile, indent=2)}

    参考以下市场分析：
    {json.dumps(market_analysis, indent=2)}

    报告应包含：
    1. 摘要
    2. 客户财务状况概览
    3. 市场展望
    4. 资产配置建议
    5. 具体投资建议
    6. 风险管理策略
    7. 实施时间表

    请按以下结构返回 JSON 对象，保留英文字段名：
    {{
        "report_title": "[客户姓名]投资策略报告",
        "executive_summary": "摘要正文",
        "client_overview": "客户状况概览",
        "market_outlook": "市场状况摘要",
        "asset_allocation": {{
            "equities": "XX%",
            "fixed_income": "XX%",
            "alternatives": "XX%",
            "cash": "XX%"
        }},
        "investment_recommendations": [
            {{
                "asset_class": "资产类别",
                "recommendation": "具体建议",
                "rationale": "原因说明"
            }}
        ],
        "risk_management": "风险管理策略",
        "implementation_timeline": "实施建议的时间表",
        "timestamp": "当前时间戳"
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    report = json.loads(response.choices[0].message.content)
    report["timestamp"] = datetime.now().isoformat()
    return report


if __name__ == "__main__":
    mcp.run()
