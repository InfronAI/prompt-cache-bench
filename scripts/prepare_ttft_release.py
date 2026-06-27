#!/usr/bin/env python3
"""Stage the 2026-06-27 TTFT routing benchmark public release."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GROWTHPULSE = ROOT.parents[2]
SOURCE_RUN = GROWTHPULSE / "export/deepseek_v4_flash_all_experiments/routing_sort_cache_cost_ab_4x50_stream_ttft_1782548941"
SOURCE_SCRIPT = GROWTHPULSE / "scripts/rerun_routing_sort_cache_cost_ab.py"
EXPERIMENT_ID = "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-ttft-2026-06-27"
EXPERIMENT_DIR = ROOT / "experiments/deepseek/deepseek-v4-flash" / EXPERIMENT_ID
REPORT_STEM = "prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream-ttft__2026-06-27"
REPO_URL = "https://github.com/InfronAI/prompt-cache-bench"
PAGES_BASE = "https://infronai.github.io/prompt-cache-bench"
PUBLIC_RUNNER_HELPERS = r'''
class Settings:
    def __init__(self) -> None:
        env = _load_dotenv()
        self.model_probe_base_url = _env(env, "INFRON_BASE_URL", "https://api.infron.ai/v1")
        self.model_probe_api_key = _env(env, "INFRON_API_KEY")
        self.openrouter_base_url = _env(env, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openrouter_api_key = _env(env, "OPENROUTER_API_KEY")
        self.openrouter_http_referer = _env(env, "OPENROUTER_HTTP_REFERER", "https://github.com/InfronAI/prompt-cache-bench")
        self.openrouter_app_title = _env(env, "OPENROUTER_APP_TITLE", "prompt-cache-bench")
        self.model_probe_infron_cache_policy = _env(env, "INFRON_CACHE_POLICY", "enabled")
        self.model_probe_openrouter_cache_policy = _env(env, "OPENROUTER_CACHE_POLICY", "enabled")
        self.model_probe_infron_proxy_url = _env(env, "INFRON_PROXY_URL")
        self.model_probe_openrouter_proxy_url = _env(env, "OPENROUTER_PROXY_URL")


def load_settings() -> Settings:
    return Settings()


def _load_dotenv() -> dict[str, str]:
    env = dict(os.environ)
    path = Path(".env")
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env.setdefault(key.strip(), value.strip().strip("'\""))
    return env


def _env(env: dict[str, str], key: str, default: str | None = None) -> str | None:
    value = env.get(key)
    return value if value not in {None, ""} else default


def _actual_cost_value(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    direct = payload.get("cost")
    if isinstance(direct, int | float) and not isinstance(direct, bool):
        return float(direct)
    usage = payload.get("usage")
    if isinstance(usage, dict) and isinstance(usage.get("cost"), int | float):
        return float(usage["cost"])
    return None


def _usage_value(payload: Any, *keys: str) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    usage = payload.get("usage")
    if isinstance(usage, dict):
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
    return None


def _cache_read_tokens(payload: Any) -> int:
    return _sum_numeric_fields(
        payload,
        {
            "cached_tokens",
            "cache_read_tokens",
            "cache_read_input_tokens",
            "input_cache_read_tokens",
            "prompt_cache_read_tokens",
        },
    )


def _cache_write_tokens(payload: Any) -> int:
    return _sum_numeric_fields(
        payload,
        {
            "cache_write_tokens",
            "cache_creation_input_tokens",
            "input_cache_write_tokens",
            "prompt_cache_write_tokens",
            "prompt_cache_write_1h_tokens",
            "prompt_cache_write_5m_tokens",
        },
    )


def _reasoning_tokens(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
    completion_details = usage.get("completion_tokens_details")
    if isinstance(completion_details, dict) and isinstance(completion_details.get("reasoning_tokens"), int):
        return int(completion_details["reasoning_tokens"])
    for key in ("reasoning_tokens", "thinking_tokens"):
        value = usage.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _sum_numeric_fields(payload: Any, field_names: set[str]) -> int:
    total = 0
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if key in field_names and isinstance(value, int | float) and not isinstance(value, bool):
                    total += int(value)
                elif isinstance(value, dict | list):
                    stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return total
'''

SORT_LABEL_ZH = {
    "throughput": "吞吐优先",
    "price": "成本优先",
    "latency": "端到端 E2E 时延优先",
    "ttft": "流式 TTFT 优先",
}
SORT_LABEL_EN = {
    "throughput": "Throughput First",
    "price": "Price First",
    "latency": "Latency First",
    "ttft": "TTFT First",
}


def main() -> int:
    summary = json.loads((SOURCE_RUN / "summary.json").read_text(encoding="utf-8"))
    _ensure_tree()
    _copy_data()
    _copy_figures()
    _write_public_runner()
    _copy_code_snapshots()
    _write_data_readme(summary)
    _write_reports(summary)
    _write_reports_readme()
    _write_experiment_readme(summary)
    _write_manifest(summary)
    _update_env_example()
    _update_validate_default()
    _update_readme()
    _update_index()
    print(json.dumps({"experiment_dir": str(EXPERIMENT_DIR), "report_stem": REPORT_STEM}, ensure_ascii=False, indent=2))
    return 0


def _ensure_tree() -> None:
    for name in ["reports", "data", "figures", "code", "metadata"]:
        (EXPERIMENT_DIR / name).mkdir(parents=True, exist_ok=True)


def _copy_data() -> None:
    data_files = [
        "benchmark_pairs.csv",
        "benchmark_requests.jsonl",
        "records.json",
        "records_anomalous_usage.json",
        "records_excluded.json",
        "records_incomplete.json",
        "records_unequal_input_tokens.json",
        "summary.json",
    ]
    for name in data_files:
        shutil.copy2(SOURCE_RUN / name, EXPERIMENT_DIR / "data" / name)


def _copy_figures() -> None:
    for src in sorted((SOURCE_RUN / "charts").glob("*.svg")):
        target = EXPERIMENT_DIR / "figures" / src.name
        text = _zh_svg(src.read_text(encoding="utf-8"))
        target.write_text(text, encoding="utf-8")
        (EXPERIMENT_DIR / "figures" / f"{src.stem}.en.svg").write_text(_en_svg(text), encoding="utf-8")


def _zh_svg(text: str) -> str:
    replacements = {
        "Throughput First 路由模式：核心指标 A/B 对比": "吞吐优先路由模式：核心指标 A/B 对比",
        "Price First 路由模式：核心指标 A/B 对比": "成本优先路由模式：核心指标 A/B 对比",
        "Latency First 路由模式：核心指标 A/B 对比": "端到端 E2E 时延优先路由模式：核心指标 A/B 对比",
        "TTFT First 路由模式：核心指标 A/B 对比": "流式 TTFT 优先路由模式：核心指标 A/B 对比",
        "Latency / 请求（含 reasoning）": "端到端 E2E 时延 / 请求（含 reasoning）",
        "Response Throughput（含 reasoning）": "响应吞吐量（含 reasoning）",
        "Actual Cost": "实际成本",
        "TTFT / 首包响应": "流式 TTFT / 首包响应",
        "Token Cache Hit Rate": "Token 级缓存命中率",
        "Infron pair": "Infron 配对",
        "OpenRouter pair": "OpenRouter 配对",
        "API Gateway": "API 网关",
        "Telemetry": "遥测",
        "Actual Cost": "实际成本",
        "healthy provider set": "健康 provider 集合",
        "Throughput First 路由模式": "吞吐优先路由模式",
        "Price First 路由模式": "成本优先路由模式",
        "Latency First 路由模式": "端到端 E2E 时延优先路由模式",
        "TTFT First 路由模式": "流式 TTFT 优先路由模式",
        "Throughput First": "吞吐优先",
        "Price First": "成本优先",
        "Latency First": "端到端 E2E 时延优先",
        "TTFT First": "流式 TTFT 优先",
        "Winner": "胜出",
        "Average winner": "均值胜出",
        "Observed cost": "实际成本",
        "Cache hit rate": "缓存命中率",
        "E2E Latency / request": "端到端 E2E 时延 / 请求",
        "Response throughput": "响应吞吐量",
    }
    return _replace_all(text, replacements)


def _en_svg(text: str) -> str:
    replacements = {
        "A/B 配对与控制变量过滤": "A/B Pairing and Controlled-Variable Filter",
        "只保留 first/second prompt tokens 在 A/B 两边完全相等的配对样本。": "Only pairs with exactly equal first/second prompt tokens on both A/B sides are retained.",
        "Infron 配对": "Infron pair",
        "OpenRouter 配对": "OpenRouter pair",
        "进入统计": "Included",
        "否则整对剔除": "otherwise exclude the pair",
        "该过滤防止 tokenization、服务端包装、异常 usage 上报对成本、缓存命中和性能指标造成混杂偏差。": "The filter prevents tokenizer, server wrapping, and anomalous usage reporting from confounding cost, cache, and performance metrics.",
        "实验设计与数据流": "Experimental Design and Data Flow",
        "固定 Payload": "Fixed payload",
        "同一 routing sort 下 payload SHA256 固定，用响应 usage.prompt_tokens 做真实 token 口径。": "Payload SHA-256 is fixed within each routing sort; response usage.prompt_tokens is the token source of truth.",
        "请求 A1/B1": "Request A1/B1",
        "请求 A2/B2": "Request A2/B2",
        "缓存预热": "Cache warm-up",
        "缓存读取观测": "Cache-read observation",
        "严格配对过滤": "Strict pair filter",
        "指标聚合": "Metric aggregation",
        "只聚合 input tokens 完全一致的 A/B pairs。": "Only A/B pairs with identical input tokens are aggregated.",
        "吞吐优先路由模式：核心指标 A/B 对比": "Throughput First Routing Mode: Core Metric A/B Comparison",
        "成本优先路由模式：核心指标 A/B 对比": "Price First Routing Mode: Core Metric A/B Comparison",
        "端到端 E2E 时延优先路由模式：核心指标 A/B 对比": "Latency First Routing Mode: Core Metric A/B Comparison",
        "流式 TTFT 优先路由模式：核心指标 A/B 对比": "TTFT First Routing Mode: Core Metric A/B Comparison",
        "每个面板均比较 Infron 与 OpenRouter；胜出方使用浅色底、粗描边和右上角标签突出展示。": "Each panel compares Infron and OpenRouter; the winner uses a highlight background, bold outline, and corner label.",
        "端到端 E2E 时延 / 请求（含 reasoning）": "E2E Latency / request (incl. reasoning)",
        "响应吞吐量（含 reasoning）": "Response throughput (incl. reasoning)",
        "实际成本": "Observed cost",
        "流式 TTFT / 首包响应": "Streaming TTFT / first byte",
        "Token 级缓存命中率": "Token cache hit rate",
        "胜出": "Winner",
        "均值胜出": "Average winner",
        "核心指标结论总览": "Core Metric Conclusion Overview",
        "跨路由模式胜出方与最大优势": "Cross-mode winners and largest advantage",
        "缓存命中率": "Cache hit rate",
        "吞吐量": "Throughput",
        "端到端E2E时延": "E2E latency",
        "端到端 E2E 时延": "E2E latency",
        "流式TTFT": "Streaming TTFT",
        "流式 TTFT": "Streaming TTFT",
        "路由模式达成情况": "Routing-objective attainment",
        "达成胜出方": "Objective winner",
        "模式": "Mode",
        "吞吐优先": "Throughput First",
        "成本优先": "Price First",
        "时延优先": "Latency First",
        "TTFT优先": "TTFT First",
        "TTFT 优先": "TTFT First",
        "不可能四角：吞吐、价格、端到端 E2E 时延、流式 TTFT": "Impossible quadrilateral: throughput, price, E2E latency, and Streaming TTFT",
        "价格": "Price",
        "相对位置基于归一化指标；越靠近某角表示该维度越强。": "Positions use normalized metrics; proximity to a corner indicates relative strength on that dimension.",
        "综合": "Aggregate",
        "区域": "region",
        "Infron 技术架构：Provider Stick 与 Cache Affinity": "Infron Architecture: Provider Stick and Cache Affinity",
        "请求入口": "Request ingress",
        "认证 / 限流 / 路由参数": "Auth / rate limit / routing params",
        "路由策略层": "Routing policy layer",
        "sort: price / latency / throughput / ttft": "sort: price / latency / throughput / ttft",
        "Provider Stick": "Provider Stick",
        "同 prompt cache domain 优先": "Same prompt cache domain preferred",
        "健康检查": "Health checks",
        "失败时 fallback": "Fallback on failure",
        "上游 Provider 池": "Upstream provider pool",
        "缓存域 A": "Cache domain A",
        "缓存域 B": "Cache domain B",
        "成本与 Usage 归因": "Cost and usage attribution",
        "usage / cost / provider": "usage / cost / provider",
        "核心点：缓存状态通常位于具体 provider/cache domain 内；路由稳定性会直接影响 cache read tokens。": "Key point: cache state usually lives inside a provider/cache domain, so route stability directly affects cache read tokens.",
        "Provider Stick 如何提升 Cache Rate": "How Provider Stick Improves Cache Rate",
        "相同 stable prefix 的连续请求优先落入同一健康缓存域，减少跨 provider 暖缓存。": "Repeated stable prefixes preferentially land in the same healthy cache domain, reducing cross-provider warm-up.",
        "第一次请求": "First request",
        "第二次请求": "Second request",
        "prefix 写入": "prefix write",
        "prefix 读取": "prefix read",
        "Provider stick 不等于禁用 fallback；它是在健康 provider 集合内优先保持缓存亲和。": "Provider stick does not disable fallback; it preserves cache affinity within the healthy provider set.",
        "结果信号：同一 sort 内 provider 分布越集中，第二次请求越容易读取同一缓存域中的 prefix cache。": "Observed signal: a more concentrated provider distribution within one sort makes the second request more likely to read the same prefix cache domain.",
        "Infron 成本控制机制": "Infron Cost-Control Mechanism",
        "成本来自 token 处理、缓存读写和上游 provider 价格；缓存亲和与路由选择共同降低单位请求成本。": "Cost comes from token processing, cache reads/writes, and upstream provider pricing; cache affinity and routing jointly lower unit request cost.",
        "缓存命中": "Cache hit",
        "减少 prefill": "Reduce prefill",
        "成本感知路由": "Cost-aware routing",
        "选择价格路径": "Select price path",
        "解释：高 cache read tokens 降低重复 prefill 成本；provider stick 维持缓存域稳定；成本感知 routing 在健康 provider 中选择更合适的价格路径。": "Explanation: high cache-read tokens reduce repeated prefill cost; provider stick keeps the cache domain stable; cost-aware routing selects a suitable price path among healthy providers.",
        "缓存命中率-实际成本分布": "Cache hit rate vs observed cost distribution",
        "越靠右表示缓存命中率越高；越靠下表示实际成本越低。": "Further right means higher cache hit rate; lower means lower observed cost.",
        "实验数据生成流程": "Experimental Data Generation Flow",
        "同一 payload、同一 routing sort、同一 group/round 下分别请求 Infron 与 OpenRouter。": "The same payload and routing sort are sent to Infron and OpenRouter under the same group/round.",
        "按 sort/group/round 配对": "Pair by sort/group/round",
        "过滤后聚合": "Aggregate after filtering",
        "每轮请求两次相同 prompt：第一次触发/建立缓存，第二次观测 cache read tokens。": "Each round sends the same prompt twice: the first triggers or establishes cache; the second observes cache-read tokens.",
        "综合雷达图": "Aggregate Radar Chart",
        "Aggregate雷达图": "Aggregate Radar Chart",
        "路由Mode": "Routing Mode",
        "指标生成过程对比曲线": "Metric-generation Comparison Curves",
        "所有轴都归一化为“越外圈越好”：成本、时延、TTFT 已做反向评分。": "All axes are normalized so farther outward is better; cost, latency, and TTFT are reverse-scored.",
        "成本效率": "Cost efficiency",
        "平均时延": "Average latency",
        "原始指标值": "Raw metric values",
        "按 group/round 顺序绘制每轮指标；曲线展示汇总均值背后的波动过程。": "Metrics are plotted by group/round sequence; curves show the variation behind aggregate means.",
        "Round 序列；越低越好": "Round sequence; lower is better",
        "Round 序列；越高越好": "Round sequence; higher is better",
        "Observed cost / 轮": "Observed cost / round",
        "结论总览：核心指标与路由ModeWinner方": "Conclusion Overview: Core Metrics and Routing-Mode Winners",
        "基于严格 A/B 配对样本；每个单元格显示同一 routing sort 下表现更好的一方。": "Based on strict A/B paired samples; each cell shows the better platform under the same routing sort.",
        "越高越好": "Higher is better",
        "越低越好": "Lower is better",
        "时延": "Latency",
        "路由Mode": "Routing mode",
        "吞吐达成": "Throughput objective",
        "成本达成": "Cost objective",
        "时延达成": "Latency objective",
        "TTFT 达成": "TTFT objective",
        "目标": "Objective",
        "吞吐目标": "Throughput objective",
        "成本目标": "Cost objective",
        "时延目标": "Latency objective",
        "TTFT 目标": "TTFT objective",
        "读法：前四列与四种路由Mode顺序对齐；金色对角线表示该路由Mode目标指标的Winner方。": "How to read: the first four columns align with the four routing modes; the gold diagonal marks the winner for each routing objective.",
        "缓存和吞吐越高越好，成本、时延和 TTFT 越低越好；Cache hit作为跨Mode辅助指标单独放在最后一列。": "Cache and throughput are better when higher; cost, latency, and TTFT are better when lower; cache hit rate is shown separately as a cross-mode auxiliary metric.",
        "Infron 多 Provider 路由与缓存控制面": "Infron Multi-Provider Routing and Cache Control Plane",
        "OpenAI-compatible API 将请求规范化后，在健康、成本、吞吐、时延和缓存亲和性之间做路由决策。": "The OpenAI-compatible API normalizes requests and routes across health, cost, throughput, latency, and cache affinity.",
        "API 网关": "API Gateway",
        "遥测": "Telemetry",
        "Provider Stick / Cache Affinity 机制": "Provider Stick / Cache Affinity Mechanism",
        "健康 provider 集合": "Healthy provider set",
        "Infron 成本控制路径": "Infron Cost-Control Path",
        "本次实验信号：Infron 的 Token cache hit rate和Observed cost在不同路由Mode下呈现差异化优势。": "Observed signal in this experiment: Infron shows differentiated advantages in token cache hit rate and observed cost across routing modes.",
        "更低Observed cost": "Lower observed cost",
        "高 ": "higher ",
        "低 ": "lower ",
    }
    text = _replace_all(text, replacements)
    post_replacements = {
        "路由Mode": "Routing mode",
        "路由ModeWinner方": "routing-mode winners",
        "路由ModeObjective指标的Winner方": "routing-mode objective winner",
        "Throughput First路由Mode": "Throughput First Routing Mode",
        "Price First路由Mode": "Price First Routing Mode",
        "E2E latency优先路由Mode": "Latency First Routing Mode",
        "Streaming TTFT First路由Mode": "TTFT First Routing Mode",
        "E2E latency优先": "Latency First",
        "Observed cost / 轮": "Observed cost / round",
        "更higher response tok/s": "Higher response tok/s",
        "更低Observed cost": "Lower observed cost",
        "更低完整响应耗时": "Lower full-response latency",
        "更低首包响应时间": "Lower first-token latency",
        "Inference 平台“不可能四角”：四项核心指标的严格归一化对比": "Inference Platform Impossible Quadrilateral: Strictly Normalized Comparison of Four Core Metrics",
        "单图投影展示：每个路由Mode先做四项指标 A/B 归一化，再投影成一个点；同一平台的四个点连接成region。": "Single-chart projection: each routing mode is A/B-normalized across four metrics and projected to one point; points from the same platform form a region.",
        "路由Mode标记": "Routing-mode labels",
        "读图：THR/PRI/LAT/TTFT 分别代表四种路由Mode；蓝色region为 Infron，橙色region为 OpenRouter，region外扩方向表示对应指标优势方向。": "How to read: THR/PRI/LAT/TTFT represent the four routing modes; the blue region is Infron, the orange region is OpenRouter, and outward direction indicates metric advantage.",
        "该图采用统一归一化、四维到二维投影和一致径向视觉放大，用于总览region形状；精确逐指标胜负以下方表格为准。": "The chart uses unified normalization, four-dimensional to two-dimensional projection, and consistent radial visual scaling for region overview; exact metric-level wins and losses are reported in the tables.",
        "该图采用统一归一化、四维到二维投影和一致径向视觉放大，用于总览region形状；精确逐指标wins负以下方表格为准。": "The chart uses unified normalization, four-dimensional to two-dimensional projection, and consistent radial visual scaling for region overview; exact metric-level wins and losses are reported in the tables.",
        "本次实验信号：Infron 的 Token cache hit rate和Observed cost在不同路由Mode下呈现差异化优势。": "Observed signal in this experiment: Infron shows differentiated advantages in token cache hit rate and observed cost across routing modes.",
        "结论总览：核心指标与路由ModeWinner方": "Conclusion Overview: Core Metrics and Routing-Mode Winners",
        "读法：前四列与四种路由Mode顺序对齐；金色对角线表示该路由ModeObjective指标的Winner方。": "How to read: the first four columns align with the four routing modes; the gold diagonal marks the winner for each routing objective.",
        "缓存和吞吐Higher is better，成本、Latency和 TTFT Lower is better；Cache hit作为跨Mode辅助指标单独放在最后一列。": "Cache and throughput are better when higher; cost, latency, and TTFT are better when lower; cache hit rate is shown separately as a cross-mode auxiliary metric.",
        "Cache hit作为跨Mode辅助指标": "cache hit rate as a cross-mode auxiliary metric",
    }
    text = _replace_all(text, post_replacements)
    text = re.sub(r"(\d+)/4 胜", r"\1/4 wins", text)
    text = text.replace("最大优势", "max advantage")
    text = text.replace("胜", "wins")
    return text


def _replace_all(text: str, replacements: dict[str, str]) -> str:
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(old, new)
    return text


def _write_public_runner() -> None:
    source = SOURCE_SCRIPT.read_text(encoding="utf-8")
    old_import = (
        "from insightloop.config.loader import load_settings\n"
        "from insightloop.datasources.model_probe import (\n"
        "    _actual_cost_value,\n"
        "    _cache_read_tokens,\n"
        "    _cache_write_tokens,\n"
        "    _reasoning_tokens,\n"
        "    _usage_value,\n"
        ")\n"
    )
    public_helpers = _extract_public_helpers()
    text = source.replace(old_import, public_helpers)
    text = text.replace('run_id = f"routing_sort_cache_cost_ab_3x40_repeat_{int(time.time())}"', 'run_id = f"routing_sort_cache_cost_ab_4x50_stream_ttft_{int(time.time())}"')
    text = text.replace(
        "def _render_report(summary: dict[str, Any], *, embed_full_reproducibility: bool = True) -> str:",
        "def _render_report(summary: dict[str, Any], *, embed_full_reproducibility: bool = False) -> str:",
    )
    old_summary_text = (
        "本节给出复现结论和图表所需的数据文件。配对级 CSV 是报告中所有总览表、核心指标图和结论快照的直接输入；"
        "请求级 JSONL 保留每一次 first/second 请求的原始 telemetry，便于审计 provider、usage、cost、latency、TTFT 与缓存字段。"
        "为满足单文件审计，报告后文完整" "嵌入本次实验使用的配对级数据、请求级数据、过滤后记录和剔除样本记录。"
    )
    text = text.replace(
        old_summary_text,
        "本节给出复现结论和图表所需的数据文件。配对级 CSV 是报告中所有总览表、核心指标图和结论快照的直接输入；请求级 JSONL 保留每一次 first/second 请求的 telemetry，便于审计 provider、usage、cost、latency、TTFT 与缓存字段。公开报告通过文件路径引用数据集，不在报告正文中展开大体量原始记录。",
    )
    text = text.replace("## 14. 可复现性附录：100% " "原始 Benchmark 数据集", "## 14. 可复现性附录：Benchmark 数据集")
    old_artifact_text = (
        "本节完整" "嵌入本次报告使用的 benchmark 数据文件，不省" "略、不抽样。"
        "`benchmark_pairs.csv` 用于复现聚合指标；`benchmark_requests.jsonl` 用于审计请求级 telemetry；"
        "`records.json` 是严格过滤后的原始结构化记录；`records_excluded.json` 保留被剔除样本，便于复核异常日志和 input token 不一致样本。"
    )
    text = text.replace(
        old_artifact_text,
        "本节引用本次报告使用的 benchmark 数据文件。`benchmark_pairs.csv` 用于复现聚合指标；`benchmark_requests.jsonl` 用于审计请求级 telemetry；`records.json` 是严格过滤后的结构化记录；`records_excluded.json` 保留被剔除样本，便于复核异常日志和 input token 不一致样本。",
    )
    text = text.replace(
        "100% " "原始 benchmark 数据集已嵌入同名 HTML/Markdown 完整版报告。PDF 版只保留数据文件路径、大小、SHA256 与用途，避免数 MB JSONL/JSON 造成 PDF 渲染超时。",
        "Benchmark 数据集保存在实验目录的数据文件中；报告保留数据文件路径、大小、SHA256 与用途，避免大体量 JSONL/JSON 影响网页与 PDF 渲染。",
    )
    (ROOT / "scripts/rerun_routing_sort_cache_cost_ab.py").write_text(text, encoding="utf-8")


def _extract_public_helpers() -> str:
    return PUBLIC_RUNNER_HELPERS.strip() + "\n"


def _copy_code_snapshots() -> None:
    shutil.copy2(ROOT / "scripts/rerun_routing_sort_cache_cost_ab.py", EXPERIMENT_DIR / "code/rerun_routing_sort_cache_cost_ab.py")
    shutil.copy2(ROOT / "scripts/export_routing_report_pdf.py", EXPERIMENT_DIR / "code/export_routing_report_pdf.py")


def _write_data_readme(summary: dict[str, Any]) -> None:
    text = f"""# Dataset

This directory contains the public benchmark datasets for `{EXPERIMENT_ID}`.

## Files

- `benchmark_pairs.csv`: strict A/B pair-level dataset after quality filtering.
- `benchmark_requests.jsonl`: request-level telemetry used for reproducibility.
- `records.json`: raw benchmark records emitted by the runner.
- `records_excluded.json`: records excluded from final aggregation.
- `records_incomplete.json`: incomplete records excluded from final aggregation.
- `records_anomalous_usage.json`: records excluded for anomalous `usage.prompt_tokens`.
- `records_unequal_input_tokens.json`: pairs excluded because A/B `usage.prompt_tokens` did not match exactly.
- `summary.json`: derived aggregate metrics used by the reports.

## Design

- Model: `{summary['model']}`
- Routing modes: `{', '.join(summary['sort_modes'])}`
- Groups: `{summary['groups']}`
- Rounds per group: `{summary['rounds_per_group']}`
- Streaming: `{summary['streaming_enabled']}`
- Included strict A/B pairs: `{_pair_count()}`
- Request-level observations in `benchmark_requests.jsonl`: `{_line_count(EXPERIMENT_DIR / 'data/benchmark_requests.jsonl')}`

The final comparison uses response-returned `usage.prompt_tokens` as the input-token source of truth.
"""
    (EXPERIMENT_DIR / "data/README.md").write_text(text, encoding="utf-8")


def _write_reports(summary: dict[str, Any]) -> None:
    (EXPERIMENT_DIR / "reports" / f"{REPORT_STEM}.zh.md").write_text(_report_zh(summary), encoding="utf-8")
    (EXPERIMENT_DIR / "reports" / f"{REPORT_STEM}.en.md").write_text(_report_en(summary), encoding="utf-8")


def _metrics(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for sort_mode in summary["sort_modes"]:
        aggs = {provider: summary["results"][sort_mode][provider]["aggregate"] for provider in ["infron", "openrouter"]}
        for metric, key, higher, fmt in [
            ("cache", "token_cache_hit_rate", True, "pct"),
            ("cost", "total_actual_cost_usd", False, "cost"),
            ("throughput", "avg_throughput_output_tokens_per_second", True, "tps"),
            ("latency", "avg_request_latency_ms", False, "ms"),
            ("ttft", "avg_ttft_ms", False, "ms"),
        ]:
            winner = _winner(aggs, key, higher)
            rows.append({
                "sort": sort_mode,
                "metric": metric,
                "winner": winner,
                "advantage": _advantage(aggs[winner][key], aggs[_other(winner)][key], higher),
                "infron": aggs["infron"][key],
                "openrouter": aggs["openrouter"][key],
                "fmt": fmt,
            })
    return rows


def _report_zh(summary: dict[str, Any]) -> str:
    pair_count = _pair_count()
    request_rows = _line_count(EXPERIMENT_DIR / "data/benchmark_requests.jsonl")
    excluded = summary["excluded_records"]["total"]
    metric_rows = _metrics(summary)
    links = _links()
    return "\n".join([
        "# deepseek-v4-flash 路由策略、提示词缓存与流式 TTFT A/B 基准报告",
        "",
        "## 摘要与结论大纲",
        "",
        f"本报告评估 `{summary['model']}` 在 Infron 与 OpenRouter 两个平台上的路由策略、提示词缓存、实际成本、吞吐量、端到端 E2E 时延与流式 TTFT。实验采用 4 个实验组、每组 50 轮、流式请求；每轮对两个平台分别发送两次相同请求，并只保留 `usage.prompt_tokens` 完全一致的严格 A/B 配对样本。",
        "",
        f"最终分析保留 {pair_count} 个严格 A/B 配对样本、{request_rows} 条请求级观测记录；数据质量规则剔除 {excluded} 条记录。全部核心指标均来自响应返回的 telemetry，包括 `usage.prompt_tokens`、缓存 token、成本字段、端到端 E2E 时延、流式 TTFT 和 provider 字段。",
        "",
        "![不可能四角](../figures/inference_impossible_quadrilateral.svg)",
        "",
        "图 0：推理平台不可能四角。图中对比吞吐量、价格、端到端 E2E 时延、流式 TTFT 四个方向，展示各路由模式在多目标权衡中的相对位置。",
        "",
        "![结论总览](../figures/conclusion_overview.svg)",
        "",
        "图 A：结论总览。矩阵按路由模式展示缓存命中率、实际成本、吞吐量、端到端 E2E 时延和流式 TTFT 的胜出方。",
        "",
        "### 路由模式级结论",
        "",
        _mode_conclusion_table_zh(summary),
        "",
        "### 核心指标胜出统计",
        "",
        _metric_win_table_zh(metric_rows),
        "",
        "## 1. 研究背景",
        "",
        "LLM 推理平台的真实性能不只由模型本身决定，还受到 provider 路由、提示词缓存、流式响应、成本归因和 fallback 策略影响。对于长上下文、RAG、Agent 工具说明和稳定系统提示词场景，缓存命中率会直接影响单位请求成本；而实时业务还需要同时关注端到端 E2E 时延、流式 TTFT 和吞吐量。",
        "",
        "本实验把推理平台视为可观测系统进行 A/B 测量。报告重点不是单一指标排名，而是回答在严格控制输入 token 和请求 payload 后，两个平台在不同路由目标下形成了怎样的速度、成本、缓存与首包体验取舍。",
        "",
        "## 2. 实验设计、数据集构造与控制变量",
        "",
        "实验使用内置业务代表性 prompt 模板，覆盖稳定长前缀、RAG 支持、Agent 工具说明、营销自动化和代码审查等常见生产形态。每一轮包含 first request 与 second request：第一次请求建立或刷新缓存状态，第二次请求观测缓存读取。",
        "",
        "![实验流程](../figures/experiment_flow.svg)",
        "",
        "图 1：实验流程。相同 payload 在同一路由模式下发送给 Infron 与 OpenRouter，最终只在严格配对样本上聚合指标。",
        "",
        "![A/B 配对过滤](../figures/ab_pairing.svg)",
        "",
        "图 2：A/B 配对过滤。HTTP 异常、未完成记录、`usage.prompt_tokens <= 0` 以及 A/B 输入 token 不一致样本均不进入最终统计。",
        "",
        "核心请求结构如下：",
        "",
        "```json",
        _payload_example_zh(),
        "```",
        "",
        "控制变量方法：同一 `sort/group/round` 下，两个平台必须 first/second 两次请求的 `usage.prompt_tokens` 完全一致。总 Input Tokens 使用响应返回的 `usage.prompt_tokens`，不使用本地 tokenizer 估算。",
        "",
        "## 3. 实验环境与数据质量",
        "",
        _environment_table_zh(summary),
        "",
        "## 4. 指标定义",
        "",
        _metric_definition_table_zh(),
        "",
        "## 5. 核心指标总览",
        "",
        _overview_table_zh(summary),
        "",
        "## 6. 路由模式下钻",
        "",
        _mode_sections_zh(summary),
        "",
        "## 7. 核心指标趋势图",
        "",
        "以下图表按路由模式组织，每张图展示端到端 E2E 时延、吞吐量、实际成本、缓存命中率和流式 TTFT 的 A/B 对比，并保留每轮观测曲线。",
        "",
        _trend_images_zh(),
        "",
        "## 8. Provider 路由下钻",
        "",
        _provider_distribution_zh(summary),
        "",
        "## 9. Infron 技术机制说明",
        "",
        "![Infron 技术架构](../figures/infron_architecture.svg)",
        "",
        "图 12：Infron 技术架构。Provider Stick 与 Cache Affinity 使重复长前缀更容易落入同一健康缓存域。",
        "",
        "![Provider Stick 与缓存亲和](../figures/provider_stick_cache_affinity.svg)",
        "",
        "图 13：Provider Stick 与缓存亲和。该机制不等于禁用 fallback，而是在健康 provider 集合内优先保持缓存域稳定。",
        "",
        "![成本控制机制](../figures/infron_cost_control.svg)",
        "",
        "图 14：成本控制机制。实际成本由 token 处理、缓存读写和上游 provider 价格共同决定。",
        "",
        "## 10. 业务价值讨论",
        "",
        "缓存命中率更适合长上下文、重复系统提示词、RAG 前缀和批处理任务；端到端 E2E 时延和流式 TTFT 更适合实时交互体验；吞吐量更适合长输出和批量生成；实际成本更适合预算敏感型工作负载。不同路由模式对应不同业务目标，平台选择应基于业务 KPI 而不是单一平均值。",
        "",
        "## 11. 局限性与后续工作",
        "",
        "本轮实验使用内置代表性业务模板，不代表所有真实业务语料。后续可以继续补充显著性检验、更长时间窗口、并发压力、更多模型、更多 provider 对，以及更细粒度的上游 routing trace 和成本 breakdown。",
        "",
        "## 12. 可复现性附录",
        "",
        _repro_links_zh(links),
    ])


def _report_en(summary: dict[str, Any]) -> str:
    pair_count = _pair_count()
    request_rows = _line_count(EXPERIMENT_DIR / "data/benchmark_requests.jsonl")
    excluded = summary["excluded_records"]["total"]
    metric_rows = _metrics(summary)
    links = _links()
    return "\n".join([
        "# deepseek-v4-flash Routing, Prompt Caching, and Streaming TTFT A/B Benchmark Report",
        "",
        "## Abstract and Executive Outline",
        "",
        f"This report evaluates `{summary['model']}` on Infron and OpenRouter across provider routing, prompt caching, observed cost, throughput, E2E latency, and Streaming TTFT. The experiment uses 4 groups, 50 rounds per group, and streaming requests. Each round sends two identical requests to each platform, then retains only strict A/B pairs with exactly equal `usage.prompt_tokens`.",
        "",
        f"The final analysis keeps {pair_count} strict A/B pairs and {request_rows} request-level observations. Data-quality rules exclude {excluded} records. All core metrics are derived from response-returned telemetry: `usage.prompt_tokens`, cache tokens, cost fields, E2E latency, Streaming TTFT, and provider fields.",
        "",
        "![Impossible quadrilateral](../figures/inference_impossible_quadrilateral.en.svg)",
        "",
        "Figure 0: The inference-platform impossible quadrilateral. The chart compares throughput, price, E2E latency, and Streaming TTFT, showing how routing modes move across multi-objective trade-offs.",
        "",
        "![Conclusion overview](../figures/conclusion_overview.en.svg)",
        "",
        "Figure A: Conclusion overview. The matrix shows winners for cache hit rate, observed cost, throughput, E2E latency, and Streaming TTFT under each routing mode.",
        "",
        "### Routing-Mode Conclusions",
        "",
        _mode_conclusion_table_en(summary),
        "",
        "### Core Metric Winner Summary",
        "",
        _metric_win_table_en(metric_rows),
        "",
        "## 1. Research Background",
        "",
        "LLM inference-platform behavior is shaped not only by the model, but also by provider routing, prompt caching, streaming response handling, cost attribution, and fallback policy. For long-context, RAG, agent-tool, and stable system-prompt workloads, cache hit rate directly affects unit economics. Interactive products must also control E2E latency, Streaming TTFT, and throughput.",
        "",
        "This study treats the inference platform as an observable system. The goal is not a single leaderboard score, but a controlled comparison of speed, cost, cache reuse, and first-token experience under different routing objectives.",
        "",
        "## 2. Experimental Design, Dataset, and Controls",
        "",
        "The experiment uses built-in representative business prompt templates covering stable long prefixes, RAG support, agent tool instructions, marketing automation, and code review. Each round contains a first request and a second request: the first establishes or refreshes cache state; the second observes cache reuse.",
        "",
        "![Experiment flow](../figures/experiment_flow.en.svg)",
        "",
        "Figure 1: Experimental flow. The same payload is sent to Infron and OpenRouter under each routing mode, and final aggregation uses only strict paired samples.",
        "",
        "![A/B pairing filter](../figures/ab_pairing.en.svg)",
        "",
        "Figure 2: A/B pairing filter. HTTP failures, incomplete records, `usage.prompt_tokens <= 0`, and unequal input-token pairs are excluded.",
        "",
        "Core request shape:",
        "",
        "```json",
        _payload_example_en(),
        "```",
        "",
        "Controlled-variable rule: within the same `sort/group/round`, both platforms must have exactly equal `usage.prompt_tokens` for the first and second requests. Total Input Tokens are computed from response-returned `usage.prompt_tokens`, not from local tokenizer estimates.",
        "",
        "## 3. Experimental Environment and Data Quality",
        "",
        _environment_table_en(summary),
        "",
        "## 4. Metric Definitions",
        "",
        _metric_definition_table_en(),
        "",
        "## 5. Core Metric Overview",
        "",
        _overview_table_en(summary),
        "",
        "## 6. Routing-Mode Drill-Down",
        "",
        _mode_sections_en(summary),
        "",
        "## 7. Core Metric Trend Charts",
        "",
        "The charts are grouped by routing mode. Each chart compares E2E latency, throughput, observed cost, cache hit rate, and Streaming TTFT, with per-round curves where available.",
        "",
        _trend_images_en(),
        "",
        "## 8. Provider Routing Drill-Down",
        "",
        _provider_distribution_en(summary),
        "",
        "## 9. Infron Technical Mechanism",
        "",
        "![Infron architecture](../figures/infron_architecture.en.svg)",
        "",
        "Figure 12: Infron architecture. Provider Stick and Cache Affinity make repeated long prefixes more likely to land in the same healthy cache domain.",
        "",
        "![Provider Stick and cache affinity](../figures/provider_stick_cache_affinity.en.svg)",
        "",
        "Figure 13: Provider Stick and cache affinity. This mechanism does not disable fallback; it preserves cache-domain stability within the healthy provider set.",
        "",
        "![Cost-control mechanism](../figures/infron_cost_control.en.svg)",
        "",
        "Figure 14: Cost-control mechanism. Observed cost is jointly determined by token processing, cache reads/writes, and upstream provider price.",
        "",
        "## 10. Business Implications",
        "",
        "Cache hit rate is most relevant to long-context, repeated system-prompt, RAG-prefix, and batch workloads. E2E latency and Streaming TTFT are most relevant to interactive products. Throughput matters for long-output and batch generation. Observed cost matters for budget-sensitive workloads. Routing mode should therefore follow the business KPI rather than a single average metric.",
        "",
        "## 11. Limitations and Future Work",
        "",
        "This run uses representative built-in business templates and does not cover every production corpus. Future work can add significance tests, longer time windows, concurrency stress tests, more models, more provider pairs, and finer upstream routing-trace and cost-breakdown evidence.",
        "",
        "## 12. Reproducibility Appendix",
        "",
        _repro_links_en(links),
    ])


def _mode_conclusion_table_zh(summary: dict[str, Any]) -> str:
    lines = ["| 路由模式 | 达成目标胜出方 | 缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT |", "| --- | --- | --- | --- | --- | --- | --- |"]
    target_metric = {"throughput": ("avg_throughput_output_tokens_per_second", True), "price": ("total_actual_cost_usd", False), "latency": ("avg_request_latency_ms", False), "ttft": ("avg_ttft_ms", False)}
    for sort in summary["sort_modes"]:
        aggs = _aggs(summary, sort)
        target = _winner(aggs, *target_metric[sort])
        lines.append(f"| {SORT_LABEL_ZH[sort]} | **{_provider(target)}** | {_winner_cell(aggs, 'token_cache_hit_rate', True)} | {_winner_cell(aggs, 'total_actual_cost_usd', False)} | {_winner_cell(aggs, 'avg_throughput_output_tokens_per_second', True)} | {_winner_cell(aggs, 'avg_request_latency_ms', False)} | {_winner_cell(aggs, 'avg_ttft_ms', False)} |")
    return "\n".join(lines)


def _mode_conclusion_table_en(summary: dict[str, Any]) -> str:
    lines = ["| Routing mode | Objective winner | Cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT |", "| --- | --- | --- | --- | --- | --- | --- |"]
    target_metric = {"throughput": ("avg_throughput_output_tokens_per_second", True), "price": ("total_actual_cost_usd", False), "latency": ("avg_request_latency_ms", False), "ttft": ("avg_ttft_ms", False)}
    for sort in summary["sort_modes"]:
        aggs = _aggs(summary, sort)
        target = _winner(aggs, *target_metric[sort])
        lines.append(f"| {SORT_LABEL_EN[sort]} | **{_provider(target)}** | {_winner_cell(aggs, 'token_cache_hit_rate', True)} | {_winner_cell(aggs, 'total_actual_cost_usd', False)} | {_winner_cell(aggs, 'avg_throughput_output_tokens_per_second', True)} | {_winner_cell(aggs, 'avg_request_latency_ms', False)} | {_winner_cell(aggs, 'avg_ttft_ms', False)} |")
    return "\n".join(lines)


def _metric_win_table_zh(rows: list[dict[str, Any]]) -> str:
    labels = {"cache": "缓存命中率", "cost": "实际成本", "throughput": "吞吐量", "latency": "端到端 E2E 时延", "ttft": "流式 TTFT"}
    lines = ["| 指标 | Infron 胜出模式 | OpenRouter 胜出模式 | 最大优势 |", "| --- | --- | --- | --- |"]
    for metric in labels:
        items = [row for row in rows if row["metric"] == metric]
        infron = [SORT_LABEL_ZH[row["sort"]] for row in items if row["winner"] == "infron"]
        openrouter = [SORT_LABEL_ZH[row["sort"]] for row in items if row["winner"] == "openrouter"]
        best = max(items, key=lambda row: row["advantage"])
        lines.append(f"| {labels[metric]} | {', '.join(infron) or '-'} | {', '.join(openrouter) or '-'} | {_provider(best['winner'])} {_pct(best['advantage'])} |")
    return "\n".join(lines)


def _metric_win_table_en(rows: list[dict[str, Any]]) -> str:
    labels = {"cache": "Cache hit rate", "cost": "Observed cost", "throughput": "Throughput", "latency": "E2E latency", "ttft": "Streaming TTFT"}
    lines = ["| Metric | Infron-winning modes | OpenRouter-winning modes | Largest advantage |", "| --- | --- | --- | --- |"]
    for metric in labels:
        items = [row for row in rows if row["metric"] == metric]
        infron = [SORT_LABEL_EN[row["sort"]] for row in items if row["winner"] == "infron"]
        openrouter = [SORT_LABEL_EN[row["sort"]] for row in items if row["winner"] == "openrouter"]
        best = max(items, key=lambda row: row["advantage"])
        lines.append(f"| {labels[metric]} | {', '.join(infron) or '-'} | {', '.join(openrouter) or '-'} | {_provider(best['winner'])} {_pct(best['advantage'])} |")
    return "\n".join(lines)


def _environment_table_zh(summary: dict[str, Any]) -> str:
    mapping = summary["provider_sort_mapping"]
    return "\n".join([
        "| 项目 | 配置 |",
        "| --- | --- |",
        f"| 模型 | `{summary['model']}` |",
        "| 平台 | Infron、OpenRouter |",
        f"| 路由模式 | {', '.join(SORT_LABEL_ZH[item] for item in summary['sort_modes'])} |",
        f"| 路由参数映射 | Infron: `{', '.join(mapping[s]['infron'] for s in summary['sort_modes'])}`；OpenRouter: `{', '.join(mapping[s]['openrouter'] for s in summary['sort_modes'])}` |",
        f"| 实验组 | {summary['groups']} |",
        f"| 每组轮数 | {summary['rounds_per_group']} |",
        f"| Workers | {summary['execution_profile']['workers']} |",
        "| 请求方式 | 流式 Chat Completions，包含 `stream_options.include_usage` 和 `usage.include` |",
        f"| 本地网络环境 | 两个平台使用相同本地代理：`{summary['network_environment']['proxy_url_redacted']}` |",
        f"| 数据集 | `{summary['dataset']['name']}`，{summary['dataset']['description']} |",
    ])


def _environment_table_en(summary: dict[str, Any]) -> str:
    mapping = summary["provider_sort_mapping"]
    return "\n".join([
        "| Item | Configuration |",
        "| --- | --- |",
        f"| Model | `{summary['model']}` |",
        "| Platforms | Infron and OpenRouter |",
        f"| Routing modes | {', '.join(SORT_LABEL_EN[item] for item in summary['sort_modes'])} |",
        f"| Routing parameter mapping | Infron: `{', '.join(mapping[s]['infron'] for s in summary['sort_modes'])}`; OpenRouter: `{', '.join(mapping[s]['openrouter'] for s in summary['sort_modes'])}` |",
        f"| Groups | {summary['groups']} |",
        f"| Rounds per group | {summary['rounds_per_group']} |",
        f"| Workers | {summary['execution_profile']['workers']} |",
        "| Request mode | Streaming Chat Completions with `stream_options.include_usage` and `usage.include` |",
        f"| Local network environment | Both platforms use the same local proxy: `{summary['network_environment']['proxy_url_redacted']}` |",
        f"| Dataset | `{summary['dataset']['name']}`, {summary['dataset']['description']} |",
    ])


def _metric_definition_table_zh() -> str:
    return "\n".join([
        "| 指标 | 定义 | 方向 |",
        "| --- | --- | --- |",
        "| 总 Input Tokens | 纳入统计请求的响应侧 `usage.prompt_tokens` 合计 | 控制变量 |",
        "| Token 级缓存命中率 | 第二次请求 cache read tokens / 第二次请求 prompt tokens | 越高越好 |",
        "| 实际成本 | 响应返回的 cost 或 cost breakdown 合计 | 越低越好 |",
        "| 吞吐量 | completion tokens / 端到端 E2E 时延秒数；reasoning 已按响应 usage 纳入 | 越高越好 |",
        "| 端到端 E2E 时延 | 请求从发送到完整响应结束的耗时 | 越低越好 |",
        "| 流式 TTFT | 首个流式 chunk/token 到达时间 | 越低越好 |",
    ])


def _metric_definition_table_en() -> str:
    return "\n".join([
        "| Metric | Definition | Direction |",
        "| --- | --- | --- |",
        "| Total Input Tokens | Sum of response-side `usage.prompt_tokens` for included requests | Control variable |",
        "| Token cache hit rate | Second-request cache-read tokens / second-request prompt tokens | Higher is better |",
        "| Observed cost | Sum of response-returned cost or cost breakdown | Lower is better |",
        "| Throughput | Completion tokens / E2E latency seconds; reasoning is included when present in response usage | Higher is better |",
        "| E2E latency | Elapsed time from request send to full response completion | Lower is better |",
        "| Streaming TTFT | Time to first streamed chunk/token | Lower is better |",
    ])


def _overview_table_zh(summary: dict[str, Any]) -> str:
    lines = ["| 路由模式 | 平台 | 严格配对轮数 | 总 Input Tokens | Token 级缓存命中率 | 实际成本 | 吞吐量 | 端到端 E2E 时延 | 流式 TTFT | P95 端到端 E2E 时延 | P99 端到端 E2E 时延 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for sort in summary["sort_modes"]:
        aggs = _aggs(summary, sort)
        for provider in ["infron", "openrouter"]:
            a = aggs[provider]
            lines.append(f"| {SORT_LABEL_ZH[sort]} | {_provider(provider)} | {a['rounds']} | {a['total_input_tokens']} | {_bold_win(provider, aggs, 'token_cache_hit_rate', True, _pct(a['token_cache_hit_rate']))} | {_bold_win(provider, aggs, 'total_actual_cost_usd', False, _cost(a['total_actual_cost_usd']))} | {_bold_win(provider, aggs, 'avg_throughput_output_tokens_per_second', True, _tps(a['avg_throughput_output_tokens_per_second']))} | {_bold_win(provider, aggs, 'avg_request_latency_ms', False, _ms(a['avg_request_latency_ms']))} | {_bold_win(provider, aggs, 'avg_ttft_ms', False, _ms(a['avg_ttft_ms']))} | {_ms(a['p95_request_latency_ms'])} | {_ms(a['p99_request_latency_ms'])} |")
    return "\n".join(lines)


def _overview_table_en(summary: dict[str, Any]) -> str:
    lines = ["| Routing mode | Platform | Strict paired rounds | Total Input Tokens | Token cache hit rate | Observed cost | Throughput | E2E latency | Streaming TTFT | P95 E2E latency | P99 E2E latency |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for sort in summary["sort_modes"]:
        aggs = _aggs(summary, sort)
        for provider in ["infron", "openrouter"]:
            a = aggs[provider]
            lines.append(f"| {SORT_LABEL_EN[sort]} | {_provider(provider)} | {a['rounds']} | {a['total_input_tokens']} | {_bold_win(provider, aggs, 'token_cache_hit_rate', True, _pct(a['token_cache_hit_rate']))} | {_bold_win(provider, aggs, 'total_actual_cost_usd', False, _cost(a['total_actual_cost_usd']))} | {_bold_win(provider, aggs, 'avg_throughput_output_tokens_per_second', True, _tps(a['avg_throughput_output_tokens_per_second']))} | {_bold_win(provider, aggs, 'avg_request_latency_ms', False, _ms(a['avg_request_latency_ms']))} | {_bold_win(provider, aggs, 'avg_ttft_ms', False, _ms(a['avg_ttft_ms']))} | {_ms(a['p95_request_latency_ms'])} | {_ms(a['p99_request_latency_ms'])} |")
    return "\n".join(lines)


def _mode_sections_zh(summary: dict[str, Any]) -> str:
    chunks = []
    for sort in summary["sort_modes"]:
        chunks.extend([f"### {SORT_LABEL_ZH[sort]}", "", f"![{SORT_LABEL_ZH[sort]}](../figures/{sort}_first.svg)" if sort != "ttft" else "![流式 TTFT 优先](../figures/ttft_first.svg)", "", f"![{SORT_LABEL_ZH[sort]} 雷达图](../figures/{sort}_first_radar.svg)" if sort != "ttft" else "![流式 TTFT 优先雷达图](../figures/ttft_first_radar.svg)", ""])
    return "\n".join(chunks)


def _mode_sections_en(summary: dict[str, Any]) -> str:
    chunks = []
    for sort in summary["sort_modes"]:
        chunks.extend([f"### {SORT_LABEL_EN[sort]}", "", f"![{SORT_LABEL_EN[sort]}](../figures/{sort}_first.en.svg)", "", f"![{SORT_LABEL_EN[sort]} radar](../figures/{sort}_first_radar.en.svg)", ""])
    return "\n".join(chunks)


def _trend_images_zh() -> str:
    return "\n".join([
        "![吞吐优先趋势](../figures/throughput_first_curves.svg)",
        "",
        "![成本优先趋势](../figures/price_first_curves.svg)",
        "",
        "![端到端 E2E 时延优先趋势](../figures/latency_first_curves.svg)",
        "",
        "![流式 TTFT 优先趋势](../figures/ttft_first_curves.svg)",
    ])


def _trend_images_en() -> str:
    return "\n".join([
        "![Throughput First trends](../figures/throughput_first_curves.en.svg)",
        "",
        "![Price First trends](../figures/price_first_curves.en.svg)",
        "",
        "![Latency First trends](../figures/latency_first_curves.en.svg)",
        "",
        "![TTFT First trends](../figures/ttft_first_curves.en.svg)",
    ])


def _provider_distribution_zh(summary: dict[str, Any]) -> str:
    lines = ["| 路由模式 | 平台 | 总请求数 | 已归因请求数 | Provider 分布 |", "| --- | --- | ---: | ---: | --- |"]
    dist = summary.get("provider_distribution", {})
    for sort in summary["sort_modes"]:
        for provider in ["infron", "openrouter"]:
            item = dist.get(sort, {}).get(provider, {})
            details = item.get("details") or []
            names = ", ".join(f"`{d.get('provider')}` {d.get('request_count', 0)}" for d in details) or "未返回稳定 provider 标识"
            lines.append(f"| {SORT_LABEL_ZH[sort]} | {_provider(provider)} | {item.get('total_requests', 0)} | {item.get('attributed_requests', 0)} | {names} |")
    return "\n".join(lines)


def _provider_distribution_en(summary: dict[str, Any]) -> str:
    lines = ["| Routing mode | Platform | Total requests | Attributed requests | Provider distribution |", "| --- | --- | ---: | ---: | --- |"]
    dist = summary.get("provider_distribution", {})
    for sort in summary["sort_modes"]:
        for provider in ["infron", "openrouter"]:
            item = dist.get(sort, {}).get(provider, {})
            details = item.get("details") or []
            names = ", ".join(f"`{d.get('provider')}` {d.get('request_count', 0)}" for d in details) or "No stable provider identifier returned"
            lines.append(f"| {SORT_LABEL_EN[sort]} | {_provider(provider)} | {item.get('total_requests', 0)} | {item.get('attributed_requests', 0)} | {names} |")
    return "\n".join(lines)


def _repro_links_zh(links: dict[str, str]) -> str:
    return "\n".join([
        "| 工件 | 路径 |",
        "| --- | --- |",
        f"| 中文 HTML 报告 | [GitHub Pages]({links['zh_html_pages']}) |",
        f"| 英文 HTML 报告 | [GitHub Pages]({links['en_html_pages']}) |",
        f"| 中文 Markdown | [GitHub]({links['zh_md']}) |",
        f"| 英文 Markdown | [GitHub]({links['en_md']}) |",
        f"| 数据目录 | [GitHub]({links['data']}) |",
        f"| 完整配对数据集 | [benchmark_pairs.csv]({links['pairs']}) |",
        f"| 请求级观测数据集 | [benchmark_requests.jsonl]({links['requests']}) |",
        f"| Summary | [summary.json]({links['summary']}) |",
        f"| 实验代码 | [rerun_routing_sort_cache_cost_ab.py]({links['runner']}) |",
        f"| 图表目录 | [figures]({links['figures']}) |",
        f"| Manifest | [manifest.json]({links['manifest']}) |",
    ])


def _repro_links_en(links: dict[str, str]) -> str:
    return "\n".join([
        "| Artifact | Path |",
        "| --- | --- |",
        f"| Chinese HTML report | [GitHub Pages]({links['zh_html_pages']}) |",
        f"| English HTML report | [GitHub Pages]({links['en_html_pages']}) |",
        f"| Chinese Markdown | [GitHub]({links['zh_md']}) |",
        f"| English Markdown | [GitHub]({links['en_md']}) |",
        f"| Data directory | [GitHub]({links['data']}) |",
        f"| Paired dataset | [benchmark_pairs.csv]({links['pairs']}) |",
        f"| Request-level dataset | [benchmark_requests.jsonl]({links['requests']}) |",
        f"| Summary | [summary.json]({links['summary']}) |",
        f"| Experiment code | [rerun_routing_sort_cache_cost_ab.py]({links['runner']}) |",
        f"| Figure directory | [figures]({links['figures']}) |",
        f"| Manifest | [manifest.json]({links['manifest']}) |",
    ])


def _write_reports_readme() -> None:
    text = f"""# Reports

- [Chinese Markdown](./{REPORT_STEM}.zh.md)
- [English Markdown](./{REPORT_STEM}.en.md)
- [Chinese HTML]({PAGES_BASE}/experiments/deepseek/deepseek-v4-flash/{EXPERIMENT_ID}/reports/{REPORT_STEM}.zh.html)
- [English HTML]({PAGES_BASE}/experiments/deepseek/deepseek-v4-flash/{EXPERIMENT_ID}/reports/{REPORT_STEM}.en.html)
"""
    (EXPERIMENT_DIR / "reports/README.md").write_text(text, encoding="utf-8")


def _write_experiment_readme(summary: dict[str, Any]) -> None:
    text = f"""# {EXPERIMENT_ID}

Public artifacts for the `{summary['model']}` Infron vs OpenRouter routing, prompt caching, cost, throughput, E2E latency, and Streaming TTFT A/B benchmark.

- Reports: [`reports/`](reports/)
- Data: [`data/`](data/)
- Figures: [`figures/`](figures/)
- Code snapshot: [`code/`](code/)
- Manifest: [`metadata/manifest.json`](metadata/manifest.json)
"""
    (EXPERIMENT_DIR / "README.md").write_text(text, encoding="utf-8")


def _write_manifest(summary: dict[str, Any]) -> None:
    files = []
    for path in sorted(EXPERIMENT_DIR.rglob("*")):
        if path.is_file():
            files.append({"path": path.relative_to(EXPERIMENT_DIR).as_posix(), "size_bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "published_date": "2026-06-27",
        "model": summary["model"],
        "providers": ["Infron", "OpenRouter"],
        "routing_modes": summary["sort_modes"],
        "provider_sort_mapping": summary["provider_sort_mapping"],
        "groups": summary["groups"],
        "rounds_per_group": summary["rounds_per_group"],
        "streaming_enabled": summary["streaming_enabled"],
        "strict_ab_pairs": _pair_count(),
        "request_rows": _line_count(EXPERIMENT_DIR / "data/benchmark_requests.jsonl"),
        "excluded_records": summary["excluded_records"],
        "network_environment": summary["network_environment"],
        "files": files,
    }
    (EXPERIMENT_DIR / "metadata/manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_env_example() -> None:
    path = ROOT / ".env.example"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"PROMPT_CACHE_BENCH_ROUTING_SORTS=.*", "PROMPT_CACHE_BENCH_ROUTING_SORTS=throughput,price,latency,ttft", text)
    text = re.sub(r"PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT=.*", f"PROMPT_CACHE_BENCH_DEFAULT_EXPERIMENT=experiments/deepseek/deepseek-v4-flash/{EXPERIMENT_ID}", text)
    if "AB_TEST_LOCAL_PROXY_URL=" not in text:
        text += "\n# Optional: force both providers through the same local proxy for controlled network conditions.\nAB_TEST_LOCAL_PROXY_URL=\n"
    path.write_text(text, encoding="utf-8")


def _update_validate_default() -> None:
    path = ROOT / "scripts/validate_release.py"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'DEFAULT_EXPERIMENT = \(\n    "experiments/deepseek/deepseek-v4-flash/"\n    "[^"]+"\n\)',
        'DEFAULT_EXPERIMENT = (\n    "experiments/deepseek/deepseek-v4-flash/"\n    "' + EXPERIMENT_ID + '"\n)',
        text,
    )
    path.write_text(text, encoding="utf-8")


def _update_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    old = "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19"
    old_stem = "prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19"
    text = text.replace(old, EXPERIMENT_ID).replace(old_stem, REPORT_STEM)
    text = text.replace("routing sort <code>throughput</code>/<code>price</code>/<code>latency</code>, 4x50 streaming run", "routing sort <code>throughput</code>/<code>price</code>/<code>latency</code>/<code>ttft</code>, 4x50 streaming run")
    text = text.replace("three routing", "four routing")
    text = text.replace("--timeout 120", "--timeout 180")
    if "--local-proxy-url" not in text:
        text = text.replace("  --stream \\\n", "  --stream \\\n  --local-proxy-url \"$AB_TEST_LOCAL_PROXY_URL\" \\\n")
    path.write_text(text, encoding="utf-8")


def _update_index() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    old = "infron-vs-openrouter-routing-sort-cache-cost-4x50-stream-2026-06-19"
    old_stem = "prompt-cache-routing-ab-study__deepseek-v4-flash__infron-vs-openrouter__4x50-stream__2026-06-19"
    text = text.replace(old, EXPERIMENT_ID).replace(old_stem, REPORT_STEM)
    text = text.replace("2026-06-19", "2026-06-27")
    text = text.replace("throughput / price / latency", "throughput / price / latency / ttft")
    text = text.replace("Throughput / Price / Latency", "Throughput / Price / Latency / TTFT")
    text = text.replace("throughput / price / latency / ttft / ttft / ttft / ttft", "throughput / price / latency / ttft")
    text = text.replace("三种路由策略", "四种路由策略")
    text = text.replace("3 routing", "4 routing")
    text = text.replace("48 个文件", "69 个文件")
    text = text.replace("input token 控制、provider 归因、缓存命中分析、实际成本统计、latency/TTFT 测量", "input token 控制、provider 归因、缓存命中分析、实际成本统计、端到端 E2E 时延/流式 TTFT 测量")
    text = text.replace("364 strict A/B pairs", "499 strict A/B pairs")
    text = text.replace("第一份已发布工件", "最新已发布工件")
    text = text.replace("The first published artifact", "The latest published artifact")
    text = text.replace("DeepSeek V4 Flash: Infron vs OpenRouter Routing Sort Cache Cost Study", "DeepSeek V4 Flash: Routing, Prompt Caching, and Streaming TTFT A/B Benchmark")
    text = text.replace("DeepSeek V4 Flash：Infron vs OpenRouter Routing Sort Cache Cost Study", "DeepSeek V4 Flash：路由策略、提示词缓存与流式 TTFT A/B 基准")
    path.write_text(text, encoding="utf-8")


def _payload_example_zh() -> str:
    return json.dumps({
        "model": "deepseek/deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "<稳定长前缀，用于缓存探针>"},
            {"role": "user", "content": "请只回复：cache probe ok"},
        ],
        "temperature": 0,
        "max_tokens": 320,
        "stream": True,
        "stream_options": {"include_usage": True},
        "usage": {"include": True},
        "provider": {"sort": "throughput | price | latency | ttft", "allow_fallbacks": True},
    }, ensure_ascii=False, indent=2)


def _payload_example_en() -> str:
    return json.dumps({
        "model": "deepseek/deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "<stable long prefix for cache probing>"},
            {"role": "user", "content": "Reply with exactly: cache probe ok"},
        ],
        "temperature": 0,
        "max_tokens": 320,
        "stream": True,
        "stream_options": {"include_usage": True},
        "usage": {"include": True},
        "provider": {"sort": "throughput | price | latency | ttft", "allow_fallbacks": True},
    }, ensure_ascii=False, indent=2)


def _links() -> dict[str, str]:
    base = f"experiments/deepseek/deepseek-v4-flash/{EXPERIMENT_ID}"
    file_base = f"{REPO_URL}/blob/main/{base}"
    tree_base = f"{REPO_URL}/tree/main/{base}"
    pages_base = f"{PAGES_BASE}/{base}"
    return {
        "zh_html_pages": f"{pages_base}/reports/{REPORT_STEM}.zh.html",
        "en_html_pages": f"{pages_base}/reports/{REPORT_STEM}.en.html",
        "zh_md": f"{file_base}/reports/{REPORT_STEM}.zh.md",
        "en_md": f"{file_base}/reports/{REPORT_STEM}.en.md",
        "data": f"{tree_base}/data",
        "pairs": f"{file_base}/data/benchmark_pairs.csv",
        "requests": f"{file_base}/data/benchmark_requests.jsonl",
        "summary": f"{file_base}/data/summary.json",
        "runner": f"{file_base}/code/rerun_routing_sort_cache_cost_ab.py",
        "figures": f"{tree_base}/figures",
        "manifest": f"{file_base}/metadata/manifest.json",
    }


def _aggs(summary: dict[str, Any], sort: str) -> dict[str, dict[str, Any]]:
    return {provider: summary["results"][sort][provider]["aggregate"] for provider in ["infron", "openrouter"]}


def _winner(aggs: dict[str, dict[str, Any]], key: str, higher: bool) -> str:
    left = float(aggs["infron"].get(key) or 0)
    right = float(aggs["openrouter"].get(key) or 0)
    return "infron" if (left >= right if higher else left <= right) else "openrouter"


def _winner_cell(aggs: dict[str, dict[str, Any]], key: str, higher: bool) -> str:
    winner = _winner(aggs, key, higher)
    advantage = _advantage(aggs[winner][key], aggs[_other(winner)][key], higher)
    return f"**{_provider(winner)}**（{_pct(advantage)}）"


def _bold_win(provider: str, aggs: dict[str, dict[str, Any]], key: str, higher: bool, value: str) -> str:
    return f"**{value}**" if _winner(aggs, key, higher) == provider else value


def _advantage(winner_value: float, loser_value: float, higher: bool) -> float:
    winner_value = float(winner_value or 0)
    loser_value = float(loser_value or 0)
    if loser_value == 0:
        return 0.0
    if higher:
        return max(0.0, winner_value / loser_value - 1)
    if winner_value == 0:
        return 0.0
    return max(0.0, loser_value / winner_value - 1)


def _other(provider: str) -> str:
    return "openrouter" if provider == "infron" else "infron"


def _provider(provider: str) -> str:
    return "Infron" if provider == "infron" else "OpenRouter"


def _pct(value: float) -> str:
    return f"{float(value) * 100:.2f}%"


def _cost(value: float) -> str:
    return f"${float(value):.8f}"


def _ms(value: float) -> str:
    return f"{float(value):.2f} ms"


def _tps(value: float) -> str:
    return f"{float(value):.2f} tok/s"


def _pair_count() -> int:
    with (EXPERIMENT_DIR / "data/benchmark_pairs.csv").open(newline="", encoding="utf-8") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
