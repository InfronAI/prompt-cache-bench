from __future__ import annotations

"""Render the canonical A/B report using the structure in docs/ab-report-standard.md."""

import csv
import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "export/glm52_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_none_20260630"
REPORT_DIR = ROOT / "export/glm52_all_experiments/reports_academic"
DEEPSEEK_REPORT_DIR = (
    ROOT
    / "export/open-source/prompt-cache-bench/experiments/deepseek/deepseek-v4-flash/"
    / "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-reasoning-none-2026-06-29/reports"
)
DEEPSEEK_ZH_HTML = (
    DEEPSEEK_REPORT_DIR
    / "routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.zh.html"
)
DEEPSEEK_EN_HTML = (
    DEEPSEEK_REPORT_DIR
    / "routing-cache-cost-streaming-performance-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft-reasoning-none__2026-06-29.en.html"
)
OUT_STEM = "routing_sort_cache_cost_ab_4x50_stream_ttft_reasoning_none_20260630-report"

SORTS = ["throughput", "price", "latency", "ttft"]
PROVIDERS = ["infron", "openrouter"]
INPUT_TOKEN_PAIR_TOLERANCE = 50
SORT_LABEL_ZH = {
    "throughput": "吞吐优先",
    "price": "价格优先",
    "latency": "端到端时延优先",
    "ttft": "流式 TTFT 优先",
}
SORT_LABEL_EN = {
    "throughput": "Throughput First",
    "price": "Price First",
    "latency": "Latency First",
    "ttft": "TTFT First",
}
METRIC_LABEL_ZH = {
    "throughput": "吞吐量",
    "cost": "实际成本",
    "latency": "端到端 E2E 时延",
    "ttft": "流式 TTFT",
    "cache": "缓存命中率",
}
METRIC_LABEL_EN = {
    "throughput": "Throughput",
    "cost": "Observed cost",
    "latency": "E2E latency",
    "ttft": "Streaming TTFT",
    "cache": "Cache hit rate",
}
METRIC_SPECS = {
    "throughput": ("avg_throughput_output_tokens_per_second", True, "tok/s"),
    "cost": ("total_actual_cost_usd", False, "usd"),
    "latency": ("avg_request_latency_ms", False, "ms"),
    "ttft": ("avg_ttft_ms", False, "ms"),
    "cache": ("token_cache_hit_rate", True, "pct"),
}


def main() -> int:
    global RUN_DIR, REPORT_DIR, OUT_STEM
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default=str(RUN_DIR), help="Directory containing summary.json and benchmark datasets.")
    parser.add_argument("--report-dir", default=str(REPORT_DIR), help="Directory for generated HTML reports.")
    parser.add_argument("--out-stem", default=OUT_STEM, help="Output filename stem before -zh.html / -en.html.")
    args = parser.parse_args()
    RUN_DIR = Path(args.run_dir)
    if not RUN_DIR.is_absolute():
        RUN_DIR = ROOT / RUN_DIR
    REPORT_DIR = Path(args.report_dir)
    if not REPORT_DIR.is_absolute():
        REPORT_DIR = ROOT / REPORT_DIR
    OUT_STEM = args.out_stem
    summary = json.loads((RUN_DIR / "summary.json").read_text(encoding="utf-8"))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for language, template_path in [("zh", DEEPSEEK_ZH_HTML), ("en", DEEPSEEK_EN_HTML)]:
        template = template_path.read_text(encoding="utf-8")
        css, echarts_runtime, init_template = _extract_template_parts(template)
        chart_data = _chart_data(summary, language)
        init_script = _replace_chart_data(init_template, chart_data)
        body = _body(summary, language)
        document = _html_document(css, echarts_runtime, init_script, body)
        out = REPORT_DIR / f"{OUT_STEM}-{language}.html"
        out.write_text(document, encoding="utf-8")
        print(out)
    return 0


def _extract_template_parts(template: str) -> tuple[str, str, str]:
    css = template.split("<style>", 1)[1].split("</style>", 1)[0]
    scripts = re.findall(r"<script>\n?(.*?)\n?</script>", template, flags=re.S)
    if len(scripts) != 2:
        raise RuntimeError("Expected report template to contain ECharts runtime and init script")
    return css, scripts[0], scripts[1]


def _replace_chart_data(init_template: str, chart_data: dict[str, Any]) -> str:
    payload = json.dumps(chart_data, ensure_ascii=False, separators=(",", ":"))
    script = re.sub(r"const chartData = .*?;\n", f"const chartData = {payload};\n", init_template, count=1, flags=re.S)
    script = script.replace("echarts-impossible-quadrilateral", "echarts-capability-radar")
    script = script.replace(
        "const chart=echarts.init(el,null,{renderer:'svg'});",
        "const chart=echarts.init(el,null,{renderer:'svg'}); const safeHigher=(v,max)=>max>0&&v>0?v/max*100:0; const safeLower=(min,v)=>min>0&&v>0?min/v*100:0;",
        1,
    )
    script = script.replace(
        "const minTtft=Math.min(metrics.infron.ttft[i],metrics.openrouter.ttft[i]);\n      scores[sort]={",
        "const minTtft=Math.min(metrics.infron.ttft[i],metrics.openrouter.ttft[i]);\n      const maxCache=Math.max(metrics.infron.cache[i],metrics.openrouter.cache[i])||1;\n      scores[sort]={",
    )
    script = script.replace(
        "infron:[metrics.infron.throughput[i]/maxThr*100,minCost/metrics.infron.cost[i]*100,minLatency/metrics.infron.latency[i]*100,minTtft/metrics.infron.ttft[i]*100].map(v=>Number(v.toFixed(2))),",
        "infron:[safeHigher(metrics.infron.throughput[i],maxThr),safeLower(minCost,metrics.infron.cost[i]),safeLower(minLatency,metrics.infron.latency[i]),safeLower(minTtft,metrics.infron.ttft[i]),safeHigher(metrics.infron.cache[i],maxCache)].map(v=>Number(v.toFixed(2))),",
    )
    script = script.replace(
        "openrouter:[metrics.openrouter.throughput[i]/maxThr*100,minCost/metrics.openrouter.cost[i]*100,minLatency/metrics.openrouter.latency[i]*100,minTtft/metrics.openrouter.ttft[i]*100].map(v=>Number(v.toFixed(2)))",
        "openrouter:[safeHigher(metrics.openrouter.throughput[i],maxThr),safeLower(minCost,metrics.openrouter.cost[i]),safeLower(minLatency,metrics.openrouter.latency[i]),safeLower(minTtft,metrics.openrouter.ttft[i]),safeHigher(metrics.openrouter.cache[i],maxCache)].map(v=>Number(v.toFixed(2)))",
    )
    script = script.replace(
        "const avgScore=provider=>[0,1,2,3].map(idx=>Number((chartData.sorts.reduce((sum,sort)=>sum+scores[sort][provider][idx],0)/chartData.sorts.length).toFixed(2)));",
        "const avgScore=provider=>[0,1,2,3,4].map(idx=>Number((chartData.sorts.reduce((sum,sort)=>sum+scores[sort][provider][idx],0)/chartData.sorts.length).toFixed(2)));",
    )
    script = script.replace(
        "{name:'流式 TTFT\\n越低越好',max:100}]",
        "{name:'流式 TTFT\\n越低越好',max:100},{name:'缓存命中率\\n越高越好',max:100}]",
    )
    script = script.replace(
        "{name:'Streaming TTFT\\nlower is better',max:100}]",
        "{name:'Streaming TTFT\\nlower is better',max:100},{name:'Cache hit rate\\nhigher is better',max:100}]",
    )
    script = script.replace(
        "function scores(provider){ const p=metrics[provider], o=provider==='infron'?metrics.openrouter:metrics.infron; const higher=(a,b)=>100*avg(a)/Math.max(avg(a),avg(b)); const lower=(a,b)=>100*Math.min(avg(a),avg(b))/avg(a); return [higher(p.throughput,o.throughput),lower(p.cost,o.cost),lower(p.latency,o.latency),lower(p.ttft,o.ttft),higher(p.cache,o.cache)].map(v=>Number(v.toFixed(2))); }",
        "function scores(provider){ const p=metrics[provider], o=provider==='infron'?metrics.openrouter:metrics.infron; const higher=(a,b)=>{const aa=avg(a),bb=avg(b),m=Math.max(aa,bb); return m>0?100*aa/m:0}; const lower=(a,b)=>{const aa=avg(a),bb=avg(b),m=Math.min(aa,bb); return aa>0&&m>0?100*m/aa:0}; return [higher(p.throughput,o.throughput),lower(p.cost,o.cost),lower(p.latency,o.latency),lower(p.ttft,o.ttft),higher(p.cache,o.cache)].map(v=>Number(v.toFixed(2))); }",
    )
    return script


def _html_document(css: str, echarts_runtime: str, init_script: str, body: str) -> str:
    icon = "https://framerusercontent.com/images/jYZGKXX6mcMkU1qAXZQeevZRY.png"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link href="{icon}" rel="icon" media="(prefers-color-scheme: light)">
  <link href="{icon}" rel="icon" media="(prefers-color-scheme: dark)">
  <link rel="apple-touch-icon" href="{icon}">
  <style>{css}</style>
</head>
<body>
{body}
<script>
{echarts_runtime}
</script>
<script>
{init_script}
</script>
</body>
</html>
"""


def _chart_data(summary: dict[str, Any], language: str) -> dict[str, Any]:
    labels = [SORT_LABEL_ZH[s] for s in SORTS] if language == "zh" else [SORT_LABEL_EN[s] for s in SORTS]
    metrics: dict[str, dict[str, list[float]]] = {"infron": {}, "openrouter": {}}
    for provider in ["infron", "openrouter"]:
        metrics[provider] = {
            "cache": [_round(_agg(summary, sort, provider, "token_cache_hit_rate") * 100, 4) for sort in SORTS],
            "cost": [_round(_agg(summary, sort, provider, "total_actual_cost_usd"), 8) for sort in SORTS],
            "throughput": [
                _round(_agg(summary, sort, provider, "avg_throughput_output_tokens_per_second"), 4) for sort in SORTS
            ],
            "latency": [_round(_agg(summary, sort, provider, "avg_request_latency_ms"), 4) for sort in SORTS],
            "ttft": [_round(_agg(summary, sort, provider, "avg_ttft_ms"), 4) for sort in SORTS],
            "p95_latency": [_round(_agg(summary, sort, provider, "p95_request_latency_ms"), 4) for sort in SORTS],
            "p99_latency": [_round(_agg(summary, sort, provider, "p99_request_latency_ms"), 4) for sort in SORTS],
            "p95_ttft": [_round(_agg(summary, sort, provider, "p95_ttft_ms"), 4) for sort in SORTS],
            "p99_ttft": [_round(_agg(summary, sort, provider, "p99_ttft_ms"), 4) for sort in SORTS],
        }
    provider_distribution = {
        "infron": [_provider_shares(summary, sort, "infron") for sort in SORTS],
        "openrouter": [_provider_shares(summary, sort, "openrouter") for sort in SORTS],
    }
    return {
        "sorts": SORTS,
        "labels": labels,
        "metrics": metrics,
        "providerDistribution": provider_distribution,
        "meta": {
            "validPairs": _pair_count(),
            "requestRows": _line_count(RUN_DIR / "benchmark_requests.jsonl"),
            "generatedAt": summary.get("generated_at"),
        },
    }


def _provider_shares(summary: dict[str, Any], sort: str, provider: str) -> list[dict[str, Any]]:
    item = summary.get("provider_distribution", {}).get(sort, {}).get(provider, {})
    details = item.get("details") or []
    rows = []
    for detail in details:
        share = detail.get("request_share")
        if share is None:
            total = item.get("total_requests") or 0
            share = (detail.get("request_count") or 0) / total if total else 0
        rows.append({"name": str(detail.get("provider") or "unknown"), "value": _round(float(share) * 100, 4)})
    return rows


def _body(summary: dict[str, Any], language: str) -> str:
    if language == "zh":
        return _body_zh(summary)
    return _body_en(summary)


def _body_zh(summary: dict[str, Any]) -> str:
    model_label = _model_label(summary)
    return "\n".join(
        [
            "<h1>Infron 与 OpenRouter 路由、缓存、成本与流式性能 A/B 实验报告</h1>",
            "<h2>摘要与结论大纲</h2>",
            f"<p><strong>关键词</strong>：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；{html.escape(model_label)}</p>",
            "<h3>摘要</h3>",
            _abstract_zh(summary),
            _impossible_panel_zh(),
            _conclusion_overview(summary, "zh"),
            _executive_outline(summary, "zh"),
            _route_mode_conclusions(summary, "zh"),
            "<h2>1. 引言：背景、研究问题与贡献</h2>",
            "<p>LLM 推理平台的真实性能不仅由模型决定，也由 provider 路由、提示词缓存、流式响应、成本归因和 fallback 策略共同决定。本报告把平台视为可观测系统，以 A/B 配对方式评估速度、成本、缓存和首包体验的多目标权衡。</p>",
            "<h3>1.1 研究假设</h3>",
            _hypothesis_table("zh"),
            "<h3>1.2 本文贡献</h3>",
            "<ul><li>使用响应返回的 <code>usage.prompt_tokens</code> 作为真实 input token 控制变量，并允许 50 tokens 内的小幅跨平台计数波动。</li><li>将 prompt caching 评估扩展到成本、吞吐、E2E latency、TTFT、provider 分布、reasoning telemetry 和配对统计检验。</li><li>所有结论只基于响应可观测 telemetry，不把平台内部私有 routing trace 当作已观测事实。</li></ul>",
            "<h2>2. 方法：实验设计、数据集构造与控制变量</h2>",
            "<h3>2.1 数据集生成方法</h3>",
            _dataset_method(summary, "zh"),
            "<h3>2.2 控制变量方法</h3>",
            _method_diagram_zh(summary),
            f"<p>控制变量方法：同一 <code>sort/group/round</code> 下，两个平台 first/second 两次请求的 <code>usage.prompt_tokens</code> 各自偏差必须不超过 {INPUT_TOKEN_PAIR_TOLERANCE} tokens。总 Input Tokens 使用响应返回的 <code>usage.prompt_tokens</code>，不使用本地 tokenizer 估算。</p>",
            "<h3>2.3 指标定义</h3>",
            _metric_definition_table("zh"),
            "<h2>3. 实验环境与数据质量控制</h2>",
            _environment_table(summary, "zh"),
            "<h2>4. 结果：总体指标与主要发现</h2>",
            _overview_table(summary, "zh"),
            "<h3>4.1 尾延迟与显著性检验</h3>",
            _tail_latency_table(summary, "zh"),
            _significance_table(summary, "zh"),
            "<h3>4.2 Reasoning / Thinking 控制校验</h3>",
            _reasoning_table(summary, "zh"),
            "<h3>4.3 API 协议兼容性矩阵</h3>",
            _api_protocol_compatibility_table(summary, "zh"),
            "<h2>5. 结果可视化：按路由模式的核心指标变化</h2>",
            "<p>以下图表使用同一份严格配对后的 summary 数据驱动，统一展示路由模式、平台差异、成本、缓存、端到端 E2E 时延、流式 TTFT 和上游 Provider 分布。</p>",
            _echarts_panels_zh(),
            "<h2>6. Infron 技术架构与缓存/成本机制解释</h2>",
            _architecture_panel_zh(),
            _cache_cost_mechanism(summary, "zh"),
            "<h2>7. Provider/Route 下钻分析</h2>",
            _provider_table(summary, "zh"),
            _provider_detail_table(summary, "zh"),
            _cache_cost_drilldown(summary, "zh"),
            "<h2>8. 分层结果：按 Prompt 长度的缓存表现</h2>",
            _prompt_length_tier_table(summary, "zh"),
            "<h2>9. 分层结果：按实验组的稳定性检查</h2>",
            _group_stability_tables(summary, "zh"),
            "<h2>10. 讨论：业务价值、适用边界与工程启示</h2>",
            _business_discussion(summary, "zh"),
            "<h2>11. 结论</h2>",
            _final_conclusion_table(summary, "zh"),
            "<h2>12. 局限性、缺失数据与后续实验计划</h2>",
            _limitations_table(summary, "zh"),
            "<h2>13. 可复现性附录</h2>",
            _repro_table("zh"),
        ]
    )


def _body_en(summary: dict[str, Any]) -> str:
    model_label = _model_label(summary)
    return "\n".join(
        [
            "<h1>Infron vs OpenRouter Routing, Cache, Cost, and Streaming Performance A/B Test Report</h1>",
            "<h2>Abstract and Executive Outline</h2>",
            f"<p><strong>Keywords</strong>: Prompt Caching; A/B Testing; Provider Routing; Cache Affinity; Latency; Throughput; Cost Attribution; {html.escape(model_label)}</p>",
            "<h3>Abstract</h3>",
            _abstract_en(summary),
            _impossible_panel_en(),
            _conclusion_overview(summary, "en"),
            _executive_outline(summary, "en"),
            _route_mode_conclusions(summary, "en"),
            "<h2>1. Introduction: Background, Questions, and Contributions</h2>",
            "<p>LLM inference-platform behavior is shaped by provider routing, prompt caching, streaming response handling, cost attribution, and fallback policy. This report treats the platform as an observable system and measures speed, cost, cache reuse, and first-token experience through strict A/B pairs.</p>",
            "<h3>1.1 Research Hypotheses</h3>",
            _hypothesis_table("en"),
            "<h3>1.2 Contributions</h3>",
            "<ul><li>Uses response-returned <code>usage.prompt_tokens</code> as the input-token control while allowing small cross-platform accounting variance up to 50 tokens.</li><li>Extends prompt-caching evaluation to cost, throughput, E2E latency, TTFT, provider distribution, reasoning telemetry, and paired statistical tests.</li><li>Scopes every claim to observable response telemetry instead of private routing internals.</li></ul>",
            "<h2>2. Experimental Design, Dataset, and Controls</h2>",
            "<h3>2.1 Dataset Construction</h3>",
            _dataset_method(summary, "en"),
            "<h3>2.2 Controlled Variables</h3>",
            _method_diagram_en(summary),
            f"<p>Controlled-variable rule: within the same <code>sort/group/round</code>, both platforms must have first/second <code>usage.prompt_tokens</code> deltas no greater than {INPUT_TOKEN_PAIR_TOLERANCE} tokens. Total Input Tokens are computed from response-returned usage, not local tokenizer estimates.</p>",
            "<h3>2.3 Metric Definitions</h3>",
            _metric_definition_table("en"),
            "<h2>3. Experimental Environment and Data Quality</h2>",
            _environment_table(summary, "en"),
            "<h2>4. Results: Overall Metrics and Main Findings</h2>",
            _overview_table(summary, "en"),
            "<h3>4.1 Tail Latency and Statistical Tests</h3>",
            _tail_latency_table(summary, "en"),
            _significance_table(summary, "en"),
            "<h3>4.2 Reasoning / Thinking Control Check</h3>",
            _reasoning_table(summary, "en"),
            "<h3>4.3 API Protocol Compatibility Matrix</h3>",
            _api_protocol_compatibility_table(summary, "en"),
            "<h2>5. Result Visualizations by Routing Mode</h2>",
            "<p>The following charts are driven by the strict-paired summary data and present routing-mode, platform, cost, cache, E2E latency, Streaming TTFT, and upstream provider differences.</p>",
            _echarts_panels_en(),
            "<h2>6. Infron Technical Architecture and Cache/Cost Mechanism</h2>",
            _architecture_panel_en(),
            _cache_cost_mechanism(summary, "en"),
            "<h2>7. Provider/Route Drill-Down</h2>",
            _provider_table(summary, "en"),
            _provider_detail_table(summary, "en"),
            _cache_cost_drilldown(summary, "en"),
            "<h2>8. Stratified Results: Prompt-Length Cache Performance</h2>",
            _prompt_length_tier_table(summary, "en"),
            "<h2>9. Stratified Results: Group-Level Stability</h2>",
            _group_stability_tables(summary, "en"),
            "<h2>10. Discussion: Business Value, Boundaries, and Engineering Implications</h2>",
            _business_discussion(summary, "en"),
            "<h2>11. Conclusion</h2>",
            _final_conclusion_table(summary, "en"),
            "<h2>12. Limitations, Missing Data, and Next Experiments</h2>",
            _limitations_table(summary, "en"),
            "<h2>13. Reproducibility Appendix</h2>",
            _repro_table("en"),
        ]
    )


def _impossible_panel_zh() -> str:
    return """
<div class="echarts-academic-panel impossible-panel">
  <h3>图 0：核心能力归一化雷达图</h3>
  <p class="echarts-academic-note">五个雷达轴分别代表吞吐量、价格、端到端 E2E 时延、流式 TTFT 和缓存命中率。所有指标统一转为 0-100 分，且越外侧越好。</p>
  <div id="echarts-capability-radar" class="echarts-chart impossible-chart"></div>
  <p class="echarts-academic-note">粗实线表示平台综合轮廓，半透明细线和点表示各路由模式下的表现。</p>
</div>"""


def _abstract_zh(summary: dict[str, Any]) -> str:
    cache = _winner_sentence(summary, "cache", "zh")
    cost = _winner_sentence(summary, "cost", "zh")
    throughput = _winner_sentence(summary, "throughput", "zh")
    latency = _winner_sentence(summary, "latency", "zh")
    ttft = _winner_sentence(summary, "ttft", "zh")
    infron_strengths = _provider_strengths(summary, "infron", "zh")
    openrouter_strengths = _provider_strengths(summary, "openrouter", "zh")
    strength_clause = _strength_clause_zh(infron_strengths, openrouter_strengths)
    return (
        f"<p>本报告以 <code>{html.escape(summary['model'])}</code> 为对象，评估 Infron 与 OpenRouter 在 Prompt Caching 场景下的缓存复用、实际成本、吞吐、端到端时延和流式 TTFT 表现。</p>"
        f"<p>核心结论是：{cache}；{cost}；{throughput}；{latency}；{ttft}。</p>"
        f"<p>整体看，{strength_clause}。平台选择不应只看单一指标，而应按业务目标在成本、缓存稳定性、吞吐和交互时延之间取舍。</p>"
    )


def _abstract_en(summary: dict[str, Any]) -> str:
    cache = _winner_sentence(summary, "cache", "en")
    cost = _winner_sentence(summary, "cost", "en")
    throughput = _winner_sentence(summary, "throughput", "en")
    latency = _winner_sentence(summary, "latency", "en")
    ttft = _winner_sentence(summary, "ttft", "en")
    infron_strengths = _provider_strengths(summary, "infron", "en")
    openrouter_strengths = _provider_strengths(summary, "openrouter", "en")
    strength_clause = _strength_clause_en(infron_strengths, openrouter_strengths)
    return (
        f"<p>This report evaluates <code>{html.escape(summary['model'])}</code> on Infron and OpenRouter across cache reuse, observed cost, throughput, E2E latency, and Streaming TTFT under Prompt Caching workloads.</p>"
        f"<p>The main findings are: {cache}; {cost}; {throughput}; {latency}; {ttft}.</p>"
        f"<p>Overall, {strength_clause}. Platform choice should be driven by workload objective rather than a single headline metric.</p>"
    )


def _provider_strengths(summary: dict[str, Any], provider: str, language: str) -> list[str]:
    other = "openrouter" if provider == "infron" else "infron"
    labels = {
        "zh": {
            "throughput": "吞吐",
            "ttft": "流式 TTFT",
            "latency": "端到端 E2E 时延",
            "cost": "实际成本",
            "cache": "缓存复用",
            "none": "本轮未形成跨模式优势",
        },
        "en": {
            "throughput": "throughput",
            "ttft": "Streaming TTFT",
            "latency": "E2E latency",
            "cost": "observed cost",
            "cache": "cache reuse",
            "none": "no cross-mode lead in this run",
        },
    }[language]
    strengths = []
    for metric in ["throughput", "ttft", "latency", "cost", "cache"]:
        wins = _winner_counts(summary, metric)
        if wins[provider] > wins[other]:
            strengths.append(labels[metric])
    return strengths or [labels["none"]]


def _strength_clause_zh(infron_strengths: list[str], openrouter_strengths: list[str]) -> str:
    infron_none = infron_strengths == ["本轮未形成跨模式优势"]
    openrouter_none = openrouter_strengths == ["本轮未形成跨模式优势"]
    if infron_none and openrouter_none:
        return "两侧本轮均未形成明确跨模式优势"
    if infron_none:
        return f"Infron 本轮未形成明确跨模式优势，OpenRouter 的跨模式优势主要体现在{'、'.join(openrouter_strengths)}"
    if openrouter_none:
        return f"Infron 的跨模式优势主要体现在{'、'.join(infron_strengths)}，OpenRouter 本轮未形成明确跨模式优势"
    return f"Infron 的跨模式优势主要体现在{'、'.join(infron_strengths)}，OpenRouter 的跨模式优势主要体现在{'、'.join(openrouter_strengths)}"


def _strength_clause_en(infron_strengths: list[str], openrouter_strengths: list[str]) -> str:
    infron_none = infron_strengths == ["no cross-mode lead in this run"]
    openrouter_none = openrouter_strengths == ["no cross-mode lead in this run"]
    if infron_none and openrouter_none:
        return "neither side shows a clear cross-mode strength in this run"
    if infron_none:
        return f"Infron does not show a clear cross-mode strength in this run, while OpenRouter's cross-mode strengths are {', '.join(openrouter_strengths)}"
    if openrouter_none:
        return f"Infron's cross-mode strengths are {', '.join(infron_strengths)}, while OpenRouter does not show a clear cross-mode strength in this run"
    return f"Infron's cross-mode strengths are {', '.join(infron_strengths)}, while OpenRouter's cross-mode strengths are {', '.join(openrouter_strengths)}"


def _impossible_panel_en() -> str:
    return """
<div class="echarts-academic-panel impossible-panel">
  <h3>Figure 0: Normalized Capability Radar</h3>
  <p class="echarts-academic-note">The five radar axes represent throughput, price, E2E latency, Streaming TTFT, and cache hit rate. Every metric is normalized to a 0-100 score, with farther outward meaning better.</p>
  <div id="echarts-capability-radar" class="echarts-chart impossible-chart"></div>
  <p class="echarts-academic-note">Thick solid lines show platform-level contours; translucent lines and points show individual routing modes.</p>
</div>"""


def _conclusion_overview(summary: dict[str, Any], language: str) -> str:
    labels = METRIC_LABEL_ZH if language == "zh" else METRIC_LABEL_EN
    title = (
        "结论总览：核心指标与路由模式胜出方"
        if language == "zh"
        else "Conclusion Overview: Core Metric Winners by Routing Mode"
    )
    note = (
        "基于严格 A/B 配对样本。蓝色代表 Infron，橙色代表 OpenRouter；金色单元格表示该路由模式的目标指标胜出方。"
        if language == "zh"
        else "Based on strict A/B paired samples. Blue represents Infron, orange represents OpenRouter; gold cells mark the winner for the routing objective."
    )
    cards = []
    for metric in ["throughput", "cost", "latency", "ttft", "cache"]:
        wins = _winner_counts(summary, metric)
        dominant = _dominant_winner(wins)
        dominant_name = _provider(dominant)
        text = (
            (f"{dominant_name} {wins[dominant]}/4 胜出" if dominant != "tie" else "双方 4/4 持平")
            if language == "zh"
            else (f"{dominant_name} wins {wins[dominant]}/4" if dominant != "tie" else "Tie in 4/4 modes")
        )
        max_advantage = max(_advantage_for_metric(summary, sort, metric)[1] for sort in SORTS)
        direction = "越高越好" if METRIC_SPECS[metric][1] else "越低越好"
        if language == "en":
            direction = "higher is better" if METRIC_SPECS[metric][1] else "lower is better"
        cards.append(
            f'<div class="metric-card"><strong>{labels[metric]}</strong>'
            f'<span class="winner-{dominant}">{text}</span>'
            f"<span>{'最大优势' if language == 'zh' else 'Max advantage'} {_pct(max_advantage)}, {direction}</span></div>"
        )
    headers = (
        ["路由模式", "吞吐目标", "成本目标", "时延目标", "TTFT 目标", "缓存结果"]
        if language == "zh"
        else ["Routing mode", "Throughput objective", "Cost objective", "Latency objective", "TTFT objective", "Cache result"]
    )
    row_html = []
    for sort in SORTS:
        cells = []
        for metric in ["throughput", "cost", "latency", "ttft", "cache"]:
            winner, advantage = _advantage_for_metric(summary, sort, metric)
            objective_metric = {"throughput": "throughput", "price": "cost", "latency": "latency", "ttft": "ttft"}[sort]
            goal_class = f" goal-cell goal-{winner}" if metric == objective_metric else ""
            name_class = winner
            delta_text = "持平" if language == "zh" and winner == "tie" else "tie" if winner == "tie" else f'{"优势" if language == "zh" else "advantage"} {_pct(advantage)}'
            cells.append(
                f'<td class="winner-cell{goal_class}"><span class="name {name_class}">{_provider(winner)}</span>'
                f'<span class="delta">{delta_text}</span></td>'
            )
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        row_html.append(f'<tr><td><strong>{label}</strong><br><span class="delta">{sort}</span></td>{"".join(cells)}</tr>')
    return f"""
<div class="conclusion-overview">
  <p class="conclusion-overview-title">{title}</p>
  <p class="conclusion-overview-note">{note}</p>
  <div class="metric-card-grid">
    {''.join(cards)}
  </div>
  <table class="winner-matrix">
    <thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead>
    <tbody>{''.join(row_html)}</tbody>
  </table>
</div>"""


def _method_diagram_zh(summary: dict[str, Any]) -> str:
    return f"""
<div class="method-diagram">
  <p class="method-diagram-title">图 1：实验设计与严格 A/B 配对过滤</p>
  <div class="method-flow">
    <div class="method-node primary"><strong>固定 Payload</strong><span>模型 {html.escape(summary['model'])}，同一路由模式下 payload SHA256 固定</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node accent"><strong>请求 A1/B1</strong><span>第一次请求建立或刷新缓存状态</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node good"><strong>请求 A2/B2</strong><span>第二次请求观测 cache read tokens 与 TTFT</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node warn"><strong>严格过滤</strong><span>只聚合 input-token 偏差不超过 50 的 A/B pairs</span></div>
  </div>
</div>"""


def _method_diagram_en(summary: dict[str, Any]) -> str:
    return f"""
<div class="method-diagram">
  <p class="method-diagram-title">Figure 1: Experimental Design and Strict A/B Pairing Filter</p>
  <div class="method-flow">
    <div class="method-node primary"><strong>Fixed Payload</strong><span>Model {html.escape(summary['model'])}; payload SHA-256 is fixed within each routing mode</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node accent"><strong>Request A1/B1</strong><span>First request establishes or refreshes cache state</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node good"><strong>Request A2/B2</strong><span>Second request observes cache-read tokens and TTFT</span></div>
    <div class="method-arrow">→</div>
    <div class="method-node warn"><strong>Strict Filter</strong><span>Only A/B pairs with input-token deltas up to 50 are aggregated</span></div>
  </div>
</div>"""


def _echarts_panels_zh() -> str:
    return """
<div class="echarts-academic-panel">
  <h3>5.1 核心指标图表总览</h3>
  <p class="echarts-academic-note">以下图表使用同一份严格配对后的 summary 数据生成，统一展示路由模式、平台差异、成本、缓存、端到端 E2E 时延、流式 TTFT 和上游 Provider 分布。</p>
  <div class="echarts-grid">
    <section class="echarts-figure wide"><p class="echarts-title">图 3-E1：路由模式级核心指标对比</p><p class="echarts-caption">按路由模式并列展示 Infron 与 OpenRouter。</p><div id="echarts-mode-metric" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">图 3-E2：归一化综合轮廓</p><p class="echarts-caption">五项指标统一转为 0-100 且越高越好。</p><div id="echarts-radar" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">图 3-E3：成本-缓存效率平面</p><p class="echarts-caption">横轴为 Token 级缓存命中率，纵轴为总实际成本。</p><div id="echarts-cost-cache" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">图 3-E4：端到端 E2E 时延与流式 TTFT</p><p class="echarts-caption">实线表示端到端 E2E 时延，虚线表示流式 TTFT。</p><div id="echarts-latency-ttft" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">图 3-E5：上游 Provider 分布</p><p class="echarts-caption">按路由模式展示主要上游路径占比。</p><div id="echarts-provider" class="echarts-chart"></div></section>
  </div>
</div>
<h3>模式级下钻图表</h3>
<p>横轴表示相对优势百分比：右侧蓝色代表 Infron 优势，左侧橙色代表 OpenRouter 优势。</p>
<div class="echarts-academic-panel route-detail-panel"><div class="route-detail-grid">
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">图 4-E1：Throughput First 路由模式下的核心指标对比</p><p class="echarts-caption">展示五项核心指标的相对优势方向与幅度。</p><div id="echarts-route-throughput" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">图 4-E2：Price First 路由模式下的核心指标对比</p><p class="echarts-caption">展示五项核心指标的相对优势方向与幅度。</p><div id="echarts-route-price" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">图 4-E3：Latency First 路由模式下的核心指标对比</p><p class="echarts-caption">展示五项核心指标的相对优势方向与幅度。</p><div id="echarts-route-latency" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">图 4-E4：TTFT First 路由模式下的核心指标对比</p><p class="echarts-caption">展示五项核心指标的相对优势方向与幅度。</p><div id="echarts-route-ttft" class="echarts-chart route-mode-chart"></div></section>
</div></div>"""


def _echarts_panels_en() -> str:
    return """
<div class="echarts-academic-panel">
  <h3>5.1 Core Metric Chart Overview</h3>
  <p class="echarts-academic-note">The charts below are generated from the same strict-paired summary data.</p>
  <div class="echarts-grid">
    <section class="echarts-figure wide"><p class="echarts-title">Figure 3-E1: Routing-mode core metric comparison</p><p class="echarts-caption">Infron and OpenRouter are shown side by side by routing mode.</p><div id="echarts-mode-metric" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">Figure 3-E2: Normalized capability contour</p><p class="echarts-caption">Five metrics are normalized to 0-100, where higher is better.</p><div id="echarts-radar" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">Figure 3-E3: Cost-cache efficiency plane</p><p class="echarts-caption">X-axis is token cache hit rate; Y-axis is observed total cost.</p><div id="echarts-cost-cache" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">Figure 3-E4: E2E latency and Streaming TTFT</p><p class="echarts-caption">Solid lines show E2E latency; dashed lines show Streaming TTFT.</p><div id="echarts-latency-ttft" class="echarts-chart"></div></section>
    <section class="echarts-figure"><p class="echarts-title">Figure 3-E5: Upstream provider distribution</p><p class="echarts-caption">Provider shares explain cache-domain and performance differences.</p><div id="echarts-provider" class="echarts-chart"></div></section>
  </div>
</div>
<h3>Routing-Mode Drill-Down Charts</h3>
<p>The horizontal axis shows relative advantage: blue to the right indicates Infron advantage, orange to the left indicates OpenRouter advantage.</p>
<div class="echarts-academic-panel route-detail-panel"><div class="route-detail-grid">
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">Figure 4-E1: Throughput First core metric comparison</p><p class="echarts-caption">Direction and magnitude of relative advantage across five metrics.</p><div id="echarts-route-throughput" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">Figure 4-E2: Price First core metric comparison</p><p class="echarts-caption">Direction and magnitude of relative advantage across five metrics.</p><div id="echarts-route-price" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">Figure 4-E3: Latency First core metric comparison</p><p class="echarts-caption">Direction and magnitude of relative advantage across five metrics.</p><div id="echarts-route-latency" class="echarts-chart route-mode-chart"></div></section>
  <section class="echarts-figure route-mode-figure"><p class="echarts-title">Figure 4-E4: TTFT First core metric comparison</p><p class="echarts-caption">Direction and magnitude of relative advantage across five metrics.</p><div id="echarts-route-ttft" class="echarts-chart route-mode-chart"></div></section>
</div></div>"""


def _architecture_panel_zh() -> str:
    return """
<div class="architecture-diagram">
  <p class="architecture-title">图 12：Infron 多 provider 路由与缓存控制面</p>
  <div class="architecture-flow">
    <div class="architecture-node primary"><strong>统一 API 入口</strong><span>OpenAI-compatible 请求进入网关，保留 usage、stream 和 provider routing 参数</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node policy"><strong>路由策略层</strong><span>按 throughput / price / latency / ttft 目标选择健康上游路径</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node cache"><strong>Provider Stick / Cache Affinity</strong><span>重复长前缀尽量落入稳定缓存域</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node provider"><strong>上游 Provider</strong><span>响应 telemetry 反馈 provider、usage、cost、latency 和 TTFT</span></div>
  </div>
</div>"""


def _architecture_panel_en() -> str:
    return """
<div class="architecture-diagram">
  <p class="architecture-title">Figure 12: Infron Multi-Provider Routing and Cache Control Plane</p>
  <div class="architecture-flow">
    <div class="architecture-node primary"><strong>Unified API Entry</strong><span>OpenAI-compatible requests enter the gateway with usage, stream, and provider routing parameters</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node policy"><strong>Routing Policy Layer</strong><span>Selects healthy upstream paths by throughput / price / latency / ttft objective</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node cache"><strong>Provider Stick / Cache Affinity</strong><span>Repeated long prefixes are kept in stable cache domains where possible</span></div>
    <div class="architecture-arrow">→</div>
    <div class="architecture-node provider"><strong>Upstream Provider</strong><span>Response telemetry reports provider, usage, cost, latency, and TTFT</span></div>
  </div>
</div>"""


def _environment_table(summary: dict[str, Any], language: str) -> str:
    tier_plan = summary.get("prompt_length_tier_plan") if isinstance(summary.get("prompt_length_tier_plan"), list) else []
    tier_text_zh = _tier_plan_text(tier_plan, "zh")
    tier_text_en = _tier_plan_text(tier_plan, "en")
    reasoning_text_zh = _reasoning_control_text(summary, "zh")
    reasoning_text_en = _reasoning_control_text(summary, "en")
    provider_models_zh = _provider_models_text(summary, "zh")
    provider_models_en = _provider_models_text(summary, "en")
    if language == "zh":
        rows = [
            ("模型", f"<code>{html.escape(summary['model'])}</code>"),
            ("平台实际模型 ID", provider_models_zh),
            ("平台", "Infron、OpenRouter"),
            ("API 协议", _api_protocols_text(summary, "zh")),
            ("路由模式", "、".join(SORT_LABEL_ZH[s] for s in SORTS)),
            ("实验组", str(summary["groups"])),
            ("每组轮数", str(summary["rounds_per_group"])),
            ("Workers", str(summary["execution_profile"]["workers"])),
            ("请求方式", "流式 Chat Completions，采集 TTFT"),
            ("Reasoning / Thinking 控制", reasoning_text_zh),
            ("Prompt 长度分层", tier_text_zh),
            ("剔除记录", str(summary.get("excluded_records", {}).get("total", 0))),
        ]
        return _html_table(["项目", "配置"], rows)
    rows = [
        ("Model", f"<code>{html.escape(summary['model'])}</code>"),
        ("Provider model IDs", provider_models_en),
        ("Platforms", "Infron and OpenRouter"),
        ("API protocol", _api_protocols_text(summary, "en")),
        ("Routing modes", ", ".join(SORT_LABEL_EN[s] for s in SORTS)),
        ("Groups", str(summary["groups"])),
        ("Rounds per group", str(summary["rounds_per_group"])),
        ("Workers", str(summary["execution_profile"]["workers"])),
        ("Request mode", "Streaming Chat Completions with TTFT collection"),
        ("Reasoning / thinking control", reasoning_text_en),
        ("Prompt length tiers", tier_text_en),
        ("Excluded records", str(summary.get("excluded_records", {}).get("total", 0))),
    ]
    return _html_table(["Item", "Configuration"], rows)


def _provider_models_text(summary: dict[str, Any], language: str) -> str:
    provider_models = summary.get("provider_model_ids")
    if not isinstance(provider_models, dict) or not provider_models:
        return f"<code>{html.escape(str(summary.get('model', '')))}</code>"
    parts = []
    for provider in PROVIDERS:
        model = str(provider_models.get(provider) or summary.get("model") or "")
        parts.append(f"{provider}: <code>{html.escape(model)}</code>")
    suffix = ""
    overrides = summary.get("provider_model_overrides")
    if isinstance(overrides, dict) and overrides:
        suffix = "（平台别名映射已记录）" if language == "zh" else " (provider alias mapping recorded)"
    return "; ".join(parts) + suffix


def _overview_table(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "平台", "严格配对轮数", "总 Input Tokens", "Token 级缓存命中率", "实际成本", "吞吐量", "端到端 E2E 时延", "流式 TTFT"]
        if language == "zh"
        else ["Routing mode", "Platform", "Strict pairs", "Total Input Tokens", "Token cache hit rate", "Observed cost", "Throughput", "E2E latency", "Streaming TTFT"]
    )
    rows = []
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        aggs = {provider: summary["results"][sort][provider]["aggregate"] for provider in PROVIDERS}
        for provider in ["infron", "openrouter"]:
            agg = aggs[provider]
            rows.append(
                (
                    label,
                    _provider_cell(summary, sort, provider),
                    str(agg["rounds"]),
                    str(agg["total_input_tokens"]),
                    _best_cell(provider, aggs, "token_cache_hit_rate", _pct(agg["token_cache_hit_rate"]), higher=True),
                    _best_cell(provider, aggs, "total_actual_cost_usd", _usd(agg["total_actual_cost_usd"]), higher=False),
                    _best_cell(provider, aggs, "avg_throughput_output_tokens_per_second", f'{agg["avg_throughput_output_tokens_per_second"]:.2f} tok/s', higher=True),
                    _best_cell(provider, aggs, "avg_request_latency_ms", _ms(agg["avg_request_latency_ms"]), higher=False),
                    _best_cell(provider, aggs, "avg_ttft_ms", _ms(agg["avg_ttft_ms"]), higher=False),
                )
            )
    return _html_table(headers, rows)


def _provider_table(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "平台", "总请求数", "已归因请求数", "Provider 分布"]
        if language == "zh"
        else ["Routing mode", "Platform", "Total requests", "Attributed requests", "Provider distribution"]
    )
    rows = []
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        for provider in ["infron", "openrouter"]:
            item = summary.get("provider_distribution", {}).get(sort, {}).get(provider, {})
            details = item.get("details") or []
            names = ", ".join(f"<code>{html.escape(str(d.get('provider')))}</code> {d.get('request_count', 0)}" for d in details)
            if not names:
                names = "未返回" if language == "zh" else "Not returned"
            rows.append(
                (
                    label,
                    _provider(provider),
                    str(item.get("total_requests", 0)),
                    str(item.get("total_attributed_requests", 0)),
                    names,
                )
            )
    return _html_table(headers, rows)


def _executive_outline(summary: dict[str, Any], language: str) -> str:
    rows = []
    tolerance = summary.get("execution_profile", {}).get("input_token_pair_tolerance", INPUT_TOKEN_PAIR_TOLERANCE)
    if language == "zh":
        rows = [
            ("控制变量", f"同一 <code>sort/group/round</code> 下 first/second <code>usage.prompt_tokens</code> 偏差不超过 {tolerance} tokens；总 Input Tokens 使用响应 telemetry。", "方法与数据质量章节"),
            ("缓存复用", _winner_sentence(summary, "cache", language), "总体指标与机制解释章节"),
            ("实际成本", _winner_sentence(summary, "cost", language), "总体指标与 Provider 下钻章节"),
            ("性能表现", _winner_sentence(summary, "throughput", language) + "；" + _winner_sentence(summary, "latency", language) + "；" + _winner_sentence(summary, "ttft", language), "结果可视化与统计检验章节"),
            ("归因边界", "报告只使用响应中可观测的 usage、cost、TTFT、latency、provider 字段和 cache tokens。", "Provider/Route 下钻分析章节"),
            ("业务含义", "长上下文、RAG 前缀、Agent 工具说明和高频模板请求应同时关注缓存命中率、成本、首包和端到端时延。", "讨论与结论章节"),
        ]
        return "<h3>结论大纲</h3>" + _html_table(["研究维度", "结论", "证据位置"], rows)
    rows = [
        ("Controls", f"First/second <code>usage.prompt_tokens</code> deltas are limited to {tolerance} tokens within each <code>sort/group/round</code> pair.", "Methods and data quality"),
        ("Cache reuse", _winner_sentence(summary, "cache", language), "Overall metrics and mechanism section"),
        ("Observed cost", _winner_sentence(summary, "cost", language), "Overall metrics and provider drill-down"),
        ("Performance", _winner_sentence(summary, "throughput", language) + "; " + _winner_sentence(summary, "latency", language) + "; " + _winner_sentence(summary, "ttft", language), "Charts and statistical tests"),
        ("Attribution boundary", "Claims use observable response telemetry: usage, cost, TTFT, latency, provider fields, and cache tokens.", "Provider/Route drill-down"),
        ("Business meaning", "Long-context, RAG-prefix, agent-tool, and high-frequency template workloads should evaluate cache rate, cost, first-token latency, and E2E latency together.", "Discussion and conclusion"),
    ]
    return "<h3>Executive Outline</h3>" + _html_table(["Dimension", "Conclusion", "Evidence"], rows)


def _route_mode_conclusions(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "目标", "缓存胜出", "成本胜出", "吞吐胜出", "E2E 时延胜出", "TTFT 胜出", "解读"]
        if language == "zh"
        else ["Routing mode", "Objective", "Cache winner", "Cost winner", "Throughput winner", "E2E latency winner", "TTFT winner", "Interpretation"]
    )
    rows = []
    for sort in SORTS:
        wins = {metric: _metric_winner(summary, sort, metric) for metric in ["cache", "cost", "throughput", "latency", "ttft"]}
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        rows.append(
            (
                label,
                _objective(sort, language),
                _strong(_provider(wins["cache"])),
                _strong(_provider(wins["cost"])),
                _strong(_provider(wins["throughput"])),
                _strong(_provider(wins["latency"])),
                _strong(_provider(wins["ttft"])),
                _mode_interpretation(wins, language),
            )
        )
    return ("<h3>路由模式级结论</h3>" if language == "zh" else "<h3>Routing-Mode Conclusions</h3>") + _html_table(headers, rows)


def _hypothesis_table(language: str) -> str:
    if language == "zh":
        return _html_table(
            ["假设", "内容", "验证指标"],
            [
                ("H1", "重复稳定长前缀请求中，更强的 provider/cache affinity 会提升 Token 级缓存命中率。", "第二次请求 cache read tokens、Token 级命中率"),
                ("H2", "更高缓存命中率会降低真实响应成本，但不必然降低 TTFT 或端到端 latency。", "实际成本、平均 TTFT、平均 latency/请求"),
                ("H3", "不同 routing sort 会改变 provider 选择，从而形成不同的成本、吞吐和时延 Pareto 前沿。", "provider 分布、throughput、latency、cost"),
            ],
        )
    return _html_table(
        ["Hypothesis", "Statement", "Validation metric"],
        [
            ("H1", "Stronger provider/cache affinity improves token-level cache hit rate for repeated stable prefixes.", "Second-request cache-read tokens and token cache hit rate"),
            ("H2", "Higher cache hit rate can reduce observed cost, but does not necessarily reduce TTFT or E2E latency.", "Observed cost, average TTFT, average request latency"),
            ("H3", "Different routing sorts change provider selection and produce different cost/throughput/latency frontiers.", "Provider distribution, throughput, latency, cost"),
        ],
    )


def _dataset_method(summary: dict[str, Any], language: str) -> str:
    dataset = summary.get("dataset", {})
    name = html.escape(str(dataset.get("name") or "business_representative"))
    if language == "zh":
        return (
            f"<p>数据集名称为 <code>{name}</code>，覆盖 4 种 routing sort、2 个平台、{summary['groups']} 个实验组、每组 {summary['rounds_per_group']} 轮。"
            "每轮包含 first/second 两次相同 Chat Completions 请求：第一次建立或刷新缓存状态，第二次观测 cache read tokens、TTFT 和端到端响应。</p>"
            "<p>业务模板覆盖稳定长上下文场景，包括 RAG 客服、Agent 工具说明、营销自动化和代码审查等高复用 prompt 结构。</p>"
        )
    return (
        f"<p>The dataset is <code>{name}</code>, covering 4 routing sorts, 2 platforms, {summary['groups']} groups, and {summary['rounds_per_group']} rounds per group. "
        "Each round sends identical first/second Chat Completions requests; the second request observes cache-read tokens, TTFT, and E2E latency.</p>"
        "<p>The built-in business templates represent stable long-context workloads such as RAG support, agent tool instructions, marketing automation, and code review.</p>"
    )


def _metric_definition_table(language: str) -> str:
    if language == "zh":
        return _html_table(
            ["指标", "定义", "解释方向"],
            [
                ("调用级命中率", "第二次请求 <code>cache_read_tokens &gt; 0</code> 的轮次占比", "越高表示越稳定触发缓存读取"),
                ("Token 级命中率", "第二次请求 cache read tokens / 第二次请求 prompt tokens", "越高表示输入 token 复用比例越高"),
                ("实际成本", "first + second 两次请求返回 usage/cost 的合计", "越低越好"),
                ("Throughput", "响应 completion tokens / 请求 latency seconds", "越高越好"),
                ("E2E latency", "每次请求完整响应耗时均值", "越低越好"),
                ("TTFT", "streaming 下首包/首 token 到达时间均值", "越低越好"),
                ("Reasoning 口径", "响应 usage 中的 reasoning token 字段保留为观测变量", "用于解释时延、吞吐和成本，不单独作为业务产出"),
            ],
        )
    return _html_table(
        ["Metric", "Definition", "Direction"],
        [
            ("Call cache hit rate", "Share of second requests with <code>cache_read_tokens &gt; 0</code>", "Higher is better"),
            ("Token cache hit rate", "Second-request cache-read tokens / second-request prompt tokens", "Higher is better"),
            ("Observed cost", "Sum of first + second request usage/cost values", "Lower is better"),
            ("Throughput", "Completion tokens / request latency seconds", "Higher is better"),
            ("E2E latency", "Full response latency per request", "Lower is better"),
            ("TTFT", "Streaming first-token arrival time", "Lower is better"),
            ("Reasoning telemetry", "Reasoning tokens from response usage", "Used to explain latency, throughput, and cost"),
        ],
    )


def _tail_latency_table(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "平台", "P50 Latency", "P95 Latency", "P99 Latency", "P50 TTFT", "P95 TTFT", "P99 TTFT"]
        if language == "zh"
        else ["Routing mode", "Platform", "P50 latency", "P95 latency", "P99 latency", "P50 TTFT", "P95 TTFT", "P99 TTFT"]
    )
    rows = []
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        aggs = {provider: summary["results"][sort][provider]["aggregate"] for provider in PROVIDERS}
        for provider in PROVIDERS:
            agg = aggs[provider]
            rows.append((
                label,
                _provider_cell(summary, sort, provider),
                _best_cell(provider, aggs, "p50_request_latency_ms", _ms(agg.get("p50_request_latency_ms")), higher=False),
                _best_cell(provider, aggs, "p95_request_latency_ms", _ms(agg.get("p95_request_latency_ms")), higher=False),
                _best_cell(provider, aggs, "p99_request_latency_ms", _ms(agg.get("p99_request_latency_ms")), higher=False),
                _best_cell(provider, aggs, "p50_ttft_ms", _ms(agg.get("p50_ttft_ms")), higher=False),
                _best_cell(provider, aggs, "p95_ttft_ms", _ms(agg.get("p95_ttft_ms")), higher=False),
                _best_cell(provider, aggs, "p99_ttft_ms", _ms(agg.get("p99_ttft_ms")), higher=False),
            ))
    caption = "<p>尾延迟分位数补充均值无法表达的尾部风险。</p>" if language == "zh" else "<p>Tail percentiles expose risk that averages hide.</p>"
    return caption + _html_table(headers, rows)


def _significance_table(summary: dict[str, Any], language: str) -> str:
    labels = {
        "latency_ms_delta_openrouter_minus_infron": ("Latency: OpenRouter - Infron", "正值表示 Infron latency 更低", "Positive means lower Infron latency"),
        "ttft_ms_delta_openrouter_minus_infron": ("TTFT: OpenRouter - Infron", "正值表示 Infron TTFT 更低", "Positive means lower Infron TTFT"),
        "throughput_delta_infron_minus_openrouter": ("Throughput: Infron - OpenRouter", "正值表示 Infron throughput 更高", "Positive means higher Infron throughput"),
        "cost_delta_openrouter_minus_infron_usd": ("Cost: OpenRouter - Infron", "正值表示 Infron 成本更低", "Positive means lower Infron cost"),
        "token_cache_hit_rate_delta_infron_minus_openrouter": ("Token Cache Hit: Infron - OpenRouter", "正值表示 Infron cache hit 更高", "Positive means higher Infron cache hit"),
    }
    headers = (
        ["路由模式", "指标", "均值差", "95% CI", "p-value", "配对数", "解释"]
        if language == "zh"
        else ["Routing mode", "Metric", "Mean delta", "95% CI", "p-value", "Pairs", "Interpretation"]
    )
    rows = []
    for sort in SORTS:
        tests = summary["results"][sort].get("statistical_tests", {})
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        for key, (metric, zh, en) in labels.items():
            item = tests.get(key, {})
            rows.append((label, metric, _signed_stat_cell(item.get("mean"), key), f"{_stat_value(item.get('ci95_low'), key)} to {_stat_value(item.get('ci95_high'), key)}", _p_value(item.get("paired_permutation_p_value")), str(item.get("n_pairs", 0)), zh if language == "zh" else en))
    note = "<p>均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。</p>" if language == "zh" else "<p>Mean deltas use bootstrap 95% CIs; p-values use paired sign-flip permutation tests.</p>"
    return note + _html_table(headers, rows)


def _reasoning_table(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "平台", "Reasoning Tokens", "平均 Reasoning Tokens/请求", "Reasoning 请求数", "平均首 Reasoning Token", "平均 TTFT", "平均 E2E 时延"]
        if language == "zh"
        else ["Routing mode", "Platform", "Reasoning tokens", "Avg reasoning tokens/request", "Reasoning requests", "Avg first reasoning token", "Avg TTFT", "Avg E2E latency"]
    )
    rows = []
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        aggs = {provider: summary["results"][sort][provider]["aggregate"] for provider in PROVIDERS}
        for provider in PROVIDERS:
            agg = aggs[provider]
            rows.append((
                label,
                _provider_cell(summary, sort, provider),
                _best_cell(provider, aggs, "total_reasoning_tokens", str(agg.get("total_reasoning_tokens", 0)), higher=False),
                _best_cell(provider, aggs, "avg_reasoning_tokens_per_request", f"{float(agg.get('avg_reasoning_tokens_per_request') or 0):.4f}", higher=False),
                _best_cell(provider, aggs, "reasoning_request_count", str(agg.get("reasoning_request_count", 0)), higher=False),
                _best_cell(provider, aggs, "avg_first_reasoning_token_ms", _ms(agg.get("avg_first_reasoning_token_ms")), higher=False),
                _best_cell(provider, aggs, "avg_ttft_ms", _ms(agg.get("avg_ttft_ms")), higher=False),
                _best_cell(provider, aggs, "avg_request_latency_ms", _ms(agg.get("avg_request_latency_ms")), higher=False),
            ))
    control = summary.get("reasoning_control") if isinstance(summary.get("reasoning_control"), dict) else {}
    if control.get("payload_includes_reasoning"):
        effort = html.escape(str(control.get("requested_effort") or "default"))
        note = (
            f"<p>请求显式设置 <code>reasoning.effort={effort}</code>；该表用于确认请求侧控制在响应 telemetry 中的实际表现。</p>"
            if language == "zh"
            else f"<p>Requests explicitly set <code>reasoning.effort={effort}</code>; this table checks how that request-side control appears in response telemetry.</p>"
        )
    else:
        note = (
            "<p>本轮未显式指定 reasoning/thinking 参数，保留模型与平台默认行为；该表记录默认行为下的 reasoning telemetry。</p>"
            if language == "zh"
            else "<p>This run does not explicitly set reasoning/thinking parameters and keeps model/platform defaults; this table records reasoning telemetry under default behavior.</p>"
        )
    return note + _html_table(headers, rows)


def _api_protocols_text(summary: dict[str, Any], language: str) -> str:
    protocols = summary.get("api_protocols") if isinstance(summary.get("api_protocols"), list) else ["chat_completions"]
    paths = summary.get("api_protocol_paths") if isinstance(summary.get("api_protocol_paths"), dict) else {}
    labels = []
    for protocol in protocols:
        path = paths.get(protocol) or {
            "messages": "/v1/messages",
            "chat_completions": "/v1/chat/completions",
            "responses": "/v1/responses",
        }.get(str(protocol), str(protocol))
        labels.append(f"<code>{html.escape(str(path))}</code>")
    if language == "zh":
        return "、".join(labels)
    return ", ".join(labels)


def _api_protocol_compatibility_table(summary: dict[str, Any], language: str) -> str:
    compatibility = summary.get("api_protocol_compatibility")
    if not isinstance(compatibility, dict) or not compatibility:
        return (
            "<p>本轮 API 协议为 <code>/v1/chat/completions</code>。</p>"
            if language == "zh"
            else "<p>This run uses <code>/v1/chat/completions</code> as the API protocol.</p>"
        )
    headers = (
        ["API 协议", "Endpoint", "平台", "配对轮数", "请求数", "成功率", "Usage 覆盖", "Token Usage 覆盖", "成本覆盖", "缓存 Telemetry 覆盖", "HTTP 状态", "主要错误"]
        if language == "zh"
        else ["API protocol", "Endpoint", "Platform", "Pairs", "Requests", "Success rate", "Usage coverage", "Token usage coverage", "Cost coverage", "Cache telemetry coverage", "HTTP statuses", "Top errors"]
    )
    rows = []
    for protocol, item in compatibility.items():
        if not isinstance(item, dict):
            continue
        providers = item.get("providers") if isinstance(item.get("providers"), dict) else {}
        provider_aggs = {
            provider: providers.get(provider, {}) if isinstance(providers.get(provider), dict) else {}
            for provider in PROVIDERS
        }
        for provider in PROVIDERS:
            agg = provider_aggs[provider]
            rows.append(
                [
                    f"<code>{html.escape(str(protocol))}</code>",
                    f"<code>{html.escape(str(item.get('endpoint_path') or ''))}</code>",
                    _provider(provider),
                    str(agg.get("pairs", 0)),
                    str(agg.get("request_count", 0)),
                    _best_cell(provider, provider_aggs, "success_rate", _pct(agg.get("success_rate", 0)), higher=True),
                    _best_cell(provider, provider_aggs, "usage_coverage", _pct(agg.get("usage_coverage", 0)), higher=True),
                    _best_cell(provider, provider_aggs, "token_usage_coverage", _pct(agg.get("token_usage_coverage", 0)), higher=True),
                    _best_cell(provider, provider_aggs, "cost_coverage", _pct(agg.get("cost_coverage", 0)), higher=True),
                    _best_cell(provider, provider_aggs, "cache_telemetry_coverage", _pct(agg.get("cache_telemetry_coverage", 0)), higher=True),
                    html.escape(json.dumps(agg.get("http_statuses", {}), ensure_ascii=False, separators=(",", ":"))),
                    _top_errors_text(agg.get("top_errors")),
                ]
            )
    protocol_paths = [str(item.get("endpoint_path") or "") for item in compatibility.values() if isinstance(item, dict)]
    has_multiple_protocols = len({path for path in protocol_paths if path}) > 1
    if has_multiple_protocols:
        intro = (
            "<p>本节按实际启用的 API 协议比较两家平台在成功响应、usage、成本和缓存 telemetry 上的兼容性。</p>"
            if language == "zh"
            else "<p>This section compares the actually enabled API protocols across success response, usage, cost, and cache telemetry compatibility.</p>"
        )
    else:
        intro = (
            "<p>本轮 API 协议为 <code>/v1/chat/completions</code>；本表记录两家平台在该协议下的成功响应、usage、成本和缓存 telemetry 覆盖。</p>"
            if language == "zh"
            else "<p>This run uses <code>/v1/chat/completions</code>; this table records success response, usage, cost, and cache telemetry coverage for both platforms under that protocol.</p>"
        )
    return intro + _html_table(headers, rows)


def _top_errors_text(errors: Any) -> str:
    if not isinstance(errors, list) or not errors:
        return ""
    parts = []
    for item in errors[:2]:
        if not isinstance(item, dict):
            continue
        parts.append(f"{html.escape(str(item.get('count', 0)))} x {html.escape(str(item.get('error', '')))}")
    return "<br>".join(parts)


def _cache_cost_mechanism(summary: dict[str, Any], language: str) -> str:
    if language == "zh":
        return (
            "<h3>6.1 多 provider 路由与可观测控制面</h3>"
            "<p>请求进入统一 API 后，路由策略层根据 throughput、price、latency 或 ttft 目标选择健康上游路径。稳定长前缀请求是否落在相同缓存域，会直接影响第二次请求的 cache read tokens。</p>"
            "<h3>6.2 Provider Stick 与 Cache Affinity</h3>"
            "<p>Provider stick 是缓存亲和策略，不等于固定锁死 provider。它的目标是在健康和 SLA 约束下减少缓存域碎片化，使重复 prefix 更容易复用已有缓存。</p>"
            "<h3>6.3 成本控制路径</h3>"
            + _html_table(["机制", "对 cache rate 的影响", "对成本的影响", "本次实验中的可观测信号"], [
                ("Stable prefix 识别", "相同前缀更容易命中已有 cache", "降低重复 prefill 的边际成本", "同一 payload SHA256、第二次请求 cache read tokens"),
                ("Provider stick / cache affinity", "降低跨 provider/cache domain 的缓存碎片", "减少重复暖缓存", "provider 分布与 Token 级命中率共同变化"),
                ("健康检查与 fallback", "保护可用性，必要时牺牲部分缓存收益", "降低失败成本", "HTTP 状态、provider 分布和尾延迟变化"),
                ("成本感知 routing", "在健康约束下偏向低成本路径", "降低总成本和每轮成本", "实际成本、cost breakdown 覆盖率、cache read tokens"),
            ])
        )
    return (
        "<h3>6.1 Multi-Provider Routing and Observable Control Plane</h3>"
        "<p>Requests enter a unified API, and the routing layer selects healthy upstream paths according to throughput, price, latency, or ttft objectives. Whether stable long prefixes stay in the same cache domain directly affects second-request cache-read tokens.</p>"
        "<h3>6.2 Provider Stick and Cache Affinity</h3>"
        "<p>Provider stick is cache affinity, not a permanent provider lock. Its goal is to reduce cache-domain fragmentation while respecting health and SLA constraints.</p>"
        "<h3>6.3 Cost-Control Path</h3>"
        + _html_table(["Mechanism", "Cache-rate effect", "Cost effect", "Observable signal"], [
            ("Stable prefix detection", "Repeated prefixes are more likely to hit cache", "Reduces repeated prefill cost", "Payload SHA-256 and second-request cache-read tokens"),
            ("Provider stick / cache affinity", "Reduces cross-domain cache fragmentation", "Avoids repeated cache warm-up", "Provider distribution and token cache hit rate"),
            ("Health checks and fallback", "Protects availability while sometimes sacrificing cache", "Reduces failure cost", "HTTP status, provider distribution, tail latency"),
            ("Cost-aware routing", "Prefers lower-cost paths under constraints", "Reduces total and per-round cost", "Observed cost, cost breakdown coverage, cache-read tokens"),
        ])
    )


def _provider_detail_table(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "平台", "上游 Provider", "请求数", "占比", "first/second", "覆盖轮次", "Avg TTFT", "Avg Latency", "Prompt Tokens", "Completion Tokens", "Reasoning Tokens", "Cache Read Tokens", "观测成本"]
        if language == "zh"
        else ["Routing mode", "Platform", "Upstream provider", "Requests", "Share", "first/second", "Covered rounds", "Avg TTFT", "Avg latency", "Prompt tokens", "Completion tokens", "Reasoning tokens", "Cache-read tokens", "Observed cost"]
    )
    rows = []
    distribution = summary.get("provider_distribution", {})
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        for provider in PROVIDERS:
            details = distribution.get(sort, {}).get(provider, {}).get("details") or []
            if not details:
                rows.append((label, _provider(provider), "Not returned" if language == "en" else "未返回", "0", "0.00%", "0/0", "0", "N/A", "N/A", "0", "0", "0", "0", "N/A"))
            for d in details:
                rows.append((label, _provider(provider), f"<code>{html.escape(str(d.get('provider') or 'unknown'))}</code>", str(d.get("request_count", 0)), _pct(d.get("request_share", 0) or 0), f"{d.get('first_request_count', 0)}/{d.get('second_request_count', 0)}", str(d.get("covered_rounds", 0)), _ms(d.get("avg_ttft_ms")), _ms(d.get("avg_latency_ms")), str(d.get("prompt_tokens", 0)), str(d.get("completion_tokens", 0)), str(d.get("reasoning_tokens", 0)), str(d.get("cache_read_tokens", 0)), _usd_or_na(d.get("observed_cost_usd"))))
    title = "<h3>上游 Provider 明细分布</h3>" if language == "zh" else "<h3>Upstream Provider Detail Distribution</h3>"
    return title + _html_table(headers, rows)


def _cache_cost_drilldown(summary: dict[str, Any], language: str) -> str:
    headers = (
        ["路由模式", "缓存命中差值", "Infron 成本倍数", "Infron 主要路径", "OpenRouter 主要路径", "Reasoning Tokens 差异", "主要归因"]
        if language == "zh"
        else ["Routing mode", "Cache-hit delta", "Infron cost multiple", "Infron top path", "OpenRouter top path", "Reasoning token delta", "Main attribution"]
    )
    rows = []
    for sort in SORTS:
        infron = summary["results"][sort]["infron"]["aggregate"]
        openrouter = summary["results"][sort]["openrouter"]["aggregate"]
        cache_delta = float(infron["token_cache_hit_rate"]) - float(openrouter["token_cache_hit_rate"])
        cost_multiple = _safe_div(infron.get("total_actual_cost_usd"), openrouter.get("total_actual_cost_usd"))
        reason_delta = int(infron.get("total_reasoning_tokens") or 0) - int(openrouter.get("total_reasoning_tokens") or 0)
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        rows.append((
            label,
            _strong_if(_signed_pp(cache_delta), cache_delta > 0),
            _strong_if(_multiple(cost_multiple), cost_multiple is not None and cost_multiple < 1),
            _strong_if(_top_provider(summary, sort, "infron"), cache_delta > 0 or (cost_multiple is not None and cost_multiple < 1)),
            _strong_if(_top_provider(summary, sort, "openrouter"), cache_delta < 0 or (cost_multiple is not None and cost_multiple > 1)),
            _strong_if(f"{reason_delta:+d}", reason_delta < 0),
            _diagnosis(summary, sort, language),
        ))
    title = "<h3>7.1 缓存命中率与实际成本反向表现下钻</h3>" if language == "zh" else "<h3>7.1 Cache-Rate and Cost Divergence Drill-Down</h3>"
    note = "<p>该表把 cache、cost、provider 分布和 reasoning telemetry 放在同一层级，解释每个路由模式的主要差异来源。</p>" if language == "zh" else "<p>This table combines cache, cost, provider distribution, and reasoning telemetry to explain routing-mode differences.</p>"
    return title + note + _html_table(headers, rows)


def _prompt_length_tier_table(summary: dict[str, Any], language: str) -> str:
    tiers = summary.get("prompt_length_tiers") if isinstance(summary.get("prompt_length_tiers"), dict) else {}
    if not tiers:
        message = "本轮未启用 prompt 长度分层。" if language == "zh" else "Prompt-length stratification was not enabled for this run."
        return f"<p>{message}</p>"
    if language == "zh":
        intro = "<p>本节按 prompt 长度 tier 聚合第二次请求的 cache read tokens、Token 级缓存命中率、实际成本、端到端时延和流式 TTFT。加粗单元表示同一长度 tier 下表现更优的一方。</p>"
        headers = ["Prompt 长度 tier", "目标 tokens", "平台", "轮数", "第二次 Prompt Tokens", "第二次 Cache Read Tokens", "Token 级命中率", "实际成本", "平均 E2E 时延", "平均 TTFT"]
        matrix_headers = ["Prompt 长度 tier", "路由模式", "Infron", "OpenRouter", "胜出方"]
        heading = "<h3>Prompt 长度分层总览</h3>"
        matrix_heading = "<h3>Prompt 长度 x 路由模式缓存命中率</h3>"
    else:
        intro = "<p>This section aggregates second-request cache-read tokens, token-level cache hit rate, observed cost, E2E latency, and Streaming TTFT by prompt-length tier. Bold cells mark the advantaged side within each tier.</p>"
        headers = ["Prompt length tier", "Target tokens", "Platform", "Pairs", "Second prompt tokens", "Second cache read tokens", "Token cache hit rate", "Observed cost", "Avg E2E latency", "Avg TTFT"]
        matrix_headers = ["Prompt length tier", "Routing mode", "Infron", "OpenRouter", "Winner"]
        heading = "<h3>Prompt-Length Tier Overview</h3>"
        matrix_heading = "<h3>Prompt Length x Routing Mode Cache Hit Rate</h3>"
    rows = []
    for label, item in _sorted_tier_items(tiers):
        provider_aggs = item.get("providers") if isinstance(item.get("providers"), dict) else {}
        for provider in PROVIDERS:
            agg = provider_aggs.get(provider, {}) if isinstance(provider_aggs.get(provider), dict) else {}
            rows.append((
                f"<code>{html.escape(str(label))}</code>",
                str(item.get("target_prompt_tokens") or ""),
                _provider(provider),
                _best_cell(provider, provider_aggs, "rounds", str(agg.get("rounds", 0)), higher=True),
                _best_cell(provider, provider_aggs, "second_prompt_tokens", str(agg.get("second_prompt_tokens", 0)), higher=True),
                _best_cell(provider, provider_aggs, "second_cache_read_tokens", str(agg.get("second_cache_read_tokens", 0)), higher=True),
                _best_cell(provider, provider_aggs, "token_cache_hit_rate", _pct(agg.get("token_cache_hit_rate", 0)), higher=True),
                _best_cell(provider, provider_aggs, "total_actual_cost_usd", _usd_or_na(agg.get("total_actual_cost_usd")), higher=False),
                _best_cell(provider, provider_aggs, "avg_request_latency_ms", _ms(agg.get("avg_request_latency_ms")), higher=False),
                _best_cell(provider, provider_aggs, "avg_ttft_ms", _ms(agg.get("avg_ttft_ms")), higher=False),
            ))
    matrix_rows = []
    for label, item in _sorted_tier_items(tiers):
        sort_modes = item.get("sort_modes") if isinstance(item.get("sort_modes"), dict) else {}
        for sort in SORTS:
            provider_aggs = sort_modes.get(sort, {}) if isinstance(sort_modes.get(sort), dict) else {}
            infron = provider_aggs.get("infron", {}) if isinstance(provider_aggs.get("infron"), dict) else {}
            openrouter = provider_aggs.get("openrouter", {}) if isinstance(provider_aggs.get("openrouter"), dict) else {}
            winner = _winner_from_values(infron.get("token_cache_hit_rate"), openrouter.get("token_cache_hit_rate"), higher=True)
            sort_label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
            matrix_rows.append((
                f"<code>{html.escape(str(label))}</code>",
                sort_label,
                _best_cell("infron", provider_aggs, "token_cache_hit_rate", _pct(infron.get("token_cache_hit_rate", 0)), higher=True),
                _best_cell("openrouter", provider_aggs, "token_cache_hit_rate", _pct(openrouter.get("token_cache_hit_rate", 0)), higher=True),
                _strong(_provider(winner)) if winner in PROVIDERS else html.escape(str(winner)),
            ))
    return intro + heading + _html_table(headers, rows) + matrix_heading + _html_table(matrix_headers, matrix_rows)


def _group_stability_tables(summary: dict[str, Any], language: str) -> str:
    chunks = []
    for sort in SORTS:
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        rows = []
        groups_by_provider = {
            provider: {int(group["group"]): group["aggregate"] for group in summary["results"][sort][provider]["groups"]}
            for provider in PROVIDERS
        }
        for provider in PROVIDERS:
            for group in summary["results"][sort][provider]["groups"]:
                agg = group["aggregate"]
                group_no = int(group["group"])
                peers = {peer: groups_by_provider[peer].get(group_no, {}) for peer in PROVIDERS}
                rows.append((
                    _provider(provider),
                    str(group["group"]),
                    str(agg["rounds"]),
                    str(agg["successful_rounds"]),
                    _best_cell(provider, peers, "token_cache_hit_rate", _pct(agg["token_cache_hit_rate"]), higher=True),
                    _best_cell(provider, peers, "total_actual_cost_usd", _usd_or_na(agg.get("total_actual_cost_usd")), higher=False),
                    _best_cell(provider, peers, "p95_request_latency_ms", _ms(agg.get("p95_request_latency_ms")), higher=False),
                    _best_cell(provider, peers, "p95_ttft_ms", _ms(agg.get("p95_ttft_ms")), higher=False),
                ))
        headers = ["平台", "组别", "轮数", "成功轮数", "Token 命中率", "实际成本", "P95 Latency", "P95 TTFT"] if language == "zh" else ["Platform", "Group", "Rounds", "Successful rounds", "Token cache hit rate", "Observed cost", "P95 latency", "P95 TTFT"]
        chunks.append(f"<h3>{label}</h3>" + _html_table(headers, rows))
    return "".join(chunks)


def _business_discussion(summary: dict[str, Any], language: str) -> str:
    rows = []
    for sort in SORTS:
        wins = {metric: _metric_winner(summary, sort, metric) for metric in ["cache", "cost", "throughput", "latency", "ttft"]}
        label = SORT_LABEL_ZH[sort] if language == "zh" else SORT_LABEL_EN[sort]
        rows.append((label, _objective(sort, language), _mode_interpretation(wins, language), _scenario(sort, language), _tradeoff(wins, language)))
    if language == "zh":
        return "<p>业务决策不应只看单一指标。稳定长上下文和高频模板请求优先关注缓存命中率与成本；实时交互应同时约束 TTFT 和端到端时延；后台批处理更重视吞吐与失败成本。</p>" + _html_table(["路由模式", "主要业务目标", "本轮数据体现", "适用场景", "注意事项"], rows)
    return "<p>Business decisions should not rely on one metric. Stable long-context and high-frequency template workloads should prioritize cache rate and cost; realtime interaction must constrain TTFT and E2E latency; batch processing often prioritizes throughput and failure cost.</p>" + _html_table(["Routing mode", "Business objective", "Observed result", "Scenarios", "Caveat"], rows)


def _final_conclusion_table(summary: dict[str, Any], language: str) -> str:
    return _route_mode_conclusions(summary, language)


def _limitations_table(summary: dict[str, Any], language: str) -> str:
    if language == "zh":
        return _html_table(["缺失或不足", "对结论的影响", "后续补充方式", "当前处理方式"], [
            ("完整 routing trace", "无法逐跳证明每次请求的 provider 选择、fallback 和重试路径", "补充 provider routing trace、decision log 和 fallback reason", "只使用响应中真实返回的 provider 字段和 provider 分布"),
            ("更长时间窗口", "4x50 能观察短期稳定性，但不能覆盖日级波动", "增加 soak test 和跨时段重复实验", "报告限定在本轮窗口内解释"),
            ("真实生产语料", "内置模板不能覆盖全部业务分布", "使用脱敏生产语料分层抽样", "当前只讨论代表性长上下文业务模板"),
            ("成本字段一致性", "不同平台 cost 字段覆盖率和口径可能不同", "结合账单回查和 provider cost breakdown", "只统计响应明确返回的成本字段"),
        ])
    return _html_table(["Limitation", "Impact", "Next step", "Current handling"], [
        ("Full routing trace", "Cannot prove every provider choice, fallback, and retry path hop by hop", "Add provider routing trace, decision logs, and fallback reasons", "Use only returned provider fields and provider distribution"),
        ("Longer time window", "4x50 observes short-window stability but not day-level drift", "Add soak tests and repeated windows", "Scope conclusions to this run"),
        ("Production corpus", "Built-in templates do not cover every workload distribution", "Use sanitized production-stratified corpora", "Discuss representative long-context templates only"),
        ("Cost-field consistency", "Cost coverage and semantics may differ by platform", "Reconcile with billing and provider cost breakdown", "Use only explicitly returned cost fields"),
    ])


def _repro_table(language: str) -> str:
    if language == "zh":
        return _html_table(
            ["工件", "路径"],
            [
                ("Summary", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/summary.json</code>"),
                ("配对数据集", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/benchmark_pairs.csv</code>"),
                ("请求级数据集", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/benchmark_requests.jsonl</code>"),
                ("过滤后结构化记录", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/records.json</code>"),
                ("剔除记录审计", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/records_excluded.json</code>"),
                ("测试源码", "<code>tests/test_rerun_routing_sort_cache_cost_ab.py</code>"),
                ("Benchmark 执行源码", "<code>scripts/rerun_routing_sort_cache_cost_ab.py</code>"),
                ("HTML 报告渲染源码", "<code>scripts/render_glm52_deepseek_style_report.py</code>"),
                ("数据集引用", "<code>business_representative</code> 内置代表性业务模板；请求级导出见 <code>benchmark_requests.jsonl</code>"),
            ],
        )
    return _html_table(
        ["Artifact", "Path"],
        [
            ("Summary", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/summary.json</code>"),
            ("Paired dataset", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/benchmark_pairs.csv</code>"),
            ("Request-level dataset", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/benchmark_requests.jsonl</code>"),
            ("Filtered structured records", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/records.json</code>"),
            ("Excluded-record audit", f"<code>{RUN_DIR.relative_to(ROOT).as_posix()}/records_excluded.json</code>"),
            ("Test source", "<code>tests/test_rerun_routing_sort_cache_cost_ab.py</code>"),
            ("Benchmark runner source", "<code>scripts/rerun_routing_sort_cache_cost_ab.py</code>"),
            ("HTML report renderer source", "<code>scripts/render_glm52_deepseek_style_report.py</code>"),
            ("Dataset reference", "<code>business_representative</code> built-in representative business templates; request-level export is <code>benchmark_requests.jsonl</code>"),
        ],
    )


def _metric_winner(summary: dict[str, Any], sort: str, metric: str) -> str:
    winner, _ = _advantage_for_metric(summary, sort, metric)
    return winner


def _winner_sentence(summary: dict[str, Any], metric: str, language: str) -> str:
    wins = _winner_counts(summary, metric)
    label = METRIC_LABEL_ZH[metric] if language == "zh" else METRIC_LABEL_EN[metric]
    if wins["tie"] == 4:
        return f"Infron 与 OpenRouter 在所有路由模式下{label}持平" if language == "zh" else f"Infron and OpenRouter tie on {label} in all routing modes"
    if wins["infron"] == 4:
        return f"Infron 在所有路由模式下{label}占优" if language == "zh" else f"Infron leads {label} in all routing modes"
    if wins["openrouter"] == 4:
        return f"OpenRouter 在所有路由模式下{label}占优" if language == "zh" else f"OpenRouter leads {label} in all routing modes"
    return (
        f"Infron 在 {wins['infron']}/4 个路由模式下{label}占优，OpenRouter 在 {wins['openrouter']}/4 个路由模式下占优，{wins['tie']}/4 个路由模式持平"
        if language == "zh"
        else f"Infron leads {label} in {wins['infron']}/4 routing modes; OpenRouter leads in {wins['openrouter']}/4; {wins['tie']}/4 tie"
    )


def _objective(sort: str, language: str) -> str:
    zh = {
        "throughput": "最大化单位时间输出能力",
        "price": "最小化单位请求和单位 token 成本",
        "latency": "最小化完整响应等待时间",
        "ttft": "最小化流式首包响应时间",
    }
    en = {
        "throughput": "Maximize output capacity per unit time",
        "price": "Minimize request and token cost",
        "latency": "Minimize full-response waiting time",
        "ttft": "Minimize streaming first-token time",
    }
    return (zh if language == "zh" else en)[sort]


def _scenario(sort: str, language: str) -> str:
    zh = {
        "throughput": "批量内容生成、离线摘要、后台数据加工",
        "price": "高频模板化请求、客服自动化、营销触达、RAG 固定前缀",
        "latency": "在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具",
        "ttft": "流式聊天、实时 Copilot、首屏反馈、长任务进度感知",
    }
    en = {
        "throughput": "Batch generation, offline summaries, backend processing",
        "price": "High-frequency templates, support automation, marketing, RAG prefixes",
        "latency": "Online chat, agent chains, IDE/writing assistants, realtime tools",
        "ttft": "Streaming chat, realtime copilots, first-screen feedback",
    }
    return (zh if language == "zh" else en)[sort]


def _mode_interpretation(wins: dict[str, str], language: str) -> str:
    infron = sum(1 for value in wins.values() if value == "infron")
    openrouter = sum(1 for value in wins.values() if value == "openrouter")
    if language == "zh":
        if infron > openrouter:
            return f"Infron 综合占优（{infron}/5 指标）"
        if openrouter > infron:
            return f"OpenRouter 综合占优（{openrouter}/5 指标）"
        return "双方各有优势"
    if infron > openrouter:
        return f"Infron leads overall ({infron}/5 metrics)"
    if openrouter > infron:
        return f"OpenRouter leads overall ({openrouter}/5 metrics)"
    return "Mixed result"


def _tradeoff(wins: dict[str, str], language: str) -> str:
    if wins["cache"] == "infron" and wins["cost"] == "infron":
        return "缓存和成本更稳，但仍需检查速度 SLA" if language == "zh" else "Cache and cost are stronger; still check speed SLA"
    if wins["latency"] == "openrouter" and wins["ttft"] == "openrouter":
        return "首包与完整响应更快，但需检查缓存和成本" if language == "zh" else "First-token and E2E response are faster; check cache and cost"
    if wins["throughput"] == "openrouter":
        return "适合吞吐优先任务，但成本和缓存需单独约束" if language == "zh" else "Good for throughput-first tasks; constrain cost and cache separately"
    return "需要结合预算、SLA 和缓存稳定性决策" if language == "zh" else "Decide with budget, SLA, and cache stability together"


def _safe_div(a: Any, b: Any) -> float | None:
    aa = _number(a)
    bb = _number(b)
    if aa is None or bb in (None, 0):
        return None
    return aa / float(bb)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stat_value(value: Any, key: str) -> str:
    numeric = _number(value)
    if numeric is None:
        return "N/A"
    if "cost" in key:
        return f"${numeric:.8f}"
    if "cache_hit_rate" in key:
        return f"{numeric * 100:.2f} pp"
    if "throughput" in key:
        return f"{numeric:.4f} tok/s"
    return f"{numeric:.2f} ms"


def _p_value(value: Any) -> str:
    numeric = _number(value)
    if numeric is None:
        return "N/A"
    if numeric < 0.001:
        return "<0.001"
    return f"{numeric:.4f}"


def _signed_pp(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def _multiple(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}x"


def _top_provider(summary: dict[str, Any], sort: str, provider: str) -> str:
    counts = summary.get("provider_distribution", {}).get(sort, {}).get(provider, {}).get("counts") or {}
    if not counts:
        return "未返回"
    name, count = max(counts.items(), key=lambda item: int(item[1]))
    total = sum(int(v) for v in counts.values()) or 1
    return f"<code>{html.escape(str(name))}</code> {_pct(count / total)}"


def _diagnosis(summary: dict[str, Any], sort: str, language: str) -> str:
    infron = summary["results"][sort]["infron"]["aggregate"]
    openrouter = summary["results"][sort]["openrouter"]["aggregate"]
    cache_delta = float(infron["token_cache_hit_rate"]) - float(openrouter["token_cache_hit_rate"])
    cost_multiple = _safe_div(infron.get("total_actual_cost_usd"), openrouter.get("total_actual_cost_usd"))
    if language == "zh":
        if cache_delta == 0 and cost_multiple and cost_multiple < 1:
            return "双方缓存持平，Infron 成本占优"
        if cache_delta > 0 and (cost_multiple is None or cost_multiple <= 1):
            return "Infron 缓存与成本同向占优"
        if cache_delta < 0 and cost_multiple and cost_multiple > 1:
            return "OpenRouter 缓存更高且成本更低，主要看 provider/cache 域差异"
        if cache_delta >= 0 and cost_multiple and cost_multiple > 1:
            return "Infron 缓存更高但成本更高，需检查上游单价、completion/reasoning tokens"
        return "缓存和成本方向存在分化，需结合速度指标判断"
    if cache_delta == 0 and cost_multiple and cost_multiple < 1:
        return "Cache is tied; Infron leads cost"
    if cache_delta > 0 and (cost_multiple is None or cost_multiple <= 1):
        return "Infron leads both cache and cost"
    if cache_delta < 0 and cost_multiple and cost_multiple > 1:
        return "OpenRouter has higher cache and lower cost; provider/cache-domain mix is the main signal"
    if cache_delta >= 0 and cost_multiple and cost_multiple > 1:
        return "Infron has higher cache but higher cost; inspect upstream unit price and completion/reasoning tokens"
    return "Cache and cost move in different directions; evaluate with speed metrics"


def _strong(value: Any) -> str:
    return f"<strong>{value}</strong>"


def _strong_if(value: Any, condition: bool) -> str:
    return _strong(value) if condition else str(value)


def _best_cell(provider: str, provider_aggs: dict[str, dict[str, Any]], key: str, text: str, *, higher: bool) -> str:
    values = {
        item: _number(agg.get(key))
        for item, agg in provider_aggs.items()
        if isinstance(agg, dict) and _number(agg.get(key)) is not None
    }
    current = values.get(provider)
    if current is None or len(values) < 2:
        return text
    best = max(values.values()) if higher else min(values.values())
    return _strong_if(text, current == best)


def _provider_cell(summary: dict[str, Any], sort: str, provider: str) -> str:
    wins = [_metric_winner(summary, sort, metric) for metric in ["cache", "cost", "throughput", "latency", "ttft"]]
    return _strong_if(_provider(provider), wins.count(provider) >= 3)


def _signed_stat_cell(value: Any, key: str) -> str:
    numeric = _number(value)
    text = _stat_value(value, key)
    if numeric is None or numeric == 0:
        return text
    # All statistical deltas are defined so that positive values are Infron-favorable.
    return _strong(text)


def _html_table(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _model_label(summary: dict[str, Any]) -> str:
    model = str(summary.get("model") or "")
    if not model:
        return "LLM"
    return model.split("/")[-1] if "/" in model else model


def _tier_plan_text(tier_plan: list[Any], language: str) -> str:
    if not tier_plan:
        return "未启用" if language == "zh" else "Not enabled"
    parts = []
    for item in tier_plan:
        if not isinstance(item, dict):
            continue
        label = html.escape(str(item.get("label", "")))
        target = html.escape(str(item.get("target_prompt_tokens", "")))
        parts.append(f"<code>{label}</code>≈{target}")
    return "、".join(parts) if language == "zh" else ", ".join(parts)


def _reasoning_control_text(summary: dict[str, Any], language: str) -> str:
    control = summary.get("reasoning_control") if isinstance(summary.get("reasoning_control"), dict) else {}
    if control.get("payload_includes_reasoning"):
        effort = html.escape(str(control.get("requested_effort") or "default"))
        if language == "zh":
            return f"请求显式携带 <code>reasoning.effort={effort}</code>；响应侧是否生效以 usage telemetry 为准"
        return f"Requests explicitly include <code>reasoning.effort={effort}</code>; effectiveness is measured from response usage telemetry"
    if language == "zh":
        return "未显式指定 reasoning/thinking 参数；保留模型与平台默认行为"
    return "No explicit reasoning/thinking parameter; model and platform defaults are preserved"


def _sorted_tier_items(tiers: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return sorted(
        ((str(label), item) for label, item in tiers.items() if isinstance(item, dict)),
        key=lambda pair: (pair[1].get("index") is None, pair[1].get("index") or 0, pair[0]),
    )


def _winner_from_values(a: Any, b: Any, *, higher: bool) -> str:
    av = _number(a)
    bv = _number(b)
    if av is None or bv is None:
        return "N/A"
    if av == bv:
        return "tie"
    if higher:
        return "infron" if av > bv else "openrouter"
    return "infron" if av < bv else "openrouter"


def _winner_counts(summary: dict[str, Any], metric: str) -> dict[str, int]:
    counts = {"infron": 0, "openrouter": 0, "tie": 0}
    for sort in SORTS:
        winner, _ = _advantage_for_metric(summary, sort, metric)
        counts[winner] += 1
    return counts


def _dominant_winner(wins: dict[str, int]) -> str:
    if wins.get("tie", 0) >= wins.get("infron", 0) and wins.get("tie", 0) >= wins.get("openrouter", 0):
        return "tie"
    return "infron" if wins.get("infron", 0) >= wins.get("openrouter", 0) else "openrouter"


def _advantage_for_metric(summary: dict[str, Any], sort: str, metric: str) -> tuple[str, float]:
    key, higher, _ = METRIC_SPECS[metric]
    infron = _agg(summary, sort, "infron", key)
    openrouter = _agg(summary, sort, "openrouter", key)
    if infron == openrouter:
        return "tie", 0.0
    if higher:
        winner = "infron" if infron > openrouter else "openrouter"
        loser_value = openrouter if winner == "infron" else infron
        winner_value = infron if winner == "infron" else openrouter
    else:
        winner = "infron" if infron < openrouter else "openrouter"
        loser_value = openrouter if winner == "infron" else infron
        winner_value = infron if winner == "infron" else openrouter
    if loser_value <= 0 or winner_value <= 0:
        return winner, 0.0
    advantage = winner_value / loser_value - 1 if higher else loser_value / winner_value - 1
    return winner, max(0.0, advantage)


def _agg(summary: dict[str, Any], sort: str, provider: str, key: str) -> float:
    value = summary["results"][sort][provider]["aggregate"].get(key)
    if value is None:
        return 0.0
    return float(value)


def _pair_count() -> int:
    with (RUN_DIR / "benchmark_pairs.csv").open(newline="", encoding="utf-8") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _provider(provider: str) -> str:
    if provider == "infron":
        return "Infron"
    if provider == "openrouter":
        return "OpenRouter"
    if provider == "tie":
        return "Tie"
    return str(provider)


def _pct(value: float) -> str:
    return f"{float(value) * 100:.2f}%" if abs(float(value)) <= 1.5 else f"{float(value):.2f}%"


def _usd(value: float) -> str:
    return _usd_or_na(value)


def _usd_or_na(value: Any) -> str:
    numeric = _number(value)
    if numeric is None:
        return "N/A"
    return f"${numeric:.8f}"


def _ms(value: Any) -> str:
    numeric = _number(value)
    if numeric is None:
        return "N/A"
    return f"{numeric:.2f} ms"


def _round(value: float, digits: int) -> float:
    return round(float(value or 0), digits)


if __name__ == "__main__":
    raise SystemExit(main())
