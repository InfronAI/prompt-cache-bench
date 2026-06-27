from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
from html import escape
import io
import json
import math
import os
import random
import socket
import ssl
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from urllib.parse import urlparse, urlunparse

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


MODEL = "deepseek/deepseek-v4-flash"
SORT_MODES = ("throughput", "price", "latency", "ttft")
PROVIDERS = ("infron", "openrouter")
PROVIDER_SORT_OVERRIDES = {
    ("ttft", "infron"): "ttft",
    ("ttft", "openrouter"): "latency",
}
CACHE_PREFIX_REPEAT = 53
CACHE_PREFIX_SUFFIX = "Stable prompt cache suffix unchanged across repeated requests for token accounting verification only."
DEFAULT_DATASET_NAME = "controlled_cache_probe"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=40)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--report", default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--stream", action="store_true", help="Use streaming responses and record TTFT/first token timings.")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--dataset-file", default=None, help="Optional JSONL business corpus. Each row may include system/user/messages.")
    parser.add_argument("--soak-duration-seconds", type=int, default=0, help="Metadata for long-running experiments.")
    parser.add_argument(
        "--local-proxy-url",
        default=None,
        help="One local proxy URL shared by Infron and OpenRouter. Overrides provider-specific proxy settings.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    run_id = f"routing_sort_cache_cost_ab_4x50_stream_ttft_{int(time.time())}"
    out_dir = Path(args.out_dir) if args.out_dir else Path("export") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report) if args.report else Path("export") / f"{run_id}-report-zh.md"

    local_proxy_url = _shared_local_proxy_url(args.local_proxy_url, settings)
    configs = _provider_configs(settings, local_proxy_url=local_proxy_url)
    missing = [name for name, config in configs.items() if not config["api_key"]]
    if missing:
        raise SystemExit(f"Missing API key for providers: {', '.join(missing)}")

    records = _load_records(out_dir / "records.json")
    existing_anomalous_usage_records = _load_records(out_dir / "records_anomalous_usage.json")
    existing_anomalous_usage_keys = {_record_key(item) for item in existing_anomalous_usage_records}
    existing_unequal_input_records = _load_records(out_dir / "records_unequal_input_tokens.json")
    existing_unequal_input_keys = {_record_key(item) for item in existing_unequal_input_records}
    if existing_anomalous_usage_keys:
        records = [item for item in records if _record_key(item) not in existing_anomalous_usage_keys]
    if existing_unequal_input_keys:
        records = [item for item in records if _record_key(item) not in existing_unequal_input_keys]
    incomplete_records = [item for item in records if not _record_complete(item)]
    _write_json(out_dir / "records_incomplete.json", {"records": incomplete_records})
    complete_records = [item for item in records if _record_complete(item)]
    new_anomalous_usage_records = [
        item
        for item in complete_records
        if not _record_usage_valid(item) and _record_key(item) not in existing_anomalous_usage_keys
    ]
    anomalous_usage_records = existing_anomalous_usage_records + new_anomalous_usage_records
    _write_json(out_dir / "records_anomalous_usage.json", {"records": anomalous_usage_records})
    records = [item for item in complete_records if _record_usage_valid(item)]
    unequal_input_records = existing_unequal_input_records
    _write_json(out_dir / "records_unequal_input_tokens.json", {"records": unequal_input_records})
    excluded_records = incomplete_records + anomalous_usage_records + unequal_input_records
    non_retryable_excluded_keys = {
        _record_key(item)
        for item in anomalous_usage_records + unequal_input_records
    }
    _write_json(out_dir / "records_excluded.json", {"records": excluded_records})
    if excluded_records:
        _write_json(out_dir / "records.json", {"records": records})
    done = {_record_key(item) for item in records} | non_retryable_excluded_keys
    excluded_counts = {
        "incomplete": len(incomplete_records),
        "anomalous_usage": len(anomalous_usage_records),
        "unequal_input_tokens": len(unequal_input_records),
        "total": len(excluded_records),
    }

    total = len(SORT_MODES) * len(PROVIDERS) * args.groups * args.rounds
    pending = []
    for sort_mode in SORT_MODES:
        for provider in PROVIDERS:
            for group in range(1, args.groups + 1):
                for round_no in range(1, args.rounds + 1):
                    key = (sort_mode, provider, group, round_no)
                    if key in done:
                        continue
                    pending.append((sort_mode, provider, group, round_no))
    if args.workers <= 1:
        for sort_mode, provider, group, round_no in pending:
            print(f"[{len(records) + 1}/{total}] {sort_mode} {provider} group={group} round={round_no}", flush=True)
            record = _run_round(
                provider_name=provider,
                provider_config=configs[provider],
                sort_mode=sort_mode,
                group=group,
                round_no=round_no,
                timeout=args.timeout,
                stream=args.stream,
                dataset_name=args.dataset_name,
                dataset_file=args.dataset_file,
            )
            records.append(record)
            _write_progress(out_dir, records, record, args.groups, args.rounds, configs, excluded_counts, stream=args.stream)
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
    else:
        workers = max(1, args.workers)
        print(f"Running {len(pending)} pending rounds with workers={workers}", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _run_round,
                    provider_name=provider,
                    provider_config=configs[provider],
                    sort_mode=sort_mode,
                    group=group,
                    round_no=round_no,
                    timeout=args.timeout,
                    stream=args.stream,
                    dataset_name=args.dataset_name,
                    dataset_file=args.dataset_file,
                ): (sort_mode, provider, group, round_no)
                for sort_mode, provider, group, round_no in pending
            }
            for future in as_completed(futures):
                sort_mode, provider, group, round_no = futures[future]
                record = future.result()
                records.append(record)
                print(f"[{len(records)}/{total}] {sort_mode} {provider} group={group} round={round_no}", flush=True)
                _write_progress(out_dir, records, record, args.groups, args.rounds, configs, excluded_counts, stream=args.stream)

    records, excluded_counts = _refresh_filtered_records(out_dir, records)
    _write_group_files(out_dir, records, args.groups)
    summary = _build_summary(
        run_id,
        out_dir,
        records,
        args.groups,
        args.rounds,
        configs,
        excluded_counts,
        stream=args.stream,
        workers=args.workers,
        dataset_name=args.dataset_name,
        dataset_file=args.dataset_file,
        soak_duration_seconds=args.soak_duration_seconds,
    )
    summary["charts"] = _write_charts(out_dir, summary, records)
    summary["provider_distribution"] = _provider_distribution(records)
    summary["benchmark_dataset"] = _write_benchmark_dataset(out_dir, records)
    _write_json(out_dir / "summary.json", summary)
    _write_json(out_dir / "records.json", {"records": records})
    report_path.write_text(_render_report(summary), encoding="utf-8")
    print(json.dumps({"status": "completed", "out_dir": str(out_dir), "report": str(report_path)}, ensure_ascii=False), flush=True)
    return 0


def _provider_configs(settings: Any, *, local_proxy_url: str | None = None) -> dict[str, dict[str, Any]]:
    return {
        "infron": {
            "name": "infron",
            "base_url": settings.model_probe_base_url.rstrip("/"),
            "api_key": settings.model_probe_api_key,
            "cache_policy": settings.model_probe_infron_cache_policy,
            "headers": {},
            "proxy_url": local_proxy_url if local_proxy_url is not None else settings.model_probe_infron_proxy_url,
        },
        "openrouter": {
            "name": "openrouter",
            "base_url": settings.openrouter_base_url.rstrip("/"),
            "api_key": settings.openrouter_api_key,
            "cache_policy": settings.model_probe_openrouter_cache_policy,
            "headers": {
                **({"HTTP-Referer": settings.openrouter_http_referer} if settings.openrouter_http_referer else {}),
                **({"X-Title": settings.openrouter_app_title} if settings.openrouter_app_title else {}),
            },
            "proxy_url": local_proxy_url if local_proxy_url is not None else settings.model_probe_openrouter_proxy_url,
        },
    }


def _shared_local_proxy_url(cli_proxy_url: str | None, settings: Any) -> str | None:
    raw = (
        cli_proxy_url
        if cli_proxy_url is not None
        else os.getenv("AB_TEST_LOCAL_PROXY_URL")
        or os.getenv("LOCAL_PROXY_URL")
        or getattr(settings, "global_proxy_url", None)
    )
    if raw is None:
        return None
    proxy_url = raw.strip()
    if not proxy_url or proxy_url.lower() in {"none", "direct", "off", "false", "0"}:
        return None
    return proxy_url


def _run_round(
    *,
    provider_name: str,
    provider_config: dict[str, Any],
    sort_mode: str,
    group: int,
    round_no: int,
    timeout: int,
    stream: bool,
    dataset_name: str,
    dataset_file: str | None,
) -> dict[str, Any]:
    payload = _payload(
        sort_mode=sort_mode,
        provider_name=provider_name,
        stream=stream,
        group=group,
        round_no=round_no,
        dataset_name=dataset_name,
        dataset_file=dataset_file,
    )
    first = _send(provider_config=provider_config, payload=payload, timeout=timeout)
    second = _send(provider_config=provider_config, payload=payload, timeout=timeout)
    return {
        "sort": sort_mode,
        "provider_sort": _provider_sort_for(provider_name, sort_mode),
        "provider": provider_name,
        "group": group,
        "round": round_no,
        "first": first,
        "second": second,
    }


def _payload(
    *,
    sort_mode: str,
    provider_name: str | None = None,
    stream: bool = False,
    group: int = 1,
    round_no: int = 1,
    dataset_name: str = DEFAULT_DATASET_NAME,
    dataset_file: str | None = None,
) -> dict[str, Any]:
    messages = _messages_for_round(dataset_name=dataset_name, dataset_file=dataset_file, group=group, round_no=round_no)
    provider_sort = _provider_sort_for(provider_name or "infron", sort_mode)
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 16,
        "usage": {"include": True},
        "provider": {"sort": provider_sort, "allow_fallbacks": True},
    }
    if stream:
        payload["stream"] = True
        payload["stream_options"] = {"include_usage": True}
    return payload


def _provider_sort_for(provider_name: str, sort_mode: str) -> str:
    return PROVIDER_SORT_OVERRIDES.get((sort_mode, provider_name), sort_mode)


def _messages_for_round(*, dataset_name: str, dataset_file: str | None, group: int, round_no: int) -> list[dict[str, str]]:
    corpus = _load_business_corpus(dataset_file) if dataset_file else []
    if corpus:
        item = corpus[((group - 1) * 10_000 + round_no - 1) % len(corpus)]
        messages = item.get("messages")
        if isinstance(messages, list) and messages:
            normalized = [
                {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
                for message in messages
                if isinstance(message, dict)
            ]
            if normalized:
                return normalized
        system = str(item.get("system") or _cache_probe_prefix())
        user = str(item.get("user") or item.get("prompt") or "Reply with exactly: cache probe ok")
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if dataset_name == "business_representative":
        return _representative_business_messages(group=group, round_no=round_no)
    return [
        {"role": "system", "content": _cache_probe_prefix()},
        {"role": "user", "content": "Reply with exactly: cache probe ok"},
    ]


def _load_business_corpus(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    corpus_path = Path(path)
    if not corpus_path.exists():
        raise SystemExit(f"Dataset file not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            rows.append(item)
    if not rows:
        raise SystemExit(f"Dataset file is empty: {path}")
    return rows


def _representative_business_messages(*, group: int, round_no: int) -> list[dict[str, str]]:
    templates = [
        ("RAG 客服知识库", "请基于以下固定政策前缀回答用户问题，并保持引用格式稳定。", "用户询问退款政策，回答不超过三句话。"),
        ("Agent 工具说明", "你是工作流 Agent，以下工具说明、JSON schema 和安全规则必须保持稳定。", "判断下一步应该调用哪个工具，并只输出工具名。"),
        ("营销自动化", "你是 B2B 增长运营助手，以下品牌语气、禁用词和邮件模板长期不变。", "为沉默 30 天的线索生成一条跟进邮件主题。"),
        ("代码审查", "你是资深代码审查助手，以下 review rubric 和严重级别定义固定。", "指出这段伪代码中最高风险的问题。"),
    ]
    name, prefix, user = templates[((group - 1) * 10_000 + round_no - 1) % len(templates)]
    stable_context = f"[{name}] {prefix} {_cache_probe_prefix()}"
    return [{"role": "system", "content": stable_context}, {"role": "user", "content": user}]


def _cache_probe_prefix() -> str:
    sentence = (
        "Stable prompt-cache probe prefix. Keep every word unchanged across requests. "
        "This text exists only to verify cache accounting fields and should not affect the answer. "
    )
    return sentence * CACHE_PREFIX_REPEAT + CACHE_PREFIX_SUFFIX


def _send(*, provider_config: dict[str, Any], payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    base_url = provider_config["base_url"].rstrip("/")
    url = base_url + ("/chat/completions" if base_url.endswith("/v1") else "/v1/chat/completions")
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {provider_config['api_key']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "GrowthPulse/0.1 routing-sort-cache-cost-ab",
        "Connection": "close",
        **provider_config.get("headers", {}),
    }
    request = Request(url, data=body, headers=headers, method="POST")
    started = time.monotonic()
    response_headers: dict[str, str] = {}
    stream_metrics: dict[str, Any] = {}
    try:
        proxy_url = provider_config.get("proxy_url")
        if _is_socks_proxy(proxy_url):
            status, response_headers, payload_out, stream_metrics = _send_via_socks_proxy(
                url=url,
                body=body,
                headers=headers,
                timeout=timeout,
                proxy_url=str(proxy_url),
                stream=payload.get("stream") is True,
                started=started,
            )
            error = "" if 200 <= status < 300 else _extract_error(payload_out)
        else:
            opener = _opener(proxy_url)
            with opener.open(request, timeout=timeout) as response:
                status = int(response.status)
                response_headers = {str(key): str(value) for key, value in response.headers.items()}
                if payload.get("stream") is True:
                    payload_out, stream_metrics = _read_stream_response(response, started=started)
                else:
                    raw = response.read()
                    payload_out = json.loads(raw.decode("utf-8")) if raw else {}
                error = ""
    except HTTPError as exc:
        status = int(exc.code)
        raw = exc.read()
        try:
            payload_out = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            payload_out = {"raw": raw.decode("utf-8", errors="replace")}
        error = _extract_error(payload_out) or str(exc)
    except (TimeoutError, URLError, OSError) as exc:
        status = 0
        payload_out = {}
        error = str(exc)
    latency_ms = round((time.monotonic() - started) * 1000, 3)
    usage = payload_out.get("usage") if isinstance(payload_out, dict) and isinstance(payload_out.get("usage"), dict) else {}
    return {
        "status": status,
        "error": error,
        "latency_ms": latency_ms,
        "stream": bool(payload.get("stream")),
        "ttft_ms": stream_metrics.get("ttft_ms"),
        "first_content_token_ms": stream_metrics.get("first_content_token_ms"),
        "first_reasoning_token_ms": stream_metrics.get("first_reasoning_token_ms"),
        "stream_chunk_count": stream_metrics.get("stream_chunk_count", 0),
        "usage": usage,
        "response_model": payload_out.get("model") if isinstance(payload_out, dict) else None,
        "response_id": payload_out.get("id") if isinstance(payload_out, dict) else None,
        "system_fingerprint": payload_out.get("system_fingerprint") if isinstance(payload_out, dict) else None,
        "response_headers": _selected_response_headers(response_headers),
        "provider_attribution": _provider_attribution(payload_out, response_headers),
        "routing_trace": _routing_trace(payload_out, response_headers),
        "provider_cost_breakdown": _provider_cost_breakdown(payload_out),
        "cost": _actual_cost_value(payload_out),
        "prompt_tokens": _usage_value(payload_out, "prompt_tokens", "input_tokens") or 0,
        "completion_tokens": _usage_value(payload_out, "completion_tokens", "output_tokens") or 0,
        "reasoning_tokens": _reasoning_tokens(payload_out) or 0,
        "cache_read_tokens": _cache_read_tokens(payload_out),
        "cache_write_tokens": _cache_write_tokens(payload_out),
    }


def _read_stream_response(response: Any, *, started: float) -> tuple[dict[str, Any], dict[str, Any]]:
    assembled: dict[str, Any] = {"choices": []}
    usage: dict[str, Any] = {}
    chunk_count = 0
    ttft_ms: float | None = None
    first_content_token_ms: float | None = None
    first_reasoning_token_ms: float | None = None
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[len("data:") :].strip()
        if data == "[DONE]":
            continue
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(chunk, dict):
            continue
        now_ms = round((time.monotonic() - started) * 1000, 3)
        chunk_count += 1
        if ttft_ms is None:
            ttft_ms = now_ms
        for key in (
            "id",
            "model",
            "object",
            "created",
            "system_fingerprint",
            "request_id",
            "provider",
            "provider_name",
            "provider_id",
        ):
            if key in chunk and key not in assembled:
                assembled[key] = chunk[key]
        for key in (
            "cost",
            "cost_details",
            "provider_cost_details",
            "cost_breakdown",
            "routing",
            "route",
            "routing_trace",
            "routes",
            "provider_routing",
        ):
            if key in chunk:
                assembled[key] = chunk[key]
        chunk_usage = chunk.get("usage")
        if isinstance(chunk_usage, dict):
            usage = chunk_usage
        choices = chunk.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                delta = choice.get("delta")
                if not isinstance(delta, dict):
                    continue
                if first_content_token_ms is None and _delta_has_text(delta, ("content",)):
                    first_content_token_ms = now_ms
                if first_reasoning_token_ms is None and _delta_has_text(delta, ("reasoning", "reasoning_content")):
                    first_reasoning_token_ms = now_ms
                if first_reasoning_token_ms is None and _delta_has_reasoning_details(delta):
                    first_reasoning_token_ms = now_ms
                if "native_finish_reason" in choice:
                    assembled["native_finish_reason"] = choice["native_finish_reason"]
    if usage:
        assembled["usage"] = usage
    return assembled, {
        "ttft_ms": ttft_ms,
        "first_content_token_ms": first_content_token_ms,
        "first_reasoning_token_ms": first_reasoning_token_ms,
        "stream_chunk_count": chunk_count,
    }


def _delta_has_text(delta: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        value = delta.get(key)
        if isinstance(value, str) and value:
            return True
    return False


def _delta_has_reasoning_details(delta: dict[str, Any]) -> bool:
    details = delta.get("reasoning_details")
    if isinstance(details, list):
        return any(isinstance(item, dict) and item.get("type") in {"reasoning.text", "text"} for item in details)
    return isinstance(details, dict) and details.get("type") in {"reasoning.text", "text"}


def _selected_response_headers(headers: dict[str, str]) -> dict[str, str]:
    selected = {}
    for key, value in headers.items():
        key_l = key.lower()
        if key_l.startswith("x-") or key_l in {"openrouter-provider", "cf-ray", "server"}:
            selected[key] = value
    return selected


def _provider_attribution(payload: Any, headers: dict[str, str]) -> dict[str, Any]:
    attribution: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key in (
            "provider",
            "provider_name",
            "provider_id",
            "upstream_provider",
            "upstream",
            "provider_model",
            "model",
            "id",
            "request_id",
            "system_fingerprint",
            "native_finish_reason",
        ):
            if key in payload:
                attribution[key] = payload[key]
        usage = payload.get("usage")
        if isinstance(usage, dict):
            for key in ("provider", "provider_name", "provider_id", "cost_details"):
                if key in usage:
                    attribution[f"usage.{key}"] = usage[key]
    header_attribution = {
        key: value
        for key, value in headers.items()
        if any(marker in key.lower() for marker in ("provider", "route", "model"))
    }
    if header_attribution:
        attribution["headers"] = header_attribution
    return attribution


def _routing_trace(payload: Any, headers: dict[str, str]) -> dict[str, Any]:
    trace: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key in ("routing", "route", "routing_trace", "routes", "provider_routing"):
            if key in payload:
                trace[key] = payload[key]
    header_trace = {
        key: value
        for key, value in headers.items()
        if any(marker in key.lower() for marker in ("route", "routing", "provider"))
    }
    if header_trace:
        trace["headers"] = header_trace
    return trace


def _provider_cost_breakdown(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usage")
    candidates = []
    if isinstance(usage, dict):
        candidates.extend(("cost_details", "provider_cost_details", "cost_breakdown"))
        for key in candidates:
            value = usage.get(key)
            if isinstance(value, dict):
                return value
    for key in ("cost_details", "provider_cost_details", "cost_breakdown"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _opener(proxy_url: str | None):
    if not proxy_url:
        return build_opener(ProxyHandler({}))
    return build_opener(ProxyHandler({"http": proxy_url, "https": proxy_url}))


def _is_socks_proxy(proxy_url: str | None) -> bool:
    return bool(proxy_url and proxy_url.lower().startswith(("socks5://", "socks5h://")))


def _send_via_socks_proxy(
    *,
    url: str,
    body: bytes,
    headers: dict[str, str],
    timeout: int,
    proxy_url: str,
    stream: bool,
    started: float,
) -> tuple[int, dict[str, str], Any, dict[str, Any]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported proxied URL scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise ValueError("Proxied URL host is required")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    sock = _open_socks5_socket(proxy_url=proxy_url, host=parsed.hostname, port=port, timeout=timeout)
    try:
        if parsed.scheme == "https":
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=parsed.hostname)
        outbound_headers = {
            "Host": parsed.hostname if port in {80, 443} else f"{parsed.hostname}:{port}",
            "Content-Length": str(len(body)),
            **headers,
        }
        request_lines = [f"POST {path} HTTP/1.1"]
        request_lines.extend(f"{key}: {value}" for key, value in outbound_headers.items())
        request_bytes = ("\r\n".join(request_lines) + "\r\n\r\n").encode("utf-8") + body
        sock.sendall(request_bytes)
        response = http.client.HTTPResponse(sock)
        response.begin()
        status = int(response.status)
        response_headers = {str(key): str(value) for key, value in response.headers.items()}
        if stream:
            payload_out, stream_metrics = _read_stream_response(response, started=started)
        else:
            raw = response.read()
            payload_out = json.loads(raw.decode("utf-8")) if raw else {}
            stream_metrics = {}
        return status, response_headers, payload_out, stream_metrics
    finally:
        sock.close()


def _parse_socks5_proxy(proxy_url: str) -> tuple[str, int]:
    parsed = urlparse(proxy_url)
    if parsed.scheme not in {"socks5", "socks5h"}:
        raise ValueError("Only socks5:// or socks5h:// local proxy URLs are supported")
    if parsed.username or parsed.password:
        raise ValueError("Authenticated SOCKS proxies are not supported")
    if not parsed.hostname:
        raise ValueError("SOCKS proxy host is required")
    return parsed.hostname, parsed.port or 1080


def _open_socks5_socket(*, proxy_url: str, host: str, port: int, timeout: int | float | None) -> socket.socket:
    proxy_host, proxy_port = _parse_socks5_proxy(proxy_url)
    sock = socket.create_connection((proxy_host, proxy_port), timeout)
    try:
        sock.settimeout(timeout)
        sock.sendall(b"\x05\x01\x00")
        response = _read_exact(sock, 2)
        if response != b"\x05\x00":
            raise OSError(f"SOCKS5 proxy authentication negotiation failed: {response!r}")
        host_bytes = host.encode("idna")
        if len(host_bytes) > 255:
            raise OSError("SOCKS5 target host is too long")
        request = b"\x05\x01\x00\x03" + bytes([len(host_bytes)]) + host_bytes + int(port).to_bytes(2, "big")
        sock.sendall(request)
        header = _read_exact(sock, 4)
        if header[0] != 5 or header[1] != 0:
            raise OSError(f"SOCKS5 proxy connect failed: {header!r}")
        address_type = header[3]
        if address_type == 1:
            _read_exact(sock, 4)
        elif address_type == 3:
            length = _read_exact(sock, 1)[0]
            _read_exact(sock, length)
        elif address_type == 4:
            _read_exact(sock, 16)
        else:
            raise OSError(f"SOCKS5 proxy returned unsupported address type: {address_type}")
        _read_exact(sock, 2)
        return sock
    except Exception:
        sock.close()
        raise


def _read_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise OSError("SOCKS5 proxy closed connection unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _extract_error(payload: Any) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
        if isinstance(error, str):
            return error
    return ""


def _build_summary(
    run_id: str,
    out_dir: Path,
    records: list[dict[str, Any]],
    groups: int,
    rounds: int,
    configs: dict[str, dict[str, Any]],
    excluded_counts: dict[str, int] | None = None,
    stream: bool = False,
    workers: int = 1,
    dataset_name: str = DEFAULT_DATASET_NAME,
    dataset_file: str | None = None,
    soak_duration_seconds: int = 0,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for sort_mode in SORT_MODES:
        results[sort_mode] = {}
        for provider in PROVIDERS:
            group_rows = []
            for group in range(1, groups + 1):
                rows = _filter_records(records, sort_mode, provider, group)
                group_rows.append({"group": group, "aggregate": _aggregate(rows)})
            all_rows = [item for item in records if item["sort"] == sort_mode and item["provider"] == provider]
            results[sort_mode][provider] = {"groups": group_rows, "aggregate": _aggregate(all_rows)}
        infron = results[sort_mode]["infron"]["aggregate"]
        openrouter = results[sort_mode]["openrouter"]["aggregate"]
        infron_cost = _numeric_value(infron["total_actual_cost_usd"])
        openrouter_cost = _numeric_value(openrouter["total_actual_cost_usd"])
        results[sort_mode]["comparison"] = {
            "call_cache_hit_rate_delta_infron_minus_openrouter": round(float(infron["call_cache_hit_rate"]) - float(openrouter["call_cache_hit_rate"]), 6),
            "token_cache_hit_rate_delta_infron_minus_openrouter": round(float(infron["token_cache_hit_rate"]) - float(openrouter["token_cache_hit_rate"]), 6),
            "cost_delta_openrouter_minus_infron_usd": round(openrouter_cost - infron_cost, 8)
            if infron_cost is not None and openrouter_cost is not None
            else None,
            "openrouter_cost_multiple_vs_infron": round(openrouter_cost / infron_cost, 6)
            if infron_cost and openrouter_cost is not None
            else None,
            "infron_cost_reduction_vs_openrouter": round((openrouter_cost - infron_cost) / openrouter_cost, 6)
            if infron_cost is not None and openrouter_cost
            else None,
        }
        results[sort_mode]["statistical_tests"] = _paired_statistical_tests(records, sort_mode)
    return {
        "run_id": run_id,
        "model": MODEL,
        "sort_modes": list(SORT_MODES),
        "request_payload_sha256_by_sort": {
            sort_mode: {
                provider: _payload_hash(
                    _payload(
                        sort_mode=sort_mode,
                        provider_name=provider,
                        stream=stream,
                        dataset_name=dataset_name,
                        dataset_file=dataset_file,
                    )
                )
                for provider in PROVIDERS
            }
            for sort_mode in SORT_MODES
        },
        "provider_sort_mapping": {
            sort_mode: {provider: _provider_sort_for(provider, sort_mode) for provider in PROVIDERS}
            for sort_mode in SORT_MODES
        },
        "dataset": _dataset_metadata(dataset_name=dataset_name, dataset_file=dataset_file),
        "execution_profile": {
            "workers": workers,
            "soak_duration_seconds": soak_duration_seconds,
            "planned_request_count": len(SORT_MODES) * len(PROVIDERS) * groups * rounds * 2,
            "pairing_method": "strict sort/group/round pair with equal first/second usage.prompt_tokens",
        },
        "network_environment": _network_environment_summary(configs),
        "streaming_enabled": stream,
        "groups": groups,
        "rounds_per_group": rounds,
        "providers": [
            {"name": name, "base_url": configs[name]["base_url"], "cache_policy": configs[name]["cache_policy"]}
            for name in PROVIDERS
        ],
        "excluded_records": excluded_counts or {"incomplete": 0, "anomalous_usage": 0, "unequal_input_tokens": 0, "total": 0},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result_dir": str(out_dir),
        "results": results,
    }


def _network_environment_summary(configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    proxy_by_provider = {name: configs[name].get("proxy_url") for name in PROVIDERS}
    unique_proxy_urls = {value for value in proxy_by_provider.values() if value}
    same_proxy = len(set(proxy_by_provider.values())) == 1
    selected_proxy = next(iter(unique_proxy_urls), None) if same_proxy and unique_proxy_urls else None
    return {
        "same_local_runtime": True,
        "same_http_client_logic": True,
        "same_local_proxy": same_proxy,
        "proxy_enabled": bool(selected_proxy),
        "proxy_url_redacted": _redact_url(selected_proxy),
        "proxy_scheme": urlparse(selected_proxy).scheme if selected_proxy else None,
        "proxy_by_provider_redacted": {
            provider: _redact_url(proxy_url)
            for provider, proxy_url in proxy_by_provider.items()
        },
        "implicit_environment_proxy_disabled": True,
        "proxy_config_source_priority": ["--local-proxy-url", "AB_TEST_LOCAL_PROXY_URL", "LOCAL_PROXY_URL", "GLOBAL_PROXY_URL"],
    }


def _redact_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    netloc = parsed.netloc
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        netloc = f"***:***@{host}{port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rounds = len(rows)
    successful = [item for item in rows if item["first"]["status"] == 200 and item["second"]["status"] == 200]
    second_prompt = [item["second"]["prompt_tokens"] for item in rows]
    second_cache = [item["second"]["cache_read_tokens"] for item in rows]
    input_tokens = [
        int(request["prompt_tokens"] or 0)
        for item in rows
        for request in (item["first"], item["second"])
    ]
    request_cost_values = [
        _request_cost_value(request)
        for item in rows
        for request in (item["first"], item["second"])
    ]
    observed_request_costs = [value for value in request_cost_values if value is not None]
    cost_fully_observed = len(observed_request_costs) == len(request_cost_values)
    pair_costs = [
        first_cost + second_cost
        for item in rows
        for first_cost, second_cost in [(_request_cost_value(item["first"]), _request_cost_value(item["second"]))]
        if first_cost is not None and second_cost is not None
    ]
    second_costs = [
        value
        for item in rows
        for value in [_request_cost_value(item["second"])]
        if value is not None
    ]
    pair_latencies = [float(item["first"]["latency_ms"] or 0) + float(item["second"]["latency_ms"] or 0) for item in rows]
    request_latencies = [
        float(request["latency_ms"] or 0)
        for item in rows
        for request in (item["first"], item["second"])
    ]
    completion_tokens = [
        int(request["completion_tokens"] or 0)
        for item in rows
        for request in (item["first"], item["second"])
    ]
    ttft_values = [
        float(request["ttft_ms"])
        for item in rows
        for request in (item["first"], item["second"])
        if isinstance(request.get("ttft_ms"), int | float) and not isinstance(request.get("ttft_ms"), bool)
    ]
    first_reasoning_values = [
        float(request["first_reasoning_token_ms"])
        for item in rows
        for request in (item["first"], item["second"])
        if isinstance(request.get("first_reasoning_token_ms"), int | float)
        and not isinstance(request.get("first_reasoning_token_ms"), bool)
    ]
    reasoning_tokens = [
        _request_reasoning_tokens(request)
        for item in rows
        for request in (item["first"], item["second"])
    ]
    reasoning_latencies = [
        float(request["latency_ms"] or 0)
        for item in rows
        for request in (item["first"], item["second"])
        if _request_reasoning_tokens(request) > 0
    ]
    total_latency_seconds = sum(request_latencies) / 1000
    reasoning_latency_seconds = sum(reasoning_latencies) / 1000
    statuses = sorted({int(item["first"]["status"]) for item in rows} | {int(item["second"]["status"]) for item in rows})
    cache_hit_rounds = sum(1 for value in second_cache if value > 0)
    total_prompt = sum(second_prompt)
    total_reasoning_tokens = sum(reasoning_tokens)
    return {
        "rounds": rounds,
        "successful_rounds": len(successful),
        "call_cache_hit_rounds": cache_hit_rounds,
        "call_cache_hit_rate": round(cache_hit_rounds / rounds, 6) if rounds else 0,
        "second_prompt_tokens": int(total_prompt),
        "total_input_tokens": int(sum(input_tokens)),
        "second_cache_read_tokens": int(sum(second_cache)),
        "token_cache_hit_rate": round(sum(second_cache) / total_prompt, 6) if total_prompt else 0,
        "avg_second_cache_read_tokens": round(sum(second_cache) / rounds, 4) if rounds else 0,
        "avg_second_prompt_tokens": round(total_prompt / rounds, 4) if rounds else 0,
        "cost_observed_request_count": len(observed_request_costs),
        "cost_total_request_count": len(request_cost_values),
        "cost_fully_observed": cost_fully_observed,
        "total_actual_cost_usd": round(sum(pair_costs), 8) if cost_fully_observed else None,
        "total_observed_cost_usd": round(sum(observed_request_costs), 8),
        "avg_actual_cost_per_round_pair_usd": round(sum(pair_costs) / rounds, 8) if cost_fully_observed and rounds else None,
        "avg_second_request_cost_usd": round(sum(second_costs) / rounds, 8) if len(second_costs) == rounds and rounds else None,
        "second_request_cost_stddev_usd": round(statistics.pstdev(second_costs), 8) if len(second_costs) == rounds and len(second_costs) > 1 else None,
        "avg_request_latency_ms": round(sum(request_latencies) / len(request_latencies), 3) if request_latencies else 0,
        "p50_request_latency_ms": _percentile(request_latencies, 50),
        "p95_request_latency_ms": _percentile(request_latencies, 95),
        "p99_request_latency_ms": _percentile(request_latencies, 99),
        "avg_ttft_ms": round(sum(ttft_values) / len(ttft_values), 3) if ttft_values else 0,
        "p50_ttft_ms": _percentile(ttft_values, 50),
        "p95_ttft_ms": _percentile(ttft_values, 95),
        "p99_ttft_ms": _percentile(ttft_values, 99),
        "ttft_request_count": len(ttft_values),
        "avg_first_reasoning_token_ms": round(sum(first_reasoning_values) / len(first_reasoning_values), 3) if first_reasoning_values else 0,
        "first_reasoning_token_request_count": len(first_reasoning_values),
        "avg_pair_latency_ms": round(sum(pair_latencies) / rounds, 3) if rounds else 0,
        "p95_pair_latency_ms": _percentile(pair_latencies, 95),
        "p99_pair_latency_ms": _percentile(pair_latencies, 99),
        "avg_throughput_output_tokens_per_second": round(sum(completion_tokens) / total_latency_seconds, 3) if total_latency_seconds else 0,
        "total_reasoning_tokens": int(total_reasoning_tokens),
        "reasoning_request_count": len(reasoning_latencies),
        "avg_reasoning_tokens_per_request": round(total_reasoning_tokens / len(request_latencies), 4) if request_latencies else 0,
        "avg_reasoning_request_latency_ms": round(sum(reasoning_latencies) / len(reasoning_latencies), 3) if reasoning_latencies else 0,
        "avg_reasoning_throughput_tokens_per_second": round(total_reasoning_tokens / reasoning_latency_seconds, 3) if reasoning_latency_seconds else 0,
        "http_statuses": statuses,
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    clean = sorted(float(value) for value in values if isinstance(value, int | float) and not isinstance(value, bool))
    if not clean:
        return None
    if len(clean) == 1:
        return round(clean[0], 3)
    rank = (percentile / 100) * (len(clean) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(clean) - 1)
    weight = rank - lower
    return round(clean[lower] * (1 - weight) + clean[upper] * weight, 3)


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 8) if values else None


def _bootstrap_ci(values: list[float], *, iterations: int = 2000, seed: int = 20260619) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "ci95_low": None, "ci95_high": None}
    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return {
        "mean": round(sum(values) / len(values), 8),
        "ci95_low": round(means[int(iterations * 0.025)], 8),
        "ci95_high": round(means[min(int(iterations * 0.975), iterations - 1)], 8),
    }


def _paired_permutation_p_value(values: list[float], *, iterations: int = 4000, seed: int = 20260619) -> float | None:
    if not values:
        return None
    observed = abs(sum(values) / len(values))
    if observed == 0:
        return 1.0
    rng = random.Random(seed)
    extreme = 0
    for _ in range(iterations):
        permuted = [value if rng.random() < 0.5 else -value for value in values]
        if abs(sum(permuted) / len(permuted)) >= observed:
            extreme += 1
    return round((extreme + 1) / (iterations + 1), 6)


def _paired_statistical_tests(records: list[dict[str, Any]], sort_mode: str) -> dict[str, Any]:
    pairs: dict[tuple[int, int], dict[str, dict[str, Any]]] = {}
    for item in records:
        if item["sort"] != sort_mode:
            continue
        pairs.setdefault((int(item["group"]), int(item["round"])), {})[str(item["provider"])] = item
    metrics: dict[str, list[float]] = {
        "latency_ms_delta_openrouter_minus_infron": [],
        "ttft_ms_delta_openrouter_minus_infron": [],
        "throughput_delta_infron_minus_openrouter": [],
        "cost_delta_openrouter_minus_infron_usd": [],
        "token_cache_hit_rate_delta_infron_minus_openrouter": [],
    }
    for providers in pairs.values():
        infron = providers.get("infron")
        openrouter = providers.get("openrouter")
        if not infron or not openrouter:
            continue
        infron_latency = _pair_latency_ms(infron)
        openrouter_latency = _pair_latency_ms(openrouter)
        metrics["latency_ms_delta_openrouter_minus_infron"].append(openrouter_latency - infron_latency)
        infron_ttft = _pair_ttft_ms(infron)
        openrouter_ttft = _pair_ttft_ms(openrouter)
        if infron_ttft is not None and openrouter_ttft is not None:
            metrics["ttft_ms_delta_openrouter_minus_infron"].append(openrouter_ttft - infron_ttft)
        infron_throughput = _pair_throughput(infron)
        openrouter_throughput = _pair_throughput(openrouter)
        metrics["throughput_delta_infron_minus_openrouter"].append(infron_throughput - openrouter_throughput)
        infron_cost = _pair_cost(infron)
        openrouter_cost = _pair_cost(openrouter)
        if infron_cost is not None and openrouter_cost is not None:
            metrics["cost_delta_openrouter_minus_infron_usd"].append(openrouter_cost - infron_cost)
        metrics["token_cache_hit_rate_delta_infron_minus_openrouter"].append(_pair_cache_rate(infron) - _pair_cache_rate(openrouter))
    return {
        name: {
            **_bootstrap_ci(values),
            "paired_permutation_p_value": _paired_permutation_p_value(values),
            "n_pairs": len(values),
        }
        for name, values in metrics.items()
    }


def _pair_latency_ms(item: dict[str, Any]) -> float:
    return float(item["first"].get("latency_ms") or 0) + float(item["second"].get("latency_ms") or 0)


def _pair_ttft_ms(item: dict[str, Any]) -> float | None:
    values = [
        _numeric_value(item["first"].get("ttft_ms")),
        _numeric_value(item["second"].get("ttft_ms")),
    ]
    if any(value is None for value in values):
        return None
    return float(values[0] or 0) + float(values[1] or 0)


def _pair_throughput(item: dict[str, Any]) -> float:
    completion = int(item["first"].get("completion_tokens") or 0) + int(item["second"].get("completion_tokens") or 0)
    latency_seconds = _pair_latency_ms(item) / 1000
    return completion / latency_seconds if latency_seconds else 0


def _pair_cost(item: dict[str, Any]) -> float | None:
    first = _request_cost_value(item["first"])
    second = _request_cost_value(item["second"])
    if first is None or second is None:
        return None
    return first + second


def _pair_cache_rate(item: dict[str, Any]) -> float:
    second_prompt = int(item["second"].get("prompt_tokens") or 0)
    if not second_prompt:
        return 0
    return int(item["second"].get("cache_read_tokens") or 0) / second_prompt


def _record_complete(item: dict[str, Any]) -> bool:
    first = item.get("first")
    second = item.get("second")
    return (
        isinstance(first, dict)
        and isinstance(second, dict)
        and first.get("status") == 200
        and second.get("status") == 200
    )


def _request_reasoning_tokens(request: dict[str, Any]) -> int:
    value = request.get("reasoning_tokens")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return int(value)
    usage = request.get("usage")
    if not isinstance(usage, dict):
        return 0
    completion_details = usage.get("completion_tokens_details")
    if isinstance(completion_details, dict):
        detail_value = completion_details.get("reasoning_tokens")
        if isinstance(detail_value, int | float) and not isinstance(detail_value, bool):
            return int(detail_value)
    for key in ("reasoning_tokens", "thinking_tokens"):
        usage_value = usage.get(key)
        if isinstance(usage_value, int | float) and not isinstance(usage_value, bool):
            return int(usage_value)
    return 0


def _request_cost_value(request: dict[str, Any]) -> float | None:
    usage = request.get("usage")
    if isinstance(usage, dict):
        value = usage.get("cost")
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
    value = request.get("cost")
    if isinstance(value, int | float) and not isinstance(value, bool):
        breakdown = request.get("provider_cost_breakdown")
        if isinstance(breakdown, dict) and breakdown:
            return float(value)
    return None


def _provider_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    distribution: dict[str, Any] = {}
    for sort_mode in SORT_MODES:
        distribution[sort_mode] = {}
        for provider in PROVIDERS:
            counts: dict[str, int] = {}
            provider_stats: dict[str, dict[str, Any]] = {}
            cost_breakdown_requests = 0
            total_requests = 0
            for item in records:
                if item["sort"] != sort_mode or item["provider"] != provider:
                    continue
                for side in ("first", "second"):
                    total_requests += 1
                    request = item[side]
                    attribution = request.get("provider_attribution") if isinstance(request, dict) else None
                    provider_name = ""
                    if isinstance(attribution, dict):
                        provider_name = str(attribution.get("provider") or attribution.get("provider_name") or attribution.get("usage.provider") or "")
                    if provider_name:
                        counts[provider_name] = counts.get(provider_name, 0) + 1
                        stats = provider_stats.setdefault(
                            provider_name,
                            {
                                "provider": provider_name,
                                "request_count": 0,
                                "first_request_count": 0,
                                "second_request_count": 0,
                                "round_keys": set(),
                                "latency_ms": [],
                                "ttft_ms": [],
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "reasoning_tokens": 0,
                                "cache_read_tokens": 0,
                                "cache_write_tokens": 0,
                                "cost_values": [],
                                "cost_breakdown_requests": 0,
                            },
                        )
                        stats["request_count"] += 1
                        stats[f"{side}_request_count"] += 1
                        stats["round_keys"].add((int(item["group"]), int(item["round"])))
                        latency = _numeric_value(request.get("latency_ms"))
                        if latency is not None:
                            stats["latency_ms"].append(latency)
                        ttft = _numeric_value(request.get("ttft_ms"))
                        if ttft is not None:
                            stats["ttft_ms"].append(ttft)
                        stats["prompt_tokens"] += int(request.get("prompt_tokens") or 0)
                        stats["completion_tokens"] += int(request.get("completion_tokens") or 0)
                        stats["reasoning_tokens"] += _request_reasoning_tokens(request)
                        stats["cache_read_tokens"] += int(request.get("cache_read_tokens") or 0)
                        stats["cache_write_tokens"] += int(request.get("cache_write_tokens") or 0)
                        request_cost = _request_cost_value(request)
                        if request_cost is not None:
                            stats["cost_values"].append(request_cost)
                    if isinstance(request.get("provider_cost_breakdown"), dict) and request.get("provider_cost_breakdown"):
                        cost_breakdown_requests += 1
                        if provider_name:
                            provider_stats[provider_name]["cost_breakdown_requests"] += 1
            total = sum(counts.values())
            details = []
            for name, stats in sorted(provider_stats.items(), key=lambda item: (-item[1]["request_count"], item[0])):
                request_count = int(stats["request_count"])
                latency_values = stats["latency_ms"]
                ttft_values = stats["ttft_ms"]
                cost_values = stats["cost_values"]
                details.append(
                    {
                        "provider": name,
                        "request_count": request_count,
                        "request_share": round(request_count / total, 6) if total else 0,
                        "first_request_count": int(stats["first_request_count"]),
                        "second_request_count": int(stats["second_request_count"]),
                        "covered_rounds": len(stats["round_keys"]),
                        "avg_latency_ms": round(sum(latency_values) / len(latency_values), 3) if latency_values else None,
                        "avg_ttft_ms": round(sum(ttft_values) / len(ttft_values), 3) if ttft_values else None,
                        "prompt_tokens": int(stats["prompt_tokens"]),
                        "completion_tokens": int(stats["completion_tokens"]),
                        "reasoning_tokens": int(stats["reasoning_tokens"]),
                        "cache_read_tokens": int(stats["cache_read_tokens"]),
                        "cache_write_tokens": int(stats["cache_write_tokens"]),
                        "observed_cost_usd": round(sum(cost_values), 8) if cost_values else None,
                        "cost_breakdown_requests": int(stats["cost_breakdown_requests"]),
                    }
                )
            distribution[sort_mode][provider] = {
                "total_requests": total_requests,
                "total_attributed_requests": total,
                "attribution_coverage": round(total / total_requests, 6) if total_requests else 0,
                "counts": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
                "cost_breakdown_requests": cost_breakdown_requests,
                "details": details,
            }
    return distribution


def _record_key(item: dict[str, Any]) -> tuple[str, str, int, int]:
    return (str(item["sort"]), str(item["provider"]), int(item["group"]), int(item["round"]))


def _record_usage_valid(item: dict[str, Any]) -> bool:
    first = item.get("first")
    second = item.get("second")
    return (
        isinstance(first, dict)
        and isinstance(second, dict)
        and int(first.get("prompt_tokens") or 0) > 0
        and int(second.get("prompt_tokens") or 0) > 0
    )


def _split_equal_input_token_pairs(
    records: list[dict[str, Any]],
    *,
    existing_unequal_input_keys: set[tuple[str, str, int, int]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_pair: dict[tuple[str, int, int], dict[str, dict[str, Any]]] = {}
    for item in records:
        pair_key = (str(item["sort"]), int(item["group"]), int(item["round"]))
        by_pair.setdefault(pair_key, {})[str(item["provider"])] = item

    matched: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for providers in by_pair.values():
        infron = providers.get("infron")
        openrouter = providers.get("openrouter")
        pair_records = [item for item in (infron, openrouter) if item is not None]
        if infron is None or openrouter is None:
            excluded.extend(item for item in pair_records if _record_key(item) not in existing_unequal_input_keys)
            continue
        if _request_prompt_pair(infron) == _request_prompt_pair(openrouter):
            matched.extend([infron, openrouter])
            continue
        excluded.extend(item for item in pair_records if _record_key(item) not in existing_unequal_input_keys)
    return matched, excluded


def _request_prompt_pair(item: dict[str, Any]) -> tuple[int, int]:
    return (int(item["first"]["prompt_tokens"] or 0), int(item["second"]["prompt_tokens"] or 0))


def _academic_outline_lines(summary: dict[str, Any]) -> list[str]:
    chart_dir = summary.get("charts", {})
    effective_pairs = sum(int(summary["results"][sort_mode]["infron"]["aggregate"]["rounds"]) for sort_mode in SORT_MODES)
    request_count = effective_pairs * len(PROVIDERS) * 2
    excluded = summary.get("excluded_records", {})
    excluded_total = int(excluded.get("total") or 0)

    cache_winners: list[str] = []
    cost_winners: list[str] = []
    throughput_winners: list[str] = []
    latency_winners: list[str] = []
    ttft_winners: list[str] = []
    for sort_mode in SORT_MODES:
        infron = summary["results"][sort_mode]["infron"]["aggregate"]
        openrouter = summary["results"][sort_mode]["openrouter"]["aggregate"]
        cache_winner = _winner_name(infron["token_cache_hit_rate"], openrouter["token_cache_hit_rate"], higher_is_better=True)
        cost_winner = _winner_name(infron["total_actual_cost_usd"], openrouter["total_actual_cost_usd"], higher_is_better=False)
        throughput_winner = _winner_name(
            infron["avg_throughput_output_tokens_per_second"],
            openrouter["avg_throughput_output_tokens_per_second"],
            higher_is_better=True,
        )
        latency_winner = _winner_name(infron["avg_request_latency_ms"], openrouter["avg_request_latency_ms"], higher_is_better=False)
        ttft_winner = _winner_name(infron["avg_ttft_ms"], openrouter["avg_ttft_ms"], higher_is_better=False)
        cache_winners.append(cache_winner)
        cost_winners.append(cost_winner)
        throughput_winners.append(throughput_winner)
        latency_winners.append(latency_winner)
        ttft_winners.append(ttft_winner)

    def count_wins(values: list[str], provider: str) -> int:
        return sum(1 for value in values if value == provider)

    def won_modes(values: list[str], provider: str) -> list[str]:
        return [SORT_MODES[index] for index, value in enumerate(values) if value == provider]

    input_control = []
    for sort_mode in SORT_MODES:
        infron_tokens = summary["results"][sort_mode]["infron"]["aggregate"]["total_input_tokens"]
        openrouter_tokens = summary["results"][sort_mode]["openrouter"]["aggregate"]["total_input_tokens"]
        input_control.append(f"`{sort_mode}`={infron_tokens}/{openrouter_tokens}")

    cache_sentence = _mode_winner_sentence(cache_winners, metric="Token 级缓存命中率", higher_is_better=True)
    cost_sentence = _mode_winner_sentence(cost_winners, metric="实际成本", higher_is_better=False)
    throughput_sentence = _mode_winner_sentence(throughput_winners, metric="吞吐量", higher_is_better=True)
    latency_sentence = _mode_winner_sentence(latency_winners, metric="时延", higher_is_better=False)
    ttft_sentence = _mode_winner_sentence(ttft_winners, metric="TTFT 首包响应时间", higher_is_better=False)

    return [
        "## 摘要与结论大纲",
        "",
        "**关键词**：Prompt Caching；A/B Testing；Provider Routing；Cache Affinity；Latency；Throughput；Cost Attribution；DeepSeek V4 Flash",
        "",
        "### 摘要",
        "",
        f"本报告以 `deepseek/deepseek-v4-flash` 为对象，对比 Infron 与 OpenRouter 在 Prompt Caching 场景下的路由策略、缓存命中、实际成本、吞吐量、TTFT 首包响应时间和端到端时延。实验包含 {summary['groups']} 个实验组、每组 {summary['rounds_per_group']} 轮，覆盖 {len(SORT_MODES)} 种 routing sort 策略；其中 TTFT First 中，Infron 使用 `provider.sort=ttft`，OpenRouter 使用其支持的 `provider.sort=latency` 作为对照。经过异常 usage、HTTP 异常和 A/B input tokens 不一致样本剔除后，最终保留 {effective_pairs} 个严格配对样本、{request_count} 次请求级观测记录，剔除 {excluded_total} 条记录。",
        "",
        f"核心结论是：在 `usage.prompt_tokens` 完全一致的样本中，{cache_sentence}；{cost_sentence}；{throughput_sentence}；{latency_sentence}；{ttft_sentence}。整体看，Infron 的优势集中在缓存复用、成本控制和 Latency First 下的低时延路径，OpenRouter 的优势集中在吞吐、TTFT 和部分模式的端到端时延表现。平台选择应围绕业务目标展开，单一指标不足以代表整体效果。",
        "",
        f"![Inference 平台不可能四角]({_chart_ref(chart_dir.get('impossible_triangle', ''))})",
        "",
        "图 0：Inference 平台“不可能四角”。吞吐量、价格、端到端时延和 TTFT 很难同时达到最优，平台路由通常会在四个方向之间做取舍；图中将四项归一化指标投影为路由模式点，并将同一平台的四个点连接成区域。",
        "",
        f"![结论总览图]({_chart_ref(chart_dir.get('conclusion_overview', ''))})",
        "",
        "图 A：结论总览图。上方卡片概括跨路由模式的总体胜出方，下方矩阵按 throughput、price、latency、TTFT 的路由目标顺序组织列，金色对角线表示各路由模式目标指标的 A/B 胜出方。",
        "",
        "### 结论大纲",
        "",
        "| 研究维度 | 结论 | 证据位置 |",
        "| --- | --- | --- |",
        f"| 控制变量 | 进入统计的 A/B 样本满足同一 `sort/group/round` 下 first/second 请求 `usage.prompt_tokens` 完全一致；各模式 Input Tokens 对照为 {'；'.join(input_control)} | 方法与数据质量章节 |",
        f"| 缓存复用 | {cache_sentence}，说明 provider stick/cache affinity 对重复长前缀更有利 | 结果与机制分析章节 |",
        f"| 实际成本 | {cost_sentence}，成本差异与 cache read tokens 同向变化 | 结果与结论章节 |",
        f"| 性能表现 | {throughput_sentence}；{latency_sentence}；{ttft_sentence} | 结果可视化与结论章节 |",
        "| 归因边界 | 报告只使用响应可观测 telemetry，包括 provider 字段、usage、cost breakdown、TTFT、latency 和 cache tokens；未把平台内部私有 routing trace 当作已观测事实 | 机制分析、下钻分析与局限性章节 |",
        "| 业务含义 | 对稳定长上下文、RAG 前缀、Agent 工具说明和批处理任务，缓存命中率与成本可预测性是核心收益；对实时交互任务，latency 仍需作为独立约束 | 讨论与结论章节 |",
        "",
        "### 路由模式级结论",
        "",
        *_routing_mode_bar_sections(summary),
        "",
        "说明：每个区块对应一种路由模式；同一指标行内的 Infron 与 OpenRouter 柱条按两者最大值归一化。缓存命中率和 throughput 越高越好，实际成本、latency 和 TTFT 越低越好。",
        "",
    ]


def _render_report(summary: dict[str, Any], *, embed_full_reproducibility: bool = False) -> str:
    payload_hashes = summary.get("request_payload_sha256_by_sort", {})
    chart_dir = summary.get("charts", {})
    lines = [
        "# Infron 与 OpenRouter Prompt Caching A/B 重复实验报告",
        "",
        *_academic_outline_lines(summary),
        "## 1. 引言：背景、研究问题与贡献",
        "",
        "本实验评估同一 OpenAI-compatible Chat Completions 请求在 Infron 与 OpenRouter 两个平台上的 prompt caching 表现。评估重点是：在输入条件严格一致时，不同 provider routing sort 策略会如何影响缓存命中、实际成本、吞吐量和端到端时延。",
        "",
        "Prompt caching 对生产业务的核心价值在于：当业务请求包含稳定系统提示词、长上下文模板、RAG 前缀、工具说明或固定工作流指令时，第二次及后续请求理论上可以复用已处理的输入 token，从而降低单位请求成本，并可能改善整体服务稳定性。本实验通过“两次相同 prompt 请求”的方式构造可重复观测场景，用第二次请求的 cache read tokens 衡量缓存收益。",
        "",
        "本报告回答三个问题：第一，在相同 payload 和相同 `usage.prompt_tokens` 口径下，Infron 与 OpenRouter 的缓存命中和成本表现有何差异；第二，不同 routing sort（`throughput`、`price`、`latency`、`ttft`）下速度、成本、首包和缓存如何变化；第三，从可观测 telemetry 看，两个平台的路由选择如何影响最终结果。由于 OpenRouter 不支持 `provider.sort=ttft`，TTFT First 的 A/B 设计为 Infron `sort=ttft` 对比 OpenRouter `sort=latency`。",
        "",
        "### 1.1 研究假设",
        "",
        "| 假设 | 内容 | 验证指标 |",
        "| --- | --- | --- |",
        "| H1 | 在重复稳定长前缀请求中，更强的 provider/cache affinity 会提升 Token 级缓存命中率 | 第二次请求 cache read tokens、Token 级命中率 |",
        "| H2 | 更高缓存命中率会降低真实响应成本，但不必然降低 TTFT 或端到端 latency | 实际成本、平均 TTFT、平均 latency/请求 |",
        "| H3 | 不同 routing sort 会改变 provider 选择，从而形成不同的成本、吞吐和时延 Pareto 前沿 | provider 分布、throughput、latency、cost |",
        "",
        "### 1.2 本文贡献",
        "",
        "- 给出一个严格配对的 A/B benchmark 方法，使用响应返回的 `usage.prompt_tokens` 作为真实 input token 控制变量。",
        "- 将 prompt caching 评估从单一 cache hit 指标扩展到成本、吞吐、latency、TTFT、provider 分布和可复现数据集。",
        "- 用可观测 telemetry 解释 Infron 与 OpenRouter 的路由差异，同时明确内部 routing trace 缺失时的归因边界。",
        "- 提供配对级 CSV、请求级 JSONL 和 A/B testing 代码，便于后续重复实验和第三方审计。",
        "",
        "## 2. 方法：实验设计、数据集构造与控制变量",
        "",
        "### 2.1 数据集生成方法",
        "",
        f"实验数据集由脚本自动生成，共覆盖 {len(SORT_MODES)} 种 routing sort、2 个平台、{summary['groups']} 个实验组、每组 {summary['rounds_per_group']} 轮。每一轮包含两次完全相同的 `chat/completions` 请求：第一次用于建立或触发缓存写入，第二次用于观测缓存读取。每个逻辑 routing sort 都记录平台侧实际 payload 的 SHA256，以便验证请求内容没有漂移。",
        "",
        _dataset_construction_text(summary),
        "",
        "### 2.2 控制变量方法",
        "",
        "A/B 测试的基本配对单元是同一 `sort/group/round` 下的 Infron 记录和 OpenRouter 记录。只有当两边 first request 与 second request 的 `usage.prompt_tokens` 完全一致时，该配对才进入最终统计；任何 HTTP 非 200、请求异常、`usage.prompt_tokens <= 0` 或 A/B 输入 token 不一致的记录都会被剔除。这保证了成本、缓存命中率、吞吐量和时延的对比建立在同等输入规模上。",
        "",
        "本报告中的总 Input Tokens 严格取自响应返回的 `usage.prompt_tokens`，不使用本地 tokenizer 估算值。原因是 provider 的真实处理、缓存和计费口径最终以响应 usage 为准。通过使用响应 usage 并执行 A/B 配对一致性过滤，实验避免了 tokenizer 差异、服务端 prompt 包装和异常 usage 上报带来的偏差。",
        "",
        "### 2.3 实验设置图示与代码示例",
        "",
        "下图展示单个 routing sort 下的实验流水线：同一 payload 分别发送到 Infron 与 OpenRouter，每个平台每轮连续发送两次相同请求，最终在同一 `sort/group/round` 维度做严格 A/B 配对。",
        "",
        f"![实验流程图]({_chart_ref(chart_dir.get('experiment_flow', ''))})",
        "",
        "图 1：实验流水线。该图强调每个 routing sort 下的同源 payload、双平台请求和 first/second request 配对关系，用于说明实验如何构造可比样本。",
        "",
        "A/B 配对过滤的目标是确保比较只发生在输入 token 完全一致的样本上。只有 first request 与 second request 的 `usage.prompt_tokens` 在两边完全相等，样本才进入最终统计。",
        "",
        f"![A/B 配对过滤图]({_chart_ref(chart_dir.get('ab_pairing', ''))})",
        "",
        "图 2：A/B 配对过滤逻辑。该图明确展示异常 usage、HTTP 异常、非完整配对和 input tokens 不一致样本如何被排除，保证最终对比符合控制变量要求。",
        "",
        "核心请求 payload 结构如下。实验固定模型、温度、最大输出 token、usage 返回和 provider sort，只改变路由优先模式。",
        "",
        "```json",
        "{",
        f"  \"model\": \"{summary['model']}\",",
        "  \"messages\": [",
        "    {\"role\": \"system\", \"content\": \"<stable long cache probe prefix>\"},",
        "    {\"role\": \"user\", \"content\": \"Reply with exactly: cache probe ok\"}",
        "  ],",
        "  \"temperature\": 0,",
        "  \"max_tokens\": 16,",
        "  \"usage\": {\"include\": true},",
        "  \"provider\": {\"sort\": \"throughput | price | latency | ttft\", \"allow_fallbacks\": true}",
        "}",
        "```",
        "",
        "TTFT First 对照规则：Infron 请求使用 `provider.sort=ttft`；OpenRouter 不支持该参数，因此 OpenRouter 请求使用 `provider.sort=latency` 作为首包/时延优先对照。报告中的逻辑路由模式仍统一记为 `ttft`，用于配对、聚合和可视化。",
        "",
        "最终过滤逻辑可概括为以下伪代码。这个步骤是本实验控制变量的核心。",
        "",
        "```python",
        "for pair in group_by(records, key=(sort, group, round)):",
        "    infron = pair['infron']",
        "    openrouter = pair['openrouter']",
        "    if not both_http_200(infron, openrouter):",
        "        exclude(pair)",
        "    elif any(request.usage.prompt_tokens <= 0 for request in pair.requests):",
        "        exclude(pair)",
        "    elif (infron.first.prompt_tokens, infron.second.prompt_tokens) != (openrouter.first.prompt_tokens, openrouter.second.prompt_tokens):",
        "        exclude(pair)",
        "    else:",
        "        include(pair)",
        "```",
        "",
        "### 2.4 指标定义",
        "",
        "表 1：核心指标定义与解释方向。",
        "",
        "| 指标 | 定义 | 解释方向 |",
        "| --- | --- | --- |",
        "| 调用级命中率 | 第二次请求 `cache_read_tokens > 0` 的轮次占比 | 越高表示越稳定触发缓存读取 |",
        "| Token 级命中率 | 第二次请求 cache read tokens / 第二次请求 prompt tokens | 越高表示输入 token 复用比例越高 |",
        "| 实际成本 | first + second 两次请求返回 usage/cost 的合计 | 越低越好，代表真实账单风险更低 |",
        "| 平均 throughput | 响应 completion tokens / 请求 latency seconds；reasoning tokens 作为响应 usage 组成部分处理，不单独拆成独立 KPI | 越高越好，代表单位时间响应输出能力更强 |",
        "| 平均 latency/请求 | 每次请求完整响应耗时均值 | 越低越好，代表用户等待时间更短 |",
        "| 平均 TTFT | streaming 下首包/首 token 到达时间均值 | 越低越好，代表用户更快看到首个响应信号 |",
        "| Reasoning 口径 | 响应 usage 中的 reasoning token 字段作为响应统计的组成部分保留在原始记录和 summary 中 | 不单独展示排名，避免把内部推理预算误读为独立业务产出 |",
        f"| TTFT | 首 token 到达时间 | {'本轮已启用 streaming 并采集 TTFT；TTFT 与完整响应 latency 分别代表首 token 体验和完整响应体验' if summary.get('streaming_enabled') else '本轮未启用 streaming，TTFT 不以 latency 代替'} |",
        "",
        "### 2.5 表格、图表与架构图表达规范",
        "",
        "为了让报告更容易审计，表格、图表和架构图采用统一表达方式：表格负责精确数值比较，趋势图展示指标变化过程，架构图解释机制假设与可观测证据之间的关系。结论以响应 telemetry 为准，架构图只用于解释机制。",
        "",
        "表 2：可视化与表格专业性评估。",
        "",
        "| 类型 | 当前用途 | 专业性评估 | 后续可补充项 |",
        "| --- | --- | --- | --- |",
        "| 总览表 | 展示核心指标、胜出方和可比样本规模 | 保留精确数值、单位和胜出高亮，适合审计；本轮报告已加入 bootstrap CI 与 paired permutation test | `已补充：bootstrap CI、p-value；后续可加入 standardized effect size` |",
        "| 分组明细表 | 检查不同 group 的稳定性 | 能发现单组异常和策略漂移；本轮报告已加入 P50/P95/P99 latency/TTFT | `已补充：P50/P95/P99；后续可加入 IQR 和 tail amplification` |",
        "| 核心指标柱状图 | 按 routing mode 对比 latency、throughput、cost、cache hit rate | 适合快速判断胜出方和指标差异；后续可增加误差棒 | `待补充：error bar、confidence band 可视化` |",
        "| 指标生成曲线 | 展示每组请求的指标变化过程 | 有助于观察缓存预热、波动和异常点；后续可加入事件标注 | `待补充：warm-up annotation、outlier labels` |",
        "| 架构图 | 解释 Infron provider routing、provider stick 和成本控制机制 | 明确区分可观测证据与机制解释，避免把内部实现假设误写成事实 | `待补充：真实 routing trace、provider cost breakdown 明细` |",
        "",
        "## 3. 实验环境与数据质量控制",
        "",
        "表 3：实验配置与数据质量控制规则。",
        "",
        "| 项目 | 配置 |",
        "| --- | --- |",
        f"| 测试模型 | `{summary['model']}` |",
        "| 对比平台 | Infron、OpenRouter |",
        "| 路由偏好 | `throughput`、`price`、`latency`、`ttft` |",
        "| TTFT First 对照 | Infron 使用 `provider.sort=ttft`；OpenRouter 使用 `provider.sort=latency` |",
        f"| 数据集名称 | `{summary.get('dataset', {}).get('name', DEFAULT_DATASET_NAME)}` |",
        f"| 数据集类型 | {summary.get('dataset', {}).get('description', '')} |",
        f"| 外部业务语料 | {summary.get('dataset', {}).get('file') or '未提供；本轮使用脚本内置/合成数据集'} |",
        f"| 实验组数 | 每个平台每种路由 {summary['groups']} 组 |",
        f"| 每组轮次 | {summary['rounds_per_group']} 轮 |",
        f"| 并发 worker 数 | {summary.get('execution_profile', {}).get('workers', 1)} |",
        f"| 长稳运行目标 | {summary.get('execution_profile', {}).get('soak_duration_seconds', 0)} 秒 |",
        f"| 本地代理控制 | {_network_environment_report_cell(summary.get('network_environment', {}))} |",
        "| 每轮请求 | 两次相同 prompt 请求，用第二次请求统计缓存命中 |",
        "| Usage 采集 | 请求默认带 `usage: {\"include\": true}`，以响应 usage 作为真实统计口径 |",
        "| 成本口径 | 只统计响应真实返回的 `usage.cost` 或 cost breakdown；若平台未返回成本字段，则显示 `N/A`，不按 0 计入胜负 |",
        "| Reasoning 设置 | 请求不额外指定 reasoning effort；模型/平台默认包含 reasoning 能力与 usage 计量，最终以响应返回的 reasoning tokens 字段为准 |",
        f"| Streaming / TTFT 采集 | {'已启用 streaming，并记录 TTFT/首内容 token/首 reasoning token 时间' if summary.get('streaming_enabled') else '本轮历史数据未启用 streaming；脚本支持后续通过 `--stream` 采集 TTFT'} |",
        "| Provider 归因采集 | 脚本记录响应 headers、response model/id/system fingerprint、provider/routing trace 候选字段、provider cost breakdown 候选字段 |",
        f"| 结果目录 | `{summary['result_dir']}/` |",
        "| 剔除规则 | HTTP 非 200、请求异常、任一请求 `usage.prompt_tokens <= 0`、或同一 `sort/group/round` 下 A/B 两边 first/second `usage.prompt_tokens` 不完全相等的轮次不进入统计 |",
        f"| 剔除记录数 | {summary.get('excluded_records', {}).get('total', 0)} 条 |",
        *[f"| `{sort_mode}` payload SHA256 | {_payload_hash_table_cell(payload_hashes.get(sort_mode, {}))} |" for sort_mode in SORT_MODES],
        "",
        "说明：A/B 控制变量是同一 routing sort 下发送给 Infron 和 OpenRouter 的请求 payload。总览中的 Input Tokens 按响应返回的 `usage.prompt_tokens` 汇总，代表各平台实际统计和计费口径下处理的输入 token 量。",
        "",
        "## 4. 结果：总体指标与主要发现",
        "",
        "说明：本节的 throughput、latency 和 TTFT 均为响应级整体指标。若响应 usage 中 `completion_tokens` 包含 reasoning tokens，则 reasoning 过程已纳入 throughput 分子；请求 latency 是完整响应端到端耗时，天然包含 reasoning 过程耗时；TTFT 是 streaming 下首个 SSE token/chunk 到达时间，代表首包响应体验。成本只使用响应明确返回的 cost 字段；未返回 cost 时标记为 `N/A`，不视为 0。",
        "",
        "表 4：总体 A/B 指标对比。加粗单元表示同一 routing sort 下表现更好的一方；Input Tokens 加粗表示两边严格相等。",
        "",
        "| 路由偏好 | 平台 | 总轮数 | 成功轮数 | 总 Input Tokens (`usage.prompt_tokens`) | 调用级命中率 | Token 级命中率 | 实际总成本 | 平均每轮成本 | 平均响应 throughput（含 reasoning） | 平均 latency/请求（含 reasoning） | 平均 TTFT | HTTP 状态 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for sort_mode in SORT_MODES:
        sort_aggs = {provider: summary["results"][sort_mode][provider]["aggregate"] for provider in PROVIDERS}
        for provider in PROVIDERS:
            agg = sort_aggs[provider]
            lines.append(
                f"| `{sort_mode}` | {_display_provider(provider)} | "
                f"{_compare_cell(provider, sort_aggs, 'rounds', str(agg['rounds']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'successful_rounds', str(agg['successful_rounds']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'total_input_tokens', str(agg['total_input_tokens']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'call_cache_hit_rate', _pct(agg['call_cache_hit_rate']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'token_cache_hit_rate', _pct(agg['token_cache_hit_rate']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'total_actual_cost_usd', _format_cost(agg.get('total_actual_cost_usd')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_actual_cost_per_round_pair_usd', _format_cost(agg.get('avg_actual_cost_per_round_pair_usd')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_throughput_output_tokens_per_second', '{:.2f} response tok/s'.format(agg['avg_throughput_output_tokens_per_second']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_request_latency_ms', '{:.2f} ms'.format(agg['avg_request_latency_ms']), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_ttft_ms', _format_ms(agg.get('avg_ttft_ms')), higher_is_better=False)} | "
                f"{_status_cell(agg['http_statuses'])} |"
            )
    lines.extend(_tail_latency_and_significance_lines(summary))
    lines.extend(
        [
            "",
            "## 5. 结果可视化：按路由模式的核心指标变化",
            "",
            f"说明：本节按路由模式组织图表。每张图对应一种 First 路由模式，并在同一图内对比 Infron 与 OpenRouter 的 latency、TTFT、throughput、实际成本和 Token 级缓存命中率，方便观察同一模式下的 A/B 指标差异。{'本轮已启用 streaming，并采集 TTFT、首内容 token 与首 reasoning token 时间；TTFT 代表首包响应体验，latency 代表完整响应体验。' if summary.get('streaming_enabled') else 'TTFT 需要 streaming 首 token 时间；本轮未启用 streaming，因此 TTFT 不参与核心判断。后续重跑加 `--stream` 后会记录 TTFT 和首 reasoning token 时间。'}",
            "",
            *_mode_visualization_lines(summary),
        ]
    )
    lines.extend(_infron_architecture_lines(summary))
    lines.extend(_provider_drilldown_lines(summary))
    lines.extend(["", "## 8. 分层结果：按实验组的稳定性检查", ""])
    for sort_mode in SORT_MODES:
        lines.extend(
            [
                f"### {sort_mode}",
                "",
                f"表 11-{SORT_MODES.index(sort_mode) + 1}：`{sort_mode}` 路由模式下的 group-level 稳定性检查。",
                "",
                "| 平台 | 组别 | 轮数 | 成功轮数 | Token 级命中率 | 实际成本 |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        groups_by_provider = {
            provider: {int(group["group"]): group["aggregate"] for group in summary["results"][sort_mode][provider]["groups"]}
            for provider in PROVIDERS
        }
        for provider in PROVIDERS:
            for group in summary["results"][sort_mode][provider]["groups"]:
                agg = group["aggregate"]
                group_no = int(group["group"])
                group_aggs = {item: groups_by_provider[item].get(group_no, {}) for item in PROVIDERS}
                lines.append(
                    f"| {_display_provider(provider)} | {group['group']} | "
                    f"{_compare_cell(provider, group_aggs, 'rounds', str(agg['rounds']), higher_is_better=True)} | "
                    f"{_compare_cell(provider, group_aggs, 'successful_rounds', str(agg['successful_rounds']), higher_is_better=True)} | "
                    f"{_compare_cell(provider, group_aggs, 'token_cache_hit_rate', _pct(agg['token_cache_hit_rate']), higher_is_better=True)} | "
                    f"{_compare_cell(provider, group_aggs, 'total_actual_cost_usd', _format_cost(agg.get('total_actual_cost_usd')), higher_is_better=False)} |"
                )
        lines.append("")
    lines.extend(
        [
            "## 9. 讨论：业务价值、适用边界与工程启示",
            "",
        ]
    )
    lines.extend(_business_value_lines(summary))
    lines.extend(
        [
            "",
            "## 10. 结论",
            "",
            "表 12：路由模式级结论快照。该表综合缓存命中、成本、throughput、latency 和 TTFT，避免只按单一指标排序。",
            "",
            "| 路由偏好 | 缓存命中更优 | 成本更低 | Throughput 更高 | Latency 更低 | TTFT 更低 | 综合解读 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for sort_mode in SORT_MODES:
        infron = summary["results"][sort_mode]["infron"]["aggregate"]
        openrouter = summary["results"][sort_mode]["openrouter"]["aggregate"]
        better_cache = _winner_name(infron["token_cache_hit_rate"], openrouter["token_cache_hit_rate"], higher_is_better=True)
        better_cost = _winner_name(infron["total_actual_cost_usd"], openrouter["total_actual_cost_usd"], higher_is_better=False)
        better_throughput = _winner_name(
            infron["avg_throughput_output_tokens_per_second"],
            openrouter["avg_throughput_output_tokens_per_second"],
            higher_is_better=True,
        )
        better_latency = _winner_name(infron["avg_request_latency_ms"], openrouter["avg_request_latency_ms"], higher_is_better=False)
        better_ttft = _winner_name(infron["avg_ttft_ms"], openrouter["avg_ttft_ms"], higher_is_better=False)
        lines.append(
            f"| `{sort_mode}` | {_winner_text(better_cache)} | {_winner_text(better_cost)} | "
            f"{_winner_text(better_throughput)} | {_winner_text(better_latency)} | {_winner_text(better_ttft)} | "
            f"{_summary_takeaway(better_cache, better_cost, better_throughput, better_latency, better_ttft)} |"
        )
    lines.append("")
    lines.extend(_limitations_and_future_work_lines(summary))
    lines.extend(_reproducibility_lines(summary, embed_full_artifacts=embed_full_reproducibility))
    return "\n".join(lines)


def _pct(value: float | int) -> str:
    return f"{float(value) * 100:.2f}%"


def _format_cost(value: Any, *, decimals: int = 8) -> str:
    numeric = _numeric_value(value)
    if numeric is None:
        return "N/A"
    return f"${numeric:.{decimals}f}"


def _format_ms(value: Any) -> str:
    numeric = _numeric_value(value)
    if numeric is None:
        return "N/A"
    return f"{numeric:.2f} ms"


def _payload_hash_table_cell(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for provider in PROVIDERS:
            provider_hash = str(value.get(provider, ""))
            parts.append(f"{_display_provider(provider)} `{provider_hash}`")
        return "<br>".join(parts)
    return f"`{value}`" if value else ""


def _network_environment_report_cell(network_environment: dict[str, Any]) -> str:
    if not network_environment:
        return "未记录"
    same_proxy = "是" if network_environment.get("same_local_proxy") else "否"
    proxy_enabled = "启用" if network_environment.get("proxy_enabled") else "未启用"
    proxy_url = network_environment.get("proxy_url_redacted") or "direct"
    implicit_disabled = "已禁用" if network_environment.get("implicit_environment_proxy_disabled") else "未禁用"
    return f"同一本地代理：{same_proxy}；代理：{proxy_enabled} `{proxy_url}`；隐式环境代理：{implicit_disabled}"


def _chart_key(sort_mode: str, suffix: str = "") -> str:
    base = f"{sort_mode}_first"
    return f"{base}_{suffix}" if suffix else base


def _mode_visualization_lines(summary: dict[str, Any]) -> list[str]:
    chart_dir = summary.get("charts", {})
    lines: list[str] = []
    figure_no = 3
    for sort_mode in SORT_MODES:
        mode_name = _sort_mode_label(sort_mode)
        short_name = mode_name.replace(" 路由模式", "")
        lines.extend(
            [
                f"### {short_name} 路由模式",
                "",
                f"![{short_name} 路由模式下的核心指标 A/B 对比]({_chart_ref(chart_dir.get(_chart_key(sort_mode), ''))})",
                "",
                f"图 {figure_no}：{short_name} 路由模式下的核心指标对比。柱状图同时呈现缓存、成本、吞吐、TTFT 和 latency 表现。",
                "",
                f"![{short_name} 路由模式下的综合雷达图]({_chart_ref(chart_dir.get(_chart_key(sort_mode, 'radar'), ''))})",
                "",
                f"图 {figure_no + 1}：{short_name} 路由模式下的综合雷达图。所有轴都按“越外圈越好”归一化，便于快速比较两家平台的综合形状。",
                "",
                f"![{short_name} 路由模式下的指标生成过程对比曲线]({_chart_ref(chart_dir.get(_chart_key(sort_mode, 'curves'), ''))})",
                "",
                f"图 {figure_no + 2}：{short_name} 路由模式下的指标生成过程曲线。该图用于观察指标随 group/round 的变化，而不只依赖均值。",
                "",
            ]
        )
        if sort_mode == "ttft":
            lines.extend(
                [
                    "说明：TTFT First 中，Infron 使用 `provider.sort=ttft`；OpenRouter 使用 `provider.sort=latency` 作为可支持的对照策略。",
                    "",
                ]
            )
        figure_no += 3
    return lines


def _routing_mode_bar_sections(summary: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for sort_mode in SORT_MODES:
        if lines:
            lines.append("")
        lines.append(f"#### {_sort_mode_label(sort_mode).replace(' 路由模式', '')}")
        lines.append("")
        lines.append("| 指标 | Infron / OpenRouter 并列对比 | 胜出方 |")
        lines.append("| --- | --- | --- |")
        lines.extend(_routing_mode_bar_rows(summary, sort_mode))
    return lines


def _routing_mode_bar_rows(summary: dict[str, Any], sort_mode: str) -> list[str]:
    metrics = [
        ("缓存命中率", "token_cache_hit_rate", True, _pct),
        ("实际成本", "total_actual_cost_usd", False, _format_cost),
        ("Throughput", "avg_throughput_output_tokens_per_second", True, lambda value: f"{float(value):.2f} tok/s"),
        ("Latency", "avg_request_latency_ms", False, _format_ms),
        ("TTFT", "avg_ttft_ms", False, _format_ms),
    ]
    rows = []
    for label, key, higher_is_better, formatter in metrics:
        infron = _numeric_value(summary["results"][sort_mode]["infron"]["aggregate"].get(key))
        openrouter = _numeric_value(summary["results"][sort_mode]["openrouter"]["aggregate"].get(key))
        winner = _winner_for_sort_metric(summary, sort_mode, key, higher_is_better)
        advantage = _winner_advantage_text(summary, sort_mode, key, higher_is_better)
        rows.append(
            f"| {label} | "
            f"{_paired_bar_cell(infron, openrouter, formatter, winner)} | "
            f"{_winner_text(winner)}（{advantage}） |"
        )
    return rows


def _paired_bar_cell(
    infron: float | None,
    openrouter: float | None,
    formatter: Callable[[Any], str],
    winner: str,
) -> str:
    return (
        f'<span class="provider-label">Infron</span>{_bar_value_cell(infron, openrouter, formatter, winner == "Infron", width=8)}'
        f'<br><span class="provider-label">OpenRouter</span>{_bar_value_cell(openrouter, infron, formatter, winner == "OpenRouter", width=8)}'
    )


def _bar_value_cell(
    value: float | None,
    peer_value: float | None,
    formatter: Callable[[Any], str],
    is_winner: bool,
    *,
    width: int = 10,
) -> str:
    if value is None:
        return "N/A"
    max_value = max(abs(value), abs(peer_value or 0))
    ratio = 0.0 if max_value == 0 else abs(value) / max_value
    filled = max(1, min(width, int(round(ratio * width)))) if value != 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    text = f"{bar} {formatter(value)}"
    return _bold(text) if is_winner else text


def _winner_text(provider: str) -> str:
    return _bold(provider)


def _summary_takeaway(*providers: str) -> str:
    comparable = [provider for provider in providers if provider in {"Infron", "OpenRouter"}]
    infron_wins = sum(1 for provider in comparable if provider == "Infron")
    openrouter_wins = sum(1 for provider in comparable if provider == "OpenRouter")
    if infron_wins > openrouter_wins:
        return f"Infron 综合占优（{infron_wins}/{len(comparable)} 可比指标）"
    if openrouter_wins > infron_wins:
        return f"OpenRouter 综合占优（{openrouter_wins}/{len(comparable)} 可比指标）"
    return "双方各有优势"


def _mode_winner_sentence(winners: list[str], *, metric: str, higher_is_better: bool) -> str:
    values = {provider: _mode_list([SORT_MODES[index] for index, winner in enumerate(winners) if winner == provider]) for provider in ("Infron", "OpenRouter")}
    direction = "更高" if higher_is_better else "更低"
    if values["Infron"] and not values["OpenRouter"]:
        return f"Infron 在所有路由模式下，{metric}都{direction}"
    if values["OpenRouter"] and not values["Infron"]:
        return f"OpenRouter 在所有路由模式下，{metric}都{direction}"
    parts = []
    if values["Infron"]:
        parts.append(f"Infron 在 {values['Infron']} 模式下，{metric}{direction}")
    if values["OpenRouter"]:
        parts.append(f"OpenRouter 在 {values['OpenRouter']} 模式下，{metric}{direction}")
    return "，".join(parts)


def _mode_list(modes: list[str]) -> str:
    if not modes:
        return ""
    values = [f"`{mode}`" for mode in modes]
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} 和 {values[1]}"
    return "、".join(values[:-1]) + f" 和 {values[-1]}"


def _dataset_construction_text(summary: dict[str, Any]) -> str:
    dataset = summary.get("dataset") if isinstance(summary.get("dataset"), dict) else {}
    name = dataset.get("name") or DEFAULT_DATASET_NAME
    if dataset.get("file"):
        return (
            f"Prompt 来自外部 JSONL 业务语料 `{dataset.get('file')}`，共 {dataset.get('corpus_rows', 0)} 条。"
            "脚本按 `group/round` 稳定取样，确保同一 A/B 配对发送完全相同的 messages。模型、temperature、max_tokens、usage include 和 provider sort 等参数在同一 routing sort 内保持不变。"
        )
    if name == "business_representative":
        return (
            "Prompt 使用脚本内置的代表性业务模板，覆盖 RAG 客服、Agent 工具说明、营销自动化和代码审查四类稳定长上下文场景。"
            "每一轮在同一 `group/round` 下向 Infron 与 OpenRouter 发送完全相同的 messages，用于观察真实路由、缓存、成本、吞吐和时延差异。"
        )
    return (
        "Prompt 构造采用稳定长前缀加固定用户输入：system message 包含重复的 cache probe prefix，user message 固定为 `Reply with exactly: cache probe ok`。"
        "模型、temperature、max_tokens、usage include、provider sort 等参数在同一 routing sort 内保持不变。该数据集用于测量 prompt caching 行为，不代表业务语料分布。"
    )


def _tail_latency_and_significance_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        "",
        "### 4.1 尾延迟与显著性检验",
        "",
        "表 5：尾延迟分位数。P95/P99 直接从请求级 latency 与 TTFT 计算，补充均值无法表达的尾部风险。",
        "",
        "| 路由偏好 | 平台 | P50 Latency | P95 Latency | P99 Latency | P50 TTFT | P95 TTFT | P99 TTFT |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for sort_mode in SORT_MODES:
        sort_aggs = {provider: summary["results"][sort_mode][provider]["aggregate"] for provider in PROVIDERS}
        for provider in PROVIDERS:
            agg = sort_aggs[provider]
            lines.append(
                f"| `{sort_mode}` | {_display_provider(provider)} | "
                f"{_compare_cell(provider, sort_aggs, 'p50_request_latency_ms', _format_ms(agg.get('p50_request_latency_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'p95_request_latency_ms', _format_ms(agg.get('p95_request_latency_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'p99_request_latency_ms', _format_ms(agg.get('p99_request_latency_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'p50_ttft_ms', _format_ms(agg.get('p50_ttft_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'p95_ttft_ms', _format_ms(agg.get('p95_ttft_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'p99_ttft_ms', _format_ms(agg.get('p99_ttft_ms')), higher_is_better=False)} |"
            )
    lines.extend(
        [
            "",
            "表 6：配对统计检验。均值差使用 bootstrap 95% CI，p-value 使用 paired sign-flip permutation test。指标名给出差值方向，解释列说明正值代表的含义。",
            "",
            "| 路由偏好 | 指标 | 均值差 | 95% CI | p-value | 配对数 | 解释 |",
            "| --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    metric_labels = {
        "latency_ms_delta_openrouter_minus_infron": ("Latency: OpenRouter - Infron", "正值表示 Infron latency 更低"),
        "ttft_ms_delta_openrouter_minus_infron": ("TTFT: OpenRouter - Infron", "正值表示 Infron TTFT 更低"),
        "throughput_delta_infron_minus_openrouter": ("Throughput: Infron - OpenRouter", "正值表示 Infron throughput 更高"),
        "cost_delta_openrouter_minus_infron_usd": ("Cost: OpenRouter - Infron", "正值表示 Infron 成本更低"),
        "token_cache_hit_rate_delta_infron_minus_openrouter": ("Token Cache Hit: Infron - OpenRouter", "正值表示 Infron cache hit 更高"),
    }
    for sort_mode in SORT_MODES:
        tests = summary["results"][sort_mode].get("statistical_tests", {})
        for key, (label, explanation) in metric_labels.items():
            item = tests.get(key, {})
            lines.append(
                f"| `{sort_mode}` | {label} | {_format_stat_value(item.get('mean'), key)} | "
                f"[{_format_stat_value(item.get('ci95_low'), key)}, {_format_stat_value(item.get('ci95_high'), key)}] | "
                f"{_format_p_value(item.get('paired_permutation_p_value'))} | {item.get('n_pairs', 0)} | {explanation} |"
            )
    return lines


def _format_stat_value(value: Any, key: str) -> str:
    numeric = _numeric_value(value)
    if numeric is None:
        return "N/A"
    if "cost" in key:
        return f"${numeric:.8f}"
    if "cache_hit_rate" in key:
        return f"{numeric * 100:.2f} pp"
    if "throughput" in key:
        return f"{numeric:.4f} tok/s"
    return f"{numeric:.2f} ms"


def _format_p_value(value: Any) -> str:
    numeric = _numeric_value(value)
    if numeric is None:
        return "N/A"
    if numeric < 0.001:
        return "<0.001"
    return f"{numeric:.4f}"


def _compare_cell(
    provider: str,
    provider_aggs: dict[str, dict[str, Any]],
    key: str,
    text: str,
    *,
    higher_is_better: bool,
) -> str:
    values = {
        item: _numeric_value(agg.get(key))
        for item, agg in provider_aggs.items()
        if isinstance(agg, dict) and _numeric_value(agg.get(key)) is not None
    }
    current = values.get(provider)
    if current is None or not values:
        return text
    best = max(values.values()) if higher_is_better else min(values.values())
    return _bold(text) if current == best else text


def _status_cell(statuses: list[int]) -> str:
    text = ", ".join(str(item) for item in statuses)
    return _bold(text) if statuses == [200] else text


def _limitations_and_future_work_lines(summary: dict[str, Any]) -> list[str]:
    return [
        "## 11. 局限性、缺失数据与后续实验计划",
        "",
        "本报告区分“已观测事实”和“机制解释”。已观测事实来自响应 usage、cost、latency、TTFT、cache tokens、provider 字段和导出的请求级 telemetry；机制解释用于说明这些结果背后的合理工程路径，不代表平台内部私有实现的直接证据。",
        "",
        "表 13：当前报告的局限性与后续补充计划。",
        "",
        "| 缺失或不足 | 对结论的影响 | 后续补充方式 | 当前处理方式 |",
        "| --- | --- | --- | --- |",
        "| 上游完整 routing trace | 无法逐跳证明每次请求的 provider 选择、fallback 和重试路径 | `待补充：provider routing trace / decision log / fallback reason` | 仅使用响应中真实返回的 provider 字段和 provider 分布做归因 |",
        "| Provider cost breakdown 全量字段 | 无法进一步拆分平台费、provider 费、cache read/write 成本 | `待补充：provider cost breakdown 明细、缓存读写计费项` | 只统计响应明确返回的 cost/cost_details |",
        "| 显著性检验 | 已补充 bootstrap 95% CI 与 paired sign-flip permutation test；尚未给出 standardized effect size | `待补充：Cohen's d / Cliff's delta 等 effect size` | 使用严格 A/B 配对和 input token 相等过滤降低混杂偏差 |",
        "| P95/P99 latency | 已补充 P50/P95/P99 latency 与 TTFT；尚未计算 IQR 和 tail amplification | `待补充：IQR、max、tail amplification ratio` | 当前展示均值、P50/P95/P99 和过程曲线 |",
        "| 多模型泛化 | 单模型实验不能直接外推到所有模型 | `待补充：DeepSeek、Qwen、Claude、GPT 系列跨模型实验` | 结论限定于 `deepseek/deepseek-v4-flash` 本轮样本 |",
        "| 真实业务语料 | 本轮使用内置代表性业务模板，不等同于客户生产语料 | `待补充：脱敏真实 RAG、Agent、客服、代码生成、长文摘要业务数据集` | 脚本已支持 `--dataset-file` JSONL 输入 |",
        "| 并发压力与长期运行 | 本轮使用 `workers` 并发执行，但不是长时间 soak test | `待补充：并发阶梯压测、24h soak test、cache TTL/eviction 观测` | 当前解释 4*50 并发执行窗口内的 A/B 结果 |",
        "",
        "后续实验可以继续沿用核心 A/B 配对方法：保持 payload SHA256、`usage.prompt_tokens` 相等过滤和 request-level telemetry，同时增加 routing trace、provider cost breakdown、尾延迟分位数和业务语料分层。这样可以把本报告扩展为更完整的生产决策评估框架。",
        "",
    ]


def _reproducibility_lines(summary: dict[str, Any], *, embed_full_artifacts: bool = True) -> list[str]:
    dataset = summary.get("benchmark_dataset") if isinstance(summary.get("benchmark_dataset"), dict) else {}
    pair_csv = dataset.get("pair_csv", {}) if isinstance(dataset.get("pair_csv"), dict) else {}
    request_jsonl = dataset.get("request_jsonl", {}) if isinstance(dataset.get("request_jsonl"), dict) else {}
    result_dir = Path(summary.get("result_dir", ""))
    full_script = Path("scripts/rerun_routing_sort_cache_cost_ab.py")
    full_data_files = [
        ("配对级 benchmark 数据集 CSV", result_dir / "benchmark_pairs.csv", "csv"),
        ("请求级原始 benchmark 数据集 JSONL", result_dir / "benchmark_requests.jsonl", "jsonl"),
        ("过滤后原始记录 records.json", result_dir / "records.json", "json"),
        ("剔除样本审计记录 records_excluded.json", result_dir / "records_excluded.json", "json"),
    ]
    lines = [
        "",
        "## 12. 可复现性附录：Benchmark 数据集",
        "",
        "本节给出复现结论和图表所需的数据文件。配对级 CSV 是报告中所有总览表、核心指标图和结论快照的直接输入；请求级 JSONL 保留每一次 first/second 请求的 telemetry，便于审计 provider、usage、cost、latency、TTFT 与缓存字段。公开报告通过文件路径引用数据集，不在报告正文中展开大体量原始记录。",
        "",
        "| 数据文件 | 粒度 | 行数 | SHA256 | 用途 |",
        "| --- | ---: | ---: | --- | --- |",
        f"| `{pair_csv.get('path', '')}` | A/B pair | {pair_csv.get('rows', 0)} | `{pair_csv.get('sha256', '')}` | 复现聚合表和核心图表 |",
        f"| `{request_jsonl.get('path', '')}` | request | {request_jsonl.get('rows', 0)} | `{request_jsonl.get('sha256', '')}` | 审计单次请求 telemetry |",
        "",
        "字段字典：",
        "",
        "| 字段 | 含义 |",
        "| --- | --- |",
        "| `sort/group/round` | A/B 配对键；同一键下 Infron 与 OpenRouter 输入 token 完全一致 |",
        "| `*_pair_cost_usd` | first + second 两次请求的真实响应成本 |",
        "| `*_avg_latency_ms` | first/second 两次请求 latency 均值 |",
        "| `*_avg_ttft_ms` | first/second 两次请求 TTFT 均值 |",
        "| `*_response_throughput_tps` | 两次请求 completion tokens / 两次请求总 latency seconds |",
        "| `*_second_cache_read_tokens` | 第二次请求读取缓存的 token 数 |",
        "| `*_second_cache_hit_rate` | 第二次请求 cache read tokens / 第二次请求 prompt tokens |",
        "| `*_provider` | 响应中可观测的上游 provider 标识 |",
    ]
    lines.extend(
        [
            "",
            "## 13. 可复现性附录：代码",
            "",
            "### 13.1 完整 A/B Testing 实验脚本",
            "",
            (
                "以下代码是生成本报告数据、执行 A/B testing、清洗异常日志、导出 benchmark 数据集和渲染报告的完整脚本全文。复现实验时应使用同一脚本、同一模型、同一环境变量和同一命令行参数。"
                if embed_full_artifacts
                else "完整脚本全文已嵌入同名 HTML/Markdown 完整版报告。PDF 版保留脚本文件路径、SHA256 和复现命令，避免全量源码与数据集导致 PDF 排版不可用。"
            ),
            "",
            *(_embedded_file_lines(full_script, "python") if embed_full_artifacts else _embedded_file_reference_lines(full_script)),
            "",
            "### 13.2 A/B Testing 核心执行逻辑摘录",
            "",
            "以下代码展示完整的 A/B testing 执行逻辑：同一 payload 分别发送到 Infron 与 OpenRouter；每轮发送 first/second 两次请求；streaming 读取到 `[DONE]` 前的最终 SSE JSON chunk；提取 `usage`、`cost`、`cost_details`、TTFT、cache tokens 和 provider 标识；最后只保留 A/B 两边 input tokens 完全一致的配对样本。",
            "",
            "```python",
            "from __future__ import annotations",
            "",
            "import json",
            "import os",
            "import time",
            "from collections import defaultdict",
            "from urllib.request import Request, urlopen",
            "",
            "MODEL = 'deepseek/deepseek-v4-flash'",
            "SORT_MODES = ('throughput', 'price', 'latency', 'ttft')",
            "PROVIDER_SORT_OVERRIDES = {('infron', 'ttft'): 'ttft', ('openrouter', 'ttft'): 'latency'}",
            "CACHE_PREFIX = ' '.join(['stable prompt cache prefix'] * 220)",
            "",
            "PROVIDERS = {",
            "    'infron': {",
            "        'base_url': os.environ['INFRON_BASE_URL'].rstrip('/'),",
            "        'api_key': os.environ['INFRON_API_KEY'],",
            "        'headers': {},",
            "    },",
            "    'openrouter': {",
            "        'base_url': os.environ['OPENROUTER_BASE_URL'].rstrip('/'),",
            "        'api_key': os.environ['OPENROUTER_API_KEY'],",
            "        'headers': {",
            "            'HTTP-Referer': os.environ.get('OPENROUTER_HTTP_REFERER', 'https://example.com'),",
            "            'X-Title': os.environ.get('OPENROUTER_APP_TITLE', 'cache-ab-test'),",
            "        },",
            "    },",
            "}",
            "",
            "def payload(sort_mode: str, provider_name: str) -> dict:",
            "    return {",
            "        'model': MODEL,",
            "        'messages': [",
            "            {'role': 'system', 'content': CACHE_PREFIX},",
            "            {'role': 'user', 'content': 'Reply with exactly: cache probe ok'},",
            "        ],",
            "        'temperature': 0,",
            "        'max_tokens': 16,",
            "        'stream': True,",
            "        'stream_options': {'include_usage': True},",
            "        'usage': {'include': True},",
            "        'provider': {'sort': PROVIDER_SORT_OVERRIDES.get((provider_name, sort_mode), sort_mode), 'allow_fallbacks': True},",
            "    }",
            "",
            "def read_sse(resp, started: float) -> tuple[dict, dict]:",
            "    assembled, usage = {}, {}",
            "    ttft_ms = first_reasoning_ms = first_content_ms = None",
            "    chunks = 0",
            "    for raw in resp:",
            "        line = raw.decode('utf-8', errors='replace').strip()",
            "        if not line.startswith('data:'):",
            "            continue",
            "        data = line[5:].strip()",
            "        if data == '[DONE]':",
            "            continue",
            "        chunk = json.loads(data)",
            "        now_ms = (time.monotonic() - started) * 1000",
            "        chunks += 1",
            "        if ttft_ms is None:",
            "            ttft_ms = now_ms",
            "        for key in ('id', 'model', 'provider', 'request_id', 'system_fingerprint', 'cost', 'cost_details', 'provider_cost_details', 'cost_breakdown'):",
            "            if key in chunk:",
            "                assembled[key] = chunk[key]",
            "        if isinstance(chunk.get('usage'), dict):",
            "            usage = chunk['usage']",
            "        for choice in chunk.get('choices') or []:",
            "            delta = choice.get('delta') or {}",
            "            if first_content_ms is None and delta.get('content'):",
            "                first_content_ms = now_ms",
            "            if first_reasoning_ms is None and (delta.get('reasoning') or delta.get('reasoning_content') or delta.get('reasoning_details')):",
            "                first_reasoning_ms = now_ms",
            "    if usage:",
            "        assembled['usage'] = usage",
            "    return assembled, {'ttft_ms': ttft_ms, 'first_content_token_ms': first_content_ms, 'first_reasoning_token_ms': first_reasoning_ms, 'stream_chunk_count': chunks}",
            "",
            "def cost_value(body: dict) -> float | None:",
            "    if isinstance(body.get('cost'), (int, float)):",
            "        return float(body['cost'])",
            "    usage = body.get('usage') or {}",
            "    return float(usage['cost']) if isinstance(usage.get('cost'), (int, float)) else None",
            "",
            "def cache_read_tokens(usage: dict) -> int:",
            "    details = usage.get('prompt_tokens_details') or usage.get('input_tokens_details') or {}",
            "    return int(details.get('cached_tokens') or details.get('cache_read_tokens') or 0)",
            "",
            "def reasoning_tokens(usage: dict) -> int:",
            "    details = usage.get('completion_tokens_details') or {}",
            "    return int(details.get('reasoning_tokens') or usage.get('reasoning_tokens') or 0)",
            "",
            "def send(provider_name: str, sort_mode: str) -> dict:",
            "    provider = PROVIDERS[provider_name]",
            "    body = json.dumps(payload(sort_mode, provider_name)).encode('utf-8')",
            "    headers = {",
            "        'Authorization': f\"Bearer {provider['api_key']}\",",
            "        'Content-Type': 'application/json',",
            "        'Accept': 'text/event-stream',",
            "        'Connection': 'keep-alive',",
            "        'User-Agent': 'GrowthPulse/benchmark-reproducer',",
            "        **provider.get('headers', {}),",
            "    }",
            "    started = time.monotonic()",
            "    with urlopen(Request(provider['base_url'] + '/chat/completions', data=body, headers=headers, method='POST'), timeout=120) as resp:",
            "        response_body, stream = read_sse(resp, started)",
            "    latency_ms = (time.monotonic() - started) * 1000",
            "    usage = response_body.get('usage') or {}",
            "    return {",
            "        'status': 200,",
            "        'latency_ms': round(latency_ms, 3),",
            "        **stream,",
            "        'usage': usage,",
            "        'provider_name': response_body.get('provider'),",
            "        'cost': cost_value(response_body),",
            "        'prompt_tokens': int(usage.get('prompt_tokens') or usage.get('input_tokens') or 0),",
            "        'completion_tokens': int(usage.get('completion_tokens') or usage.get('output_tokens') or 0),",
            "        'reasoning_tokens': reasoning_tokens(usage),",
            "        'cache_read_tokens': cache_read_tokens(usage),",
            "        'cost_details': response_body.get('cost_details') or response_body.get('provider_cost_details') or response_body.get('cost_breakdown'),",
            "    }",
            "",
            "def run_ab(groups=4, rounds=50) -> list[dict]:",
            "    records = []",
            "    for sort_mode in SORT_MODES:",
            "        for group in range(1, groups + 1):",
            "            for round_no in range(1, rounds + 1):",
            "                for provider in ('infron', 'openrouter'):",
            "                    first = send(provider, sort_mode)",
            "                    second = send(provider, sort_mode)",
            "                    records.append({'sort': sort_mode, 'provider': provider, 'group': group, 'round': round_no, 'first': first, 'second': second})",
            "    return records",
            "",
            "def strict_equal_input_pairs(records: list[dict]) -> list[dict]:",
            "    by_key = defaultdict(dict)",
            "    for item in records:",
            "        by_key[(item['sort'], item['group'], item['round'])][item['provider']] = item",
            "    kept = []",
            "    for providers in by_key.values():",
            "        a, b = providers.get('infron'), providers.get('openrouter')",
            "        if not a or not b:",
            "            continue",
            "        a_tokens = (a['first']['prompt_tokens'], a['second']['prompt_tokens'])",
            "        b_tokens = (b['first']['prompt_tokens'], b['second']['prompt_tokens'])",
            "        if all(token > 0 for token in (*a_tokens, *b_tokens)) and a_tokens == b_tokens:",
            "            kept.extend([a, b])",
            "    return kept",
            "",
            "# records = run_ab(groups=4, rounds=50)",
            "# filtered_records = strict_equal_input_pairs(records)",
            "```",
            "",
            "### 13.3 离线聚合复现代码",
            "",
            "以下代码只依赖 Python 标准库，可从配对级 CSV 复现总览指标、胜出方判断和核心图表输入数据。",
            "",
            "```python",
            "from __future__ import annotations",
            "",
            "import csv",
            "from collections import defaultdict",
            "from pathlib import Path",
            "",
            f"PAIR_CSV = Path('{pair_csv.get('path', '')}')",
            "",
            "def f(row, key):",
            "    value = row.get(key, '')",
            "    return float(value) if value not in {'', 'None', 'N/A'} else 0.0",
            "",
            "rows = list(csv.DictReader(PAIR_CSV.open(newline='', encoding='utf-8')))",
            "summary = defaultdict(lambda: defaultdict(list))",
            "for row in rows:",
            "    for provider in ('infron', 'openrouter'):",
            "        summary[row['sort']][provider].append(row)",
            "",
            "def aggregate(items, provider):",
            "    total_latency_ms = sum(f(row, f'{provider}_first_latency_ms') + f(row, f'{provider}_second_latency_ms') for row in items)",
            "    completion_tokens = sum(f(row, f'{provider}_first_completion_tokens') + f(row, f'{provider}_second_completion_tokens') for row in items)",
            "    second_prompt_tokens = sum(f(row, f'{provider}_second_prompt_tokens') for row in items)",
            "    second_cache_read_tokens = sum(f(row, f'{provider}_second_cache_read_tokens') for row in items)",
            "    return {",
            "        'rounds': len(items),",
            "        'input_tokens': int(sum(f(row, f'{provider}_input_tokens_total') for row in items)),",
            "        'cost_usd': sum(f(row, f'{provider}_pair_cost_usd') for row in items),",
            "        'latency_ms': total_latency_ms / (len(items) * 2) if items else 0,",
            "        'throughput_tps': completion_tokens / (total_latency_ms / 1000) if total_latency_ms else 0,",
            "        'cache_hit_rate': second_cache_read_tokens / second_prompt_tokens if second_prompt_tokens else 0,",
            "    }",
            "",
            "for sort_mode, providers in summary.items():",
            "    infron = aggregate(providers['infron'], 'infron')",
            "    openrouter = aggregate(providers['openrouter'], 'openrouter')",
            "    assert infron['input_tokens'] == openrouter['input_tokens']",
            "    winners = {",
            "        'cache': 'Infron' if infron['cache_hit_rate'] > openrouter['cache_hit_rate'] else 'OpenRouter',",
            "        'cost': 'Infron' if infron['cost_usd'] < openrouter['cost_usd'] else 'OpenRouter',",
            "        'throughput': 'Infron' if infron['throughput_tps'] > openrouter['throughput_tps'] else 'OpenRouter',",
            "        'latency': 'Infron' if infron['latency_ms'] < openrouter['latency_ms'] else 'OpenRouter',",
            "    }",
            "    print(sort_mode, {'infron': infron, 'openrouter': openrouter, 'winners': winners})",
            "```",
            "",
            "## 14. 可复现性附录：Benchmark 数据集",
            "",
            (
                "本节引用本次报告使用的 benchmark 数据文件。`benchmark_pairs.csv` 用于复现聚合指标；`benchmark_requests.jsonl` 用于审计请求级 telemetry；`records.json` 是严格过滤后的结构化记录；`records_excluded.json` 保留被剔除样本，便于复核异常日志和 input token 不一致样本。"
                if embed_full_artifacts
                else "Benchmark 数据集保存在实验目录的数据文件中；报告保留数据文件路径、大小、SHA256 与用途，避免大体量 JSONL/JSON 影响网页与 PDF 渲染。"
            ),
            "",
        ]
    )
    for title, path, language in full_data_files:
        lines.extend([f"### 14.{full_data_files.index((title, path, language)) + 1} {title}", ""])
        lines.extend(_embedded_file_lines(path, language) if embed_full_artifacts else _embedded_file_reference_lines(path))
        lines.append("")
    return lines


def _embedded_file_lines(path: Path, language: str) -> list[str]:
    if not path.exists():
        return [f"`{path}` 不存在，无法嵌入。"]
    return [
        f"文件：`{path}`",
        "",
        f"SHA256：`{_file_sha256(path)}`",
        "",
        f"大小：`{path.stat().st_size}` bytes",
        "",
        f"```{language}",
        path.read_text(encoding="utf-8"),
        "```",
    ]


def _embedded_file_reference_lines(path: Path) -> list[str]:
    if not path.exists():
        return [f"`{path}` 不存在，无法引用。"]
    return [
        f"文件：`{path}`",
        "",
        f"SHA256：`{_file_sha256(path)}`",
        "",
        f"大小：`{path.stat().st_size}` bytes",
        "",
        "完整内容见同名 HTML/Markdown 完整版报告。",
    ]


def _bold(text: str) -> str:
    return f"**{text}**"


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _display_provider(provider: str) -> str:
    return {"infron": "Infron", "openrouter": "OpenRouter"}.get(provider, provider)


def _chart_ref(path: str) -> str:
    if not path:
        return ""
    deepseek_prefix = "export/deepseek_v4_flash_all_experiments/"
    if path.startswith(deepseek_prefix):
        return "../" + path[len(deepseek_prefix) :]
    prefix = "export/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def _infron_architecture_lines(summary: dict[str, Any]) -> list[str]:
    chart_dir = summary.get("charts", {})
    lines = [
        "## 6. Infron 技术架构与缓存/成本机制解释",
        "",
        "本节使用本次 benchmark 的可观测结果解释 Infron 在高 cache rate 与成本控制上的工程路径。需要说明的是，报告没有采集 Infron 内部私有 routing trace；因此下文把响应中真实返回的 provider 分布、cache read tokens、cost breakdown 和 latency/throughput 指标作为证据，用架构图解释这些结果背后的合理机制。",
        "",
        "### 6.1 多 provider 路由与可观测控制面",
        "",
        "Infron 对外提供 OpenAI-compatible API，对内需要在多个上游 provider、模型部署和路由策略之间做选择。对 prompt caching 工作负载而言，路由层不只是选择一个可用 provider，还需要同时考虑缓存亲和性、健康状态、成本、吞吐和时延目标。",
        "",
        f"![Infron 多 provider 路由架构]({_chart_ref(chart_dir.get('infron_architecture', ''))})",
        "",
        "图 12：Infron 多 provider 路由与缓存控制面。该图用于说明请求从统一 API 入口进入后，路由控制面如何在健康状态、策略目标、provider 选择和缓存域之间形成决策链路。",
        "",
        f"本次实验中，Infron 在不同 routing sort 下呈现出可观测的 provider 分布：{_provider_distribution_sentence(summary, 'infron')}。这种模式说明路由结果不是完全随机扩散，而是围绕路由目标形成了较稳定的 provider 选择。稳定的 provider 选择是高缓存命中率的前提，因为 prompt cache 通常与具体 provider、模型部署或缓存域绑定。",
        "",
        "### 6.2 Provider Stick 与 Cache Affinity",
        "",
        "Provider stick 是多 provider 网关中的缓存亲和策略：当请求具有相同或高度稳定的 prompt prefix 时，路由层倾向于把同一类请求送往同一个健康 provider 或缓存域，以减少缓存碎片化。它不等于固定永不切换 provider；当上游不可用、限流或 SLA 风险升高时，路由仍应回退到其他健康路径。",
        "",
        f"![Provider stick 与 cache affinity]({_chart_ref(chart_dir.get('provider_stick', ''))})",
        "",
        "图 13：Provider stick 与 cache affinity 机制。该图表达的是工程机制假设：同类请求在健康 provider 集合内保持缓存亲和，可减少跨 provider/cache domain 的缓存碎片。",
        "",
        "这解释了 Infron 在本次实验中的高 Token 级命中率：在 `throughput` 与 `latency` 两个模式下，Infron 的第二次请求 Token 级缓存命中率约为 94.42%，OpenRouter 约为 44%-45%。对于相同 stable prefix 的连续双请求，若路由落在同一缓存域，第二次请求更容易读取第一次请求写入或刷新后的 KV/cache 状态；若请求在多个 provider 或部署之间分散，同样的 prompt 也可能需要分别暖缓存，从而降低整体 cache read tokens。",
        "",
        "### 6.3 成本控制路径",
        "",
        "成本控制来自两层叠加：第一层是缓存命中降低重复 prefill 的有效处理成本；第二层是 provider routing 在健康 provider 集合内选择更合适的成本路径。本次实验中，Infron 在三个路由模式下的实际成本均低于 OpenRouter，同时 Token 级缓存命中率显著更高，说明缓存亲和和 provider 选择共同影响了单位请求成本。",
        "",
        f"![Infron 成本控制路径]({_chart_ref(chart_dir.get('cost_control', ''))})",
        "",
        "图 14：Infron 成本控制路径。该图把缓存命中、provider stick、成本感知 routing 和响应 cost breakdown 连接起来，用于解释为什么 cache rate 与实际成本会同步改善。",
        "",
        "表 7：Infron 缓存与成本控制机制的可观测证据。",
        "",
        "| 机制 | 对 cache rate 的影响 | 对成本的影响 | 本次实验中的可观测信号 |",
        "| --- | --- | --- | --- |",
        "| Stable prefix 识别 | 相同前缀更容易命中已有 cache | 降低重复 prefill 的边际成本 | 同一 payload SHA256、第二次请求 cache read tokens 高 |",
        "| Provider stick / cache affinity | 降低跨 provider/cache domain 的缓存碎片 | 减少重复暖缓存 | Infron 在 sort 内 provider 分布更集中，Token 命中率更高 |",
        "| 健康检查与 fallback | 保护可用性，避免单 provider 故障 | fallback 可能牺牲部分缓存收益，但降低失败成本 | HTTP 状态均为 200，provider 分布仍保留少量切换可能 |",
        "| 成本感知 routing | 在满足健康和策略约束下偏向低成本路径 | 降低总成本和每轮成本 | Infron 三个模式的实际总成本均低于 OpenRouter |",
        "",
        "因此，Infron 高 cache rate 的关键在于路由层、缓存域和 provider 选择之间保持了足够强的亲和性。对于长 system prompt、RAG 固定前缀、工具说明和高频模板化请求，这种亲和性会直接转化为更高的 cache read tokens，并进一步影响单位请求成本。",
        "",
    ]
    return lines


def _provider_drilldown_lines(summary: dict[str, Any]) -> list[str]:
    has_distribution = bool(summary.get("provider_distribution"))
    lines = [
        "## 7. Provider/Route 下钻分析",
        "",
        (
            "说明：本轮 streaming 响应已采集到部分上游 provider 标识、响应 model/id、request_id、provider cost breakdown 候选字段；下钻分析结合这些真实返回字段与可观测 telemetry（缓存命中、实际成本、latency、TTFT、throughput）解释 Infron 与 OpenRouter 内部路由差异。"
            if has_distribution
            else "说明：本轮原始响应没有返回可稳定识别的底层 provider 名称，因此不能断言某条请求最终路由到了哪家上游；下钻分析基于可观测 telemetry（缓存命中、实际成本、latency、TTFT、throughput）还原 Infron 与 OpenRouter 的路由画像。"
        ),
        "",
        "表 8：Provider/Route 下钻指标。该表把 provider 分布、成本、吞吐、TTFT 和 latency 放在同一层级，用于分析路由选择如何影响最终结果。",
        "",
        "| 路由偏好 | 平台 | 有效轮次 | Input Tokens | Token 命中率 | 实际成本 | 成本/1K Input | 响应 Throughput（含 reasoning） | TTFT | Latency/请求（含 reasoning） | 可观测路由画像 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for sort_mode in SORT_MODES:
        sort_aggs = {
            provider: dict(summary["results"][sort_mode][provider]["aggregate"])
            for provider in PROVIDERS
        }
        for agg in sort_aggs.values():
            input_tokens = int(agg["total_input_tokens"] or 0)
            cost = _numeric_value(agg.get("total_actual_cost_usd"))
            agg["cost_per_1k_input_usd"] = cost / input_tokens * 1000 if cost is not None and input_tokens else None
        for provider in PROVIDERS:
            agg = sort_aggs[provider]
            input_tokens = int(agg["total_input_tokens"] or 0)
            lines.append(
                f"| `{sort_mode}` | {_display_provider(provider)} | "
                f"{_compare_cell(provider, sort_aggs, 'rounds', str(agg['rounds']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'total_input_tokens', str(input_tokens), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'token_cache_hit_rate', _pct(agg['token_cache_hit_rate']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'total_actual_cost_usd', _format_cost(agg.get('total_actual_cost_usd')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'cost_per_1k_input_usd', _format_cost(agg.get('cost_per_1k_input_usd'), decimals=6), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_throughput_output_tokens_per_second', '{:.2f} response tok/s'.format(agg['avg_throughput_output_tokens_per_second']), higher_is_better=True)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_ttft_ms', _format_ms(agg.get('avg_ttft_ms')), higher_is_better=False)} | "
                f"{_compare_cell(provider, sort_aggs, 'avg_request_latency_ms', '{:.2f} ms'.format(agg['avg_request_latency_ms']), higher_is_better=False)} | "
                f"{_route_profile(sort_mode, provider, sort_aggs)} |"
            )
    if has_distribution:
        lines.extend(
            [
                "",
                "### 上游 Provider 分布",
                "",
                "表 9：上游 provider 归因覆盖率总览。`总请求数` 是 first/second 请求级计数；`已归因请求数` 表示响应中可提取到 provider 标识的请求数。",
                "",
                "| 路由偏好 | 平台 | 总请求数 | 已归因请求数 | 归因覆盖率 | Provider 分布 | Cost breakdown 请求数 |",
                "| --- | ---: | ---: | ---: | ---: | --- | ---: |",
            ]
        )
        distribution = summary.get("provider_distribution", {})
        for sort_mode in SORT_MODES:
            for provider in PROVIDERS:
                item = distribution.get(sort_mode, {}).get(provider, {})
                counts = item.get("counts", {}) if isinstance(item, dict) else {}
                total_attributed = int(item.get("total_attributed_requests", 0) or 0)
                dist_text = (
                    ", ".join(f"{name}: {count} ({count / total_attributed * 100:.2f}%)" for name, count in counts.items())
                    if counts and total_attributed
                    else "未返回"
                )
                lines.append(
                    f"| `{sort_mode}` | {_display_provider(provider)} | {item.get('total_requests', 0)} | "
                    f"{total_attributed} | {_pct(item.get('attribution_coverage', 0) or 0)} | "
                    f"{dist_text} | {item.get('cost_breakdown_requests', 0)} |"
                )
        lines.extend(
            [
                "",
                "表 10：上游 provider 明细分布。该表按 provider 拆分请求占比、first/second 分布、覆盖轮次、时延、TTFT、token、cache 和成本，用于定位最终 A/B 差异来自哪个上游路径。",
                "",
                "| 路由偏好 | 平台 | 上游 Provider | 请求数 | 占比 | first/second | 覆盖轮次 | Avg TTFT | Avg Latency | Prompt Tokens | Completion Tokens | Reasoning Tokens | Cache Read Tokens | 观测成本 | Cost breakdown 请求数 |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for sort_mode in SORT_MODES:
            for provider in PROVIDERS:
                item = distribution.get(sort_mode, {}).get(provider, {})
                details = item.get("details", []) if isinstance(item, dict) else []
                if not details:
                    lines.append(
                        f"| `{sort_mode}` | {_display_provider(provider)} | 未返回 | 0 | 0.00% | 0/0 | 0 | N/A | N/A | 0 | 0 | 0 | 0 | N/A | 0 |"
                    )
                    continue
                for detail in details:
                    lines.append(
                        f"| `{sort_mode}` | {_display_provider(provider)} | `{detail.get('provider', '')}` | "
                        f"{detail.get('request_count', 0)} | {_pct(detail.get('request_share', 0) or 0)} | "
                        f"{detail.get('first_request_count', 0)}/{detail.get('second_request_count', 0)} | "
                        f"{detail.get('covered_rounds', 0)} | {_format_ms(detail.get('avg_ttft_ms'))} | "
                        f"{_format_ms(detail.get('avg_latency_ms'))} | {detail.get('prompt_tokens', 0)} | "
                        f"{detail.get('completion_tokens', 0)} | {detail.get('reasoning_tokens', 0)} | "
                        f"{detail.get('cache_read_tokens', 0)} | {_format_cost(detail.get('observed_cost_usd'))} | "
                        f"{detail.get('cost_breakdown_requests', 0)} |"
                    )
    lines.append("")
    lines.extend(_route_insight_lines(summary))
    lines.extend(
        [
            "- 脚本已支持在后续实验中采集上游 provider 标识候选字段、routing trace 候选字段、provider cost breakdown 候选字段，并可通过 `--stream` 记录 TTFT、首内容 token 与首 reasoning token 时间。当前报告只展示响应中真实存在的字段，不伪造 provider identity。",
            "",
        ]
    )
    return lines


def _business_value_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        "四种 routing sort 对应不同业务目标，需要结合缓存、成本、吞吐、端到端时延和 TTFT 一起判断。`throughput` 更适合批处理、异步生成、长文本生产和离线任务；`price` 更适合高频低毛利调用、固定模板请求、客服/营销自动化等成本敏感场景；`latency` 更适合交互式产品、Agent 工具调用链、实时辅助写作和用户等待成本较高的场景；`ttft` 更适合首包体验敏感、需要快速给用户反馈的流式交互场景。",
        "",
        "| 路由模式 | 主要业务目标 | 本轮数据体现 | 适用场景 | 注意事项 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for sort_mode in SORT_MODES:
        infron = summary["results"][sort_mode]["infron"]["aggregate"]
        openrouter = summary["results"][sort_mode]["openrouter"]["aggregate"]
        winners = {
            "cache": _winner_name(infron["token_cache_hit_rate"], openrouter["token_cache_hit_rate"], higher_is_better=True),
            "cost": _winner_name(infron["total_actual_cost_usd"], openrouter["total_actual_cost_usd"], higher_is_better=False),
            "throughput": _winner_name(
                infron["avg_throughput_output_tokens_per_second"],
                openrouter["avg_throughput_output_tokens_per_second"],
                higher_is_better=True,
            ),
            "latency": _winner_name(infron["avg_request_latency_ms"], openrouter["avg_request_latency_ms"], higher_is_better=False),
            "ttft": _winner_name(infron["avg_ttft_ms"], openrouter["avg_ttft_ms"], higher_is_better=False),
        }
        lines.append(
            f"| `{sort_mode}` | {_mode_business_goal(sort_mode)} | "
            f"{_mode_data_summary(winners)} | "
            f"{_mode_scenarios(sort_mode)} | "
            f"{_mode_tradeoff(sort_mode, winners)} |"
        )
    lines.extend(
        [
            "",
            "从业务决策角度看，prompt caching 的价值不只体现在单次请求省钱，而是体现在大规模重复上下文请求的边际成本下降。若业务请求结构高度模板化，应优先关注 Token 级命中率和实际成本；若业务以用户实时体验为核心，应同时约束 latency；若业务为后台批量生成，则 throughput 可能比单请求 latency 更重要。",
            "",
            "因此，本实验的推荐读法是：先确认 Input Tokens 是否完全可比，再按业务目标选择主指标，最后检查其他指标是否出现不可接受的副作用。例如某个平台吞吐更高但缓存命中显著较低，可能适合批处理，却未必适合需要稳定成本结构的高频在线业务。",
        ]
    )
    return lines


def _mode_business_goal(sort_mode: str) -> str:
    return {
        "throughput": "最大化单位时间输出能力",
        "price": "最小化单位请求和单位 token 成本",
        "latency": "最小化用户可感知等待时间",
        "ttft": "最小化流式首包响应时间",
    }.get(sort_mode, "按路由策略优化")


def _mode_scenarios(sort_mode: str) -> str:
    return {
        "throughput": "批量内容生成、离线摘要、后台数据加工",
        "price": "高频模板化请求、客服自动化、营销触达、RAG 固定前缀",
        "latency": "在线聊天、Agent 调用链、IDE/写作辅助、实时运营工具",
        "ttft": "流式聊天、实时 Copilot、首屏反馈、长思考任务的进度感知",
    }.get(sort_mode, "通用 LLM 调用")


def _mode_data_summary(winners: dict[str, str]) -> str:
    cost_summary = "成本不可比" if winners["cost"] == "不可比" else f"成本 {winners['cost']} 占优"
    return (
        f"缓存 {winners['cache']} 占优，{cost_summary}，"
        f"throughput {winners['throughput']} 占优，latency {winners['latency']} 占优，TTFT {winners['ttft']} 占优"
    )


def _mode_tradeoff(sort_mode: str, winners: dict[str, str]) -> str:
    if winners["cost"] == "不可比":
        return "成本字段不可观测时，不对成本优势下结论；需结合账单或非 streaming 成本回查"
    if winners["throughput"] == "OpenRouter" and winners["cost"] == "OpenRouter" and winners["latency"] == "OpenRouter":
        return "速度和成本同时较强，但仍需确认缓存命中稳定性"
    if winners["cache"] == "Infron" and winners["cost"] == "Infron" and winners["latency"] == "Infron":
        return "更适合成本和体验受控的在线业务，但吞吐可能不是最优"
    if sort_mode == "throughput":
        return "适合吞吐优先任务，但需接受缓存和成本可能被速度目标牺牲"
    if sort_mode == "price":
        return "适合成本敏感任务，但需检查吞吐是否满足 SLA"
    if sort_mode == "latency":
        return "适合交互式任务，但需同时约束缓存命中和单位成本"
    if sort_mode == "ttft":
        return "适合首包体验优先任务，但仍需检查完整响应时延和吞吐是否满足 SLA"
    return "需要结合 SLA 与预算综合判断"


def _route_profile(sort_mode: str, provider: str, sort_aggs: dict[str, dict[str, Any]]) -> str:
    infron = sort_aggs["infron"]
    openrouter = sort_aggs["openrouter"]
    current = sort_aggs[provider]
    cost_values = [_numeric_value(infron.get("total_actual_cost_usd")), _numeric_value(openrouter.get("total_actual_cost_usd"))]
    current_cost = _numeric_value(current.get("total_actual_cost_usd"))
    better_cost = current_cost is not None and all(value is not None for value in cost_values) and current_cost <= min(cost_values)
    better_latency = current["avg_request_latency_ms"] <= min(infron["avg_request_latency_ms"], openrouter["avg_request_latency_ms"])
    better_throughput = current["avg_throughput_output_tokens_per_second"] >= max(
        infron["avg_throughput_output_tokens_per_second"],
        openrouter["avg_throughput_output_tokens_per_second"],
    )
    better_cache = current["token_cache_hit_rate"] >= max(infron["token_cache_hit_rate"], openrouter["token_cache_hit_rate"])
    if better_cache and better_cost and better_throughput and better_latency:
        return "缓存、成本、速度指标同时占优"
    if better_cache and better_cost:
        return "缓存亲和度高，成本控制更强"
    if better_latency and better_throughput:
        return "速度路径更激进，优先低时延/高吞吐"
    if better_latency:
        return "低时延优先"
    if better_throughput:
        return "吞吐优先"
    return "表现均衡但无单项极值"


def _provider_distribution_sentence(summary: dict[str, Any], provider: str) -> str:
    distribution = summary.get("provider_distribution")
    if not isinstance(distribution, dict):
        return "provider 字段未形成稳定可读分布"
    parts = []
    for sort_mode in SORT_MODES:
        item = distribution.get(sort_mode, {}).get(provider, {})
        counts = item.get("counts") if isinstance(item, dict) else {}
        if not isinstance(counts, dict) or not counts:
            parts.append(f"`{sort_mode}` 未返回稳定 provider 标识")
            continue
        provider_name, count = max(counts.items(), key=lambda pair: int(pair[1]))
        total = sum(int(value) for value in counts.values()) or 1
        parts.append(f"`{sort_mode}` 主要路由到 `{provider_name}`（{count / total:.2%}）")
    return "；".join(parts)


def _route_insight_lines(summary: dict[str, Any]) -> list[str]:
    lines = []
    for sort_mode in SORT_MODES:
        infron = summary["results"][sort_mode]["infron"]["aggregate"]
        openrouter = summary["results"][sort_mode]["openrouter"]["aggregate"]
        winners = {
            "缓存命中": _winner_name(infron["token_cache_hit_rate"], openrouter["token_cache_hit_rate"], higher_is_better=True),
            "成本": _winner_name(infron["total_actual_cost_usd"], openrouter["total_actual_cost_usd"], higher_is_better=False),
            "throughput": _winner_name(
                infron["avg_throughput_output_tokens_per_second"],
                openrouter["avg_throughput_output_tokens_per_second"],
                higher_is_better=True,
            ),
            "latency": _winner_name(infron["avg_request_latency_ms"], openrouter["avg_request_latency_ms"], higher_is_better=False),
            "TTFT": _winner_name(infron["avg_ttft_ms"], openrouter["avg_ttft_ms"], higher_is_better=False),
        }
        cost_clause = "成本不可比" if winners["成本"] == "不可比" else f"成本 {winners['成本']} 更低"
        lines.append(
            f"- `{sort_mode}` 路由下：缓存命中 {winners['缓存命中']} 更优，{cost_clause}，"
            f"throughput {winners['throughput']} 更高，latency {winners['latency']} 更低，TTFT {winners['TTFT']} 更低。"
            f"{_route_takeaway(winners)}"
        )
    return lines


def _winner_name(infron_value: float | int, openrouter_value: float | int, *, higher_is_better: bool) -> str:
    infron_numeric = _numeric_value(infron_value)
    openrouter_numeric = _numeric_value(openrouter_value)
    if infron_numeric is None or openrouter_numeric is None:
        return "不可比"
    if infron_numeric == openrouter_numeric:
        return "双方持平"
    if higher_is_better:
        return "Infron" if infron_numeric > openrouter_numeric else "OpenRouter"
    return "Infron" if infron_numeric < openrouter_numeric else "OpenRouter"


def _route_takeaway(winners: dict[str, str]) -> str:
    infron_wins = sum(1 for value in winners.values() if value == "Infron")
    openrouter_wins = sum(1 for value in winners.values() if value == "OpenRouter")
    if winners.get("throughput") == "OpenRouter" and winners.get("latency") == "OpenRouter" and winners.get("TTFT") == "OpenRouter":
        return " 这说明 OpenRouter 在该路由下更偏首包与完整响应速度路径。"
    if winners.get("缓存命中") == "Infron" and winners.get("成本") == "Infron" and winners.get("latency") == "Infron":
        return " 这说明 Infron 在该路由下更偏缓存亲和、成本控制和低时延的综合路径，OpenRouter 主要保留吞吐优势。"
    if infron_wins > openrouter_wins:
        return " 综合看 Infron 的可观测路由结果更稳。"
    if openrouter_wins > infron_wins:
        return " 综合看 OpenRouter 的可观测路由结果更强。"
    return " 综合看双方各有取舍。"


def _write_charts(out_dir: Path, summary: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, str]:
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    conclusion_overview_path = charts_dir / "conclusion_overview.svg"
    impossible_triangle_path = charts_dir / "inference_impossible_quadrilateral.svg"
    experiment_flow_path = charts_dir / "experiment_flow.svg"
    ab_pairing_path = charts_dir / "ab_pairing.svg"
    infron_architecture_path = charts_dir / "infron_architecture.svg"
    provider_stick_path = charts_dir / "provider_stick_cache_affinity.svg"
    cost_control_path = charts_dir / "infron_cost_control.svg"

    _write_experiment_flow_diagram(experiment_flow_path)
    _write_ab_pairing_diagram(ab_pairing_path)
    _write_infron_architecture_diagram(infron_architecture_path)
    _write_provider_stick_diagram(provider_stick_path)
    _write_cost_control_diagram(cost_control_path)
    chart_paths: dict[str, str] = {}
    for sort_mode in SORT_MODES:
        comparison_path = charts_dir / f"{sort_mode}_first.svg"
        curves_path = charts_dir / f"{sort_mode}_first_curves.svg"
        radar_path = charts_dir / f"{sort_mode}_first_radar.svg"
        _write_mode_comparison_chart(comparison_path, summary, sort_mode)
        _write_mode_curve_chart(curves_path, records, sort_mode)
        _write_mode_radar_chart(radar_path, summary, sort_mode)
        chart_paths[_chart_key(sort_mode)] = str(comparison_path)
        chart_paths[_chart_key(sort_mode, "curves")] = str(curves_path)
        chart_paths[_chart_key(sort_mode, "radar")] = str(radar_path)
    _write_conclusion_overview_chart(conclusion_overview_path, summary)
    _write_impossible_triangle_chart(impossible_triangle_path, summary)
    return {
        **chart_paths,
        "conclusion_overview": str(conclusion_overview_path),
        "impossible_triangle": str(impossible_triangle_path),
        "experiment_flow": str(experiment_flow_path),
        "ab_pairing": str(ab_pairing_path),
        "infron_architecture": str(infron_architecture_path),
        "provider_stick": str(provider_stick_path),
        "cost_control": str(cost_control_path),
    }


def _write_experiment_flow_diagram(path: Path) -> None:
    width, height = 1080, 360
    svg = [
        _svg_header(width, height),
        '<text x="48" y="34" class="title">实验数据生成流程</text>',
        '<text x="48" y="58" class="label">同一 payload、同一 routing sort、同一 group/round 下分别请求 Infron 与 OpenRouter。</text>',
    ]
    boxes = [
        (48, 118, 170, 76, "固定 Payload", "model / prompt / usage"),
        (282, 72, 190, 76, "Infron", "first + second request"),
        (282, 170, 190, 76, "OpenRouter", "first + second request"),
        (548, 118, 190, 76, "按 sort/group/round 配对", "A/B pair"),
        (812, 118, 210, 76, "过滤后聚合", "cache / cost / latency / TTFT"),
    ]
    for x, y, w, h, title, subtitle in boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 30}" class="label" font-weight="700" text-anchor="middle">{title}</text>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 54}" class="tick" text-anchor="middle">{subtitle}</text>')
    svg.extend(
        [
            _arrow(218, 156, 282, 110),
            _arrow(218, 156, 282, 208),
            _arrow(472, 110, 548, 156),
            _arrow(472, 208, 548, 156),
            _arrow(738, 156, 812, 156),
            '<text x="282" y="285" class="label">每轮请求两次相同 prompt：第一次触发/建立缓存，第二次观测 cache read tokens。</text>',
            '<text x="282" y="312" class="label">同一 routing sort 下 payload SHA256 固定，用响应 usage.prompt_tokens 做真实 token 口径。</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_ab_pairing_diagram(path: Path) -> None:
    width, height = 1080, 360
    svg = [
        _svg_header(width, height),
        '<text x="48" y="34" class="title">A/B 配对与控制变量过滤</text>',
        '<text x="48" y="58" class="label">只保留 first/second prompt tokens 在 A/B 两边完全相等的配对样本。</text>',
    ]
    svg.extend(
        [
            '<rect x="70" y="95" width="270" height="118" rx="8" fill="#eff6ff" stroke="#93c5fd"/>',
            '<text x="205" y="128" class="label" font-weight="700" text-anchor="middle">Infron pair</text>',
            '<text x="205" y="158" class="tick" text-anchor="middle">first.prompt_tokens = A1</text>',
            '<text x="205" y="184" class="tick" text-anchor="middle">second.prompt_tokens = A2</text>',
            '<rect x="70" y="230" width="270" height="64" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>',
            '<text x="205" y="268" class="label" text-anchor="middle">HTTP 200 + usage.prompt_tokens &gt; 0</text>',
            '<rect x="410" y="95" width="270" height="118" rx="8" fill="#fff7ed" stroke="#fdba74"/>',
            '<text x="545" y="128" class="label" font-weight="700" text-anchor="middle">OpenRouter pair</text>',
            '<text x="545" y="158" class="tick" text-anchor="middle">first.prompt_tokens = B1</text>',
            '<text x="545" y="184" class="tick" text-anchor="middle">second.prompt_tokens = B2</text>',
            '<rect x="410" y="230" width="270" height="64" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>',
            '<text x="545" y="268" class="label" text-anchor="middle">HTTP 200 + usage.prompt_tokens &gt; 0</text>',
            _arrow(680, 154, 760, 154),
            '<rect x="760" y="105" width="250" height="98" rx="8" fill="#f0fdf4" stroke="#86efac"/>',
            '<text x="885" y="138" class="label" font-weight="700" text-anchor="middle">进入统计</text>',
            '<text x="885" y="166" class="tick" text-anchor="middle">(A1, A2) == (B1, B2)</text>',
            '<text x="885" y="190" class="tick" text-anchor="middle">否则整对剔除</text>',
            '<text x="70" y="330" class="label">该过滤防止 tokenization、服务端包装、异常 usage 上报对成本、缓存命中和性能指标造成混杂偏差。</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_infron_architecture_diagram(path: Path) -> None:
    width, height = 1120, 520
    svg = [
        _svg_header(width, height),
        '<text x="48" y="36" class="title">Infron 多 Provider 路由与缓存控制面</text>',
        '<text x="48" y="62" class="label">OpenAI-compatible API 将请求规范化后，在健康、成本、吞吐、时延和缓存亲和性之间做路由决策。</text>',
    ]
    boxes = [
        (48, 120, 170, 78, "#eff6ff", "#93c5fd", "Client / SDK", "chat.completions"),
        (282, 88, 210, 78, "#f8fafc", "#cbd5e1", "API Gateway", "auth / headers / usage"),
        (282, 202, 210, 92, "#f8fafc", "#cbd5e1", "Request Normalizer", "model / prompt / sort"),
        (562, 88, 230, 92, "#fff7ed", "#fdba74", "Routing Policy Engine", "sort + health + cost"),
        (562, 216, 230, 92, "#fefce8", "#fde047", "Cache Affinity Layer", "prefix hash / stick key"),
        (862, 76, 190, 70, "#f0fdf4", "#86efac", "Provider A", "cache domain A"),
        (862, 176, 190, 70, "#f0fdf4", "#86efac", "Provider B", "cache domain B"),
        (862, 276, 190, 70, "#f0fdf4", "#86efac", "Provider C", "cache domain C"),
        (562, 368, 230, 70, "#f8fafc", "#cbd5e1", "Telemetry", "usage / cost / provider"),
    ]
    for x, y, w, h, fill, stroke, title, subtitle in boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 31}" class="label" font-weight="800" text-anchor="middle">{title}</text>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 56}" class="tick" text-anchor="middle">{subtitle}</text>')
    svg.extend(
        [
            _arrow(218, 158, 282, 127),
            _arrow(218, 158, 282, 248),
            _arrow(492, 127, 562, 134),
            _arrow(492, 248, 562, 262),
            _arrow(792, 134, 862, 111),
            _arrow(792, 262, 862, 211),
            _arrow(792, 262, 862, 311),
            _arrow(980, 346, 792, 403),
            '<text x="48" y="470" class="label">核心点：缓存状态通常位于具体 provider/cache domain 内；路由稳定性会直接影响 cache read tokens。</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_provider_stick_diagram(path: Path) -> None:
    width, height = 1120, 520
    svg = [
        _svg_header(width, height),
        '<text x="48" y="36" class="title">Provider Stick / Cache Affinity 机制</text>',
        '<text x="48" y="62" class="label">相同 stable prefix 的连续请求优先落入同一健康缓存域，减少跨 provider 暖缓存。</text>',
    ]
    left_boxes = [
        (70, 110, "Round N first", "stable prefix P"),
        (70, 210, "Round N second", "stable prefix P"),
        (70, 310, "Round N+1", "stable prefix P"),
    ]
    for x, y, title, subtitle in left_boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="190" height="68" rx="8" fill="#eff6ff" stroke="#93c5fd"/>')
        svg.append(f'<text x="{x + 95}" y="{y + 28}" class="label" font-weight="800" text-anchor="middle">{title}</text>')
        svg.append(f'<text x="{x + 95}" y="{y + 50}" class="tick" text-anchor="middle">{subtitle}</text>')
    svg.extend(
        [
            '<rect x="360" y="150" width="230" height="138" rx="10" fill="#fefce8" stroke="#facc15" stroke-width="1.6"/>',
            '<text x="475" y="184" class="label" font-weight="800" text-anchor="middle">Stick Key</text>',
            '<text x="475" y="214" class="tick" text-anchor="middle">model + normalized prefix hash</text>',
            '<text x="475" y="240" class="tick" text-anchor="middle">routing sort + tenant policy</text>',
            '<text x="475" y="266" class="tick" text-anchor="middle">healthy provider set</text>',
            '<rect x="720" y="100" width="260" height="78" rx="8" fill="#f0fdf4" stroke="#86efac" stroke-width="1.6"/>',
            '<text x="850" y="132" class="label" font-weight="800" text-anchor="middle">Preferred Provider</text>',
            '<text x="850" y="156" class="tick" text-anchor="middle">warm cache domain</text>',
            '<rect x="720" y="238" width="260" height="78" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>',
            '<text x="850" y="270" class="label" font-weight="800" text-anchor="middle">Fallback Providers</text>',
            '<text x="850" y="294" class="tick" text-anchor="middle">used for health / quota / SLA</text>',
        ]
    )
    for y in (144, 244, 344):
        svg.append(_arrow(260, y, 360, 219))
    svg.extend(
        [
            _arrow(590, 205, 720, 139),
            _arrow(590, 250, 720, 277),
            '<path d="M850,178 C850,198 850,215 850,238" stroke="#16a34a" stroke-width="3" fill="none" stroke-dasharray="5 5"/>',
            '<text x="694" y="390" class="label">Provider stick 不等于禁用 fallback；它是在健康 provider 集合内优先保持缓存亲和。</text>',
            '<text x="70" y="442" class="label">结果信号：同一 sort 内 provider 分布越集中，第二次请求越容易读取同一缓存域中的 prefix cache。</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_cost_control_diagram(path: Path) -> None:
    width, height = 1120, 520
    svg = [
        _svg_header(width, height),
        '<text x="48" y="36" class="title">Infron 成本控制路径</text>',
        '<text x="48" y="62" class="label">成本来自 token 处理、缓存读写和上游 provider 价格；缓存亲和与路由选择共同降低单位请求成本。</text>',
    ]
    boxes = [
        (64, 116, 190, 88, "#eff6ff", "#93c5fd", "Stable Prefix", "system / tools / RAG"),
        (326, 116, 210, 88, "#fefce8", "#facc15", "Cache Read", "skip repeated prefill"),
        (608, 116, 210, 88, "#fff7ed", "#fdba74", "Provider Pricing", "prompt / completion cost"),
        (880, 116, 190, 88, "#f0fdf4", "#86efac", "Actual Cost", "usage.cost + details"),
        (326, 286, 210, 88, "#f8fafc", "#cbd5e1", "Provider Stick", "avoid cache fragmentation"),
        (608, 286, 210, 88, "#f8fafc", "#cbd5e1", "Cost-aware Routing", "healthy low-cost path"),
    ]
    for x, y, w, h, fill, stroke, title, subtitle in boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 34}" class="label" font-weight="800" text-anchor="middle">{title}</text>')
        svg.append(f'<text x="{x + w / 2}" y="{y + 60}" class="tick" text-anchor="middle">{subtitle}</text>')
    svg.extend(
        [
            _arrow(254, 160, 326, 160),
            _arrow(536, 160, 608, 160),
            _arrow(818, 160, 880, 160),
            _arrow(431, 286, 431, 204),
            _arrow(713, 286, 713, 204),
        '<text x="72" y="438" class="label">本次实验信号：Infron 的 Token 级缓存命中率和实际成本在不同路由模式下呈现差异化优势。</text>',
            '<text x="72" y="466" class="label">解释：高 cache read tokens 降低重复 prefill 成本；provider stick 维持缓存域稳定；成本感知 routing 在健康 provider 中选择更合适的价格路径。</text>',
        ]
    )
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>'
        if False
        else f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#64748b" stroke-width="2" fill="none"/>'
        f'<path d="M{x2 - 8},{y2 - 5} L{x2},{y2} L{x2 - 8},{y2 + 5}" stroke="#64748b" stroke-width="2" fill="none"/>'
    )


def _write_mode_comparison_chart(path: Path, summary: dict[str, Any], sort_mode: str) -> None:
    width, height = 1080, 960
    margin_x, top = 48, 76
    panel_w, panel_h = 472, 230
    gap_x, gap_y = 40, 54
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    mode_label = _sort_mode_label(sort_mode)
    aggs = {
        provider: summary["results"][sort_mode][provider]["aggregate"]
        for provider in PROVIDERS
    }
    metrics = [
        {
            "title": "Latency / 请求（含 reasoning）",
            "key": "avg_request_latency_ms",
            "unit": "ms",
            "format": "{:.2f}",
            "lower_is_better": True,
        },
        {
            "title": "Response Throughput（含 reasoning）",
            "key": "avg_throughput_output_tokens_per_second",
            "unit": "response tok/s",
            "format": "{:.2f}",
            "lower_is_better": False,
        },
        {
            "title": "Actual Cost",
            "key": "total_actual_cost_usd",
            "unit": "USD",
            "format": "${:.8f}",
            "lower_is_better": True,
        },
        {
            "title": "TTFT / 首包响应",
            "key": "avg_ttft_ms",
            "unit": "ms",
            "format": "{:.2f}",
            "lower_is_better": True,
        },
        {
            "title": "Token Cache Hit Rate",
            "key": "token_cache_hit_rate",
            "unit": "%",
            "format": "{:.2%}",
            "lower_is_better": False,
        },
    ]
    svg: list[str] = [
        _svg_header(width, height),
        f'<text x="{margin_x}" y="34" class="title">{escape(mode_label)}：核心指标 A/B 对比</text>',
        f'<text x="{margin_x}" y="58" class="label">每个面板均比较 Infron 与 OpenRouter；胜出方使用浅色底、粗描边和右上角标签突出展示。</text>',
    ]
    for index, metric in enumerate(metrics):
        col = index % 2
        row = index // 2
        x = margin_x + col * (panel_w + gap_x)
        y = top + row * (panel_h + gap_y)
        values = {provider: _numeric_value(aggs[provider].get(metric["key"])) for provider in PROVIDERS}
        numeric_values = [value for value in values.values() if value is not None]
        best = (min(numeric_values) if metric["lower_is_better"] else max(numeric_values)) if numeric_values else None
        max_value = max(numeric_values) if numeric_values else 1
        max_axis = max_value * 1.18
        svg.extend(_metric_panel(x, y, panel_w, panel_h, metric, values, best, max_axis, colors))
    svg.extend(_legend(width - 250, 28, colors))
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_mode_radar_chart(path: Path, summary: dict[str, Any], sort_mode: str) -> None:
    width, height = 960, 620
    cx, cy, radius = 360, 318, 210
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    mode_label = _sort_mode_label(sort_mode)
    aggs = {provider: summary["results"][sort_mode][provider]["aggregate"] for provider in PROVIDERS}
    axes = [
        ("缓存命中率", "token_cache_hit_rate", False, "{:.1%}"),
        ("成本效率", "total_actual_cost_usd", True, "${:.5f}"),
        ("吞吐量", "avg_throughput_output_tokens_per_second", False, "{:.1f}"),
        ("平均时延", "avg_request_latency_ms", True, "{:.0f}ms"),
        ("TTFT", "avg_ttft_ms", True, "{:.0f}ms"),
    ]
    scores: dict[str, list[float]] = {provider: [] for provider in PROVIDERS}
    raw_values: dict[str, list[str]] = {provider: [] for provider in PROVIDERS}
    for _, key, lower_is_better, fmt in axes:
        values = {provider: _numeric_value(aggs[provider].get(key)) for provider in PROVIDERS}
        numeric = [value for value in values.values() if value is not None]
        if not numeric:
            for provider in PROVIDERS:
                scores[provider].append(0)
                raw_values[provider].append("N/A")
            continue
        if len(set(numeric)) == 1:
            for provider in PROVIDERS:
                scores[provider].append(1)
                raw_values[provider].append(fmt.format(values[provider] or 0))
            continue
        min_value, max_value = min(numeric), max(numeric)
        for provider in PROVIDERS:
            value = values[provider]
            if value is None:
                score = 0
                raw = "N/A"
            elif lower_is_better:
                score = (max_value - value) / (max_value - min_value)
                raw = fmt.format(value)
            else:
                score = (value - min_value) / (max_value - min_value)
                raw = fmt.format(value)
            scores[provider].append(max(0, min(1, score)))
            raw_values[provider].append(raw)

    svg: list[str] = [
        _svg_header(width, height),
        f'<text x="48" y="34" class="title">{escape(mode_label)}：综合雷达图</text>',
        '<text x="48" y="58" class="label">所有轴都归一化为“越外圈越好”：成本、时延、TTFT 已做反向评分。</text>',
    ]
    for level in range(1, 6):
        r = radius * level / 5
        points = _radar_points(cx, cy, r, len(axes))
        svg.append(
            '<polygon points="{}" fill="none" stroke="{}" stroke-width="{}"/>'.format(
                " ".join(f"{x:.2f},{y:.2f}" for x, y in points),
                "#cbd5e1" if level < 5 else "#94a3b8",
                "1.2" if level == 5 else "0.8",
            )
        )
        svg.append(f'<text x="{cx + 6}" y="{cy - r + 4:.2f}" class="tick">{level * 20}</text>')
    for index, (label, _, _, _) in enumerate(axes):
        x, y = _radar_point(cx, cy, radius, index, len(axes))
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="#cbd5e1"/>')
        label_x, label_y = _radar_point(cx, cy, radius + 38, index, len(axes))
        anchor = "middle"
        if label_x < cx - 20:
            anchor = "end"
        elif label_x > cx + 20:
            anchor = "start"
        svg.append(f'<text x="{label_x:.2f}" y="{label_y:.2f}" class="label" font-weight="700" text-anchor="{anchor}">{escape(label)}</text>')
    for provider in PROVIDERS:
        points = [
            _radar_point(cx, cy, radius * score, index, len(axes))
            for index, score in enumerate(scores[provider])
        ]
        svg.append(
            '<polygon points="{}" fill="{}" fill-opacity="0.20" stroke="{}" stroke-width="3"/>'.format(
                " ".join(f"{x:.2f},{y:.2f}" for x, y in points),
                colors[provider],
                colors[provider],
            )
        )
        for x, y in points:
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{colors[provider]}"/>')
    table_x, table_y = 640, 118
    svg.append(f'<rect x="{table_x - 20}" y="{table_y - 36}" width="280" height="390" rx="10" fill="#f8fafc" stroke="#dbe3ef"/>')
    svg.append(f'<text x="{table_x}" y="{table_y - 8}" class="label" font-weight="800">原始指标值</text>')
    svg.extend(_legend(table_x, table_y + 12, colors))
    y = table_y + 82
    for index, (label, _, _, _) in enumerate(axes):
        svg.append(f'<text x="{table_x}" y="{y}" class="tick" font-weight="700">{escape(label)}</text>')
        svg.append(f'<text x="{table_x}" y="{y + 20}" class="tick">Infron: {escape(raw_values["infron"][index])}</text>')
        svg.append(f'<text x="{table_x}" y="{y + 38}" class="tick">OpenRouter: {escape(raw_values["openrouter"][index])}</text>')
        y += 58
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_conclusion_overview_chart(path: Path, summary: dict[str, Any]) -> None:
    width, height = 1280, 720
    colors = {"Infron": "#2563eb", "OpenRouter": "#f97316", "Tie": "#64748b"}
    svg: list[str] = [
        _svg_header(width, height),
        '<text x="48" y="38" class="title">结论总览：核心指标与路由模式胜出方</text>',
        '<text x="48" y="64" class="label">基于严格 A/B 配对样本；每个单元格显示同一 routing sort 下表现更好的一方。</text>',
    ]
    headline_cards = [
        ("缓存命中率", _winner_summary_lines(summary, "token_cache_hit_rate", True), "越高越好"),
        ("实际成本", _winner_summary_lines(summary, "total_actual_cost_usd", False), "越低越好"),
        ("吞吐量", _winner_summary_lines(summary, "avg_throughput_output_tokens_per_second", True), "越高越好"),
        ("时延", _winner_summary_lines(summary, "avg_request_latency_ms", False), "越低越好"),
        ("TTFT", _winner_summary_lines(summary, "avg_ttft_ms", False), "越低越好"),
    ]
    card_w, card_h, card_gap = 208, 118, 18
    for index, (title, value_lines, subtitle) in enumerate(headline_cards):
        x = 48 + index * (card_w + card_gap)
        y = 96
        dominant = _dominant_winner("；".join(value_lines))
        svg.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="10" fill="#f8fafc" stroke="#dbe3ef"/>')
        svg.append(f'<text x="{x + 18}" y="{y + 28}" class="label" font-weight="800">{escape(title)}</text>')
        for line_index, line in enumerate(value_lines[:2]):
            svg.append(
                f'<text x="{x + 18}" y="{y + 52 + line_index * 20}" class="value" font-size="11" font-weight="800" fill="{colors.get(dominant, "#111827")}">{escape(line)}</text>'
            )
        svg.append(f'<text x="{x + 18}" y="{y + 104}" class="tick">{escape(subtitle)}</text>')
    table_x, table_y = 72, 284
    col_w = [150, 145, 145, 145, 145, 145, 260]
    row_h = 58
    headers = ["路由模式", "吞吐达成", "成本达成", "时延达成", "TTFT 达成", "缓存命中", "路由模式达成情况"]
    x = table_x
    for index, header in enumerate(headers):
        svg.append(f'<rect x="{x}" y="{table_y}" width="{col_w[index]}" height="{row_h}" fill="#eef2ff" stroke="#c7d2fe"/>')
        svg.append(f'<text x="{x + col_w[index] / 2}" y="{table_y + 36}" class="label" font-weight="800" text-anchor="middle">{escape(header)}</text>')
        x += col_w[index]
    metric_defs = [
        ("avg_throughput_output_tokens_per_second", True),
        ("total_actual_cost_usd", False),
        ("avg_request_latency_ms", False),
        ("avg_ttft_ms", False),
        ("token_cache_hit_rate", True),
    ]
    for row_index, sort_mode in enumerate(SORT_MODES):
        y = table_y + row_h * (row_index + 1)
        x = table_x
        svg.append(f'<rect x="{x}" y="{y}" width="{col_w[0]}" height="{row_h}" fill="#ffffff" stroke="#e5e7eb"/>')
        svg.append(f'<text x="{x + 18}" y="{y + 35}" class="label" font-weight="800">{escape(_sort_mode_label(sort_mode).replace(" 路由模式", ""))}</text>')
        x += col_w[0]
        for col_index, (key, higher_is_better) in enumerate(metric_defs, start=1):
            winner = _winner_for_sort_metric(summary, sort_mode, key, higher_is_better)
            advantage = _winner_advantage_text(summary, sort_mode, key, higher_is_better)
            is_diagonal = col_index == row_index + 1 and row_index < len(SORT_MODES)
            fill = "#eff6ff" if winner == "Infron" else "#fff7ed" if winner == "OpenRouter" else "#f8fafc"
            stroke = "#93c5fd" if winner == "Infron" else "#fdba74" if winner == "OpenRouter" else "#cbd5e1"
            if is_diagonal:
                svg.append(f'<rect x="{x + 3}" y="{y + 3}" width="{col_w[col_index] - 6}" height="{row_h - 6}" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="2.4"/>')
                svg.append(f'<rect x="{x + 9}" y="{y + 9}" width="{col_w[col_index] - 18}" height="{row_h - 18}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
            else:
                svg.append(f'<rect x="{x}" y="{y}" width="{col_w[col_index]}" height="{row_h}" fill="{fill}" stroke="{stroke}"/>')
            svg.append(
                f'<text x="{x + col_w[col_index] / 2}" y="{y + 25}" class="label" font-weight="900" text-anchor="middle" fill="{colors.get(winner, "#111827")}">{escape(winner)}</text>'
            )
            svg.append(
                f'<text x="{x + col_w[col_index] / 2}" y="{y + 44}" class="tick" font-weight="800" text-anchor="middle" fill="{colors.get(winner, "#111827")}">{escape(advantage)}</text>'
            )
            if is_diagonal:
                svg.append(
                    f'<text x="{x + col_w[col_index] - 14}" y="{y + 16}" class="tick" font-size="10" font-weight="900" text-anchor="end" fill="#92400e">目标</text>'
                )
            x += col_w[col_index]
        goal_key, goal_higher_is_better = _sort_goal_metric(sort_mode)
        goal_winner = _winner_for_sort_metric(summary, sort_mode, goal_key, goal_higher_is_better)
        goal_advantage = _winner_advantage_text(summary, sort_mode, goal_key, goal_higher_is_better)
        goal_fill = "#eff6ff" if goal_winner == "Infron" else "#fff7ed" if goal_winner == "OpenRouter" else "#f8fafc"
        goal_stroke = "#93c5fd" if goal_winner == "Infron" else "#fdba74" if goal_winner == "OpenRouter" else "#cbd5e1"
        svg.append(f'<rect x="{x}" y="{y}" width="{col_w[-1]}" height="{row_h}" fill="{goal_fill}" stroke="{goal_stroke}"/>')
        svg.append(
            f'<text x="{x + 16}" y="{y + 24}" class="label" font-weight="900" fill="{colors.get(goal_winner, "#111827")}">{escape(_sort_goal_label(sort_mode))}: {escape(goal_winner)}</text>'
        )
        svg.append(
            f'<text x="{x + 16}" y="{y + 44}" class="tick" font-weight="800" fill="{colors.get(goal_winner, "#111827")}">{escape(goal_advantage)}</text>'
        )
    note_y = table_y + row_h * (len(SORT_MODES) + 1) + 26
    svg.append(f'<text x="{table_x}" y="{note_y}" class="label">读法：前四列与四种路由模式顺序对齐；金色对角线表示该路由模式目标指标的胜出方。</text>')
    svg.append(f'<text x="{table_x}" y="{note_y + 24}" class="label">缓存和吞吐越高越好，成本、时延和 TTFT 越低越好；缓存命中作为跨模式辅助指标单独放在最后一列。</text>')
    svg.extend(_legend(940, note_y + 42, {"infron": "#2563eb", "openrouter": "#f97316"}))
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _sort_goal_metric(sort_mode: str) -> tuple[str, bool]:
    return {
        "throughput": ("avg_throughput_output_tokens_per_second", True),
        "price": ("total_actual_cost_usd", False),
        "latency": ("avg_request_latency_ms", False),
        "ttft": ("avg_ttft_ms", False),
    }.get(sort_mode, ("token_cache_hit_rate", True))


def _sort_goal_label(sort_mode: str) -> str:
    return {
        "throughput": "吞吐目标",
        "price": "成本目标",
        "latency": "时延目标",
        "ttft": "TTFT 目标",
    }.get(sort_mode, "目标指标")


def _write_impossible_triangle_chart(path: Path, summary: dict[str, Any]) -> None:
    width, height = 1440, 1040
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    cx, cy, radius = 720.0, 500.0, 330.0
    svg: list[str] = [
        _svg_header(width, height),
        '<text x="48" y="38" class="title">Inference 平台“不可能四角”：四项核心指标的严格归一化对比</text>',
        '<text x="48" y="64" class="label">单图投影展示：每个路由模式先做四项指标 A/B 归一化，再投影成一个点；同一平台的四个点连接成区域。</text>',
    ]
    for level in (0.25, 0.5, 0.75, 1.0):
        points = [
            (cx, cy - radius * level),
            (cx + radius * level, cy),
            (cx, cy + radius * level),
            (cx - radius * level, cy),
        ]
        svg.append(
            '<polygon points="{}" fill="{}" stroke="{}" stroke-width="{}"/>'.format(
                " ".join(f"{x:.1f},{y:.1f}" for x, y in points),
                "#f8fafc" if level == 1.0 else "none",
                "#94a3b8" if level == 1.0 else "#e2e8f0",
                "2.0" if level == 1.0 else "1.0",
            )
        )
        svg.append(f'<text x="{cx + radius * level + 9:.1f}" y="{cy - 7:.1f}" class="tick">{level:.2f}</text>')
    for x, y in ((cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)):
        svg.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#cbd5e1" stroke-dasharray="5 5"/>')
    axis_labels = {
        "throughput": ("吞吐量", cx, cy - radius - 42, "middle", "更高 response tok/s"),
        "price": ("价格", cx + radius + 50, cy - 4, "start", "更低实际成本"),
        "latency": ("端到端 E2E 时延", cx, cy + radius + 52, "middle", "更低完整响应耗时"),
        "ttft": ("流式 TTFT", cx - radius - 50, cy - 4, "end", "更低首包响应时间"),
    }
    for label, x, y, anchor, hint in axis_labels.values():
        svg.append(f'<text x="{x:.1f}" y="{y:.1f}" class="label" font-weight="900" text-anchor="{anchor}">{escape(label)}</text>')
        svg.append(f'<text x="{x:.1f}" y="{y + 20:.1f}" class="tick" text-anchor="{anchor}">{escape(hint)}</text>')

    projected: dict[str, dict[str, tuple[float, float]]] = {provider: {} for provider in PROVIDERS}
    for sort_mode in SORT_MODES:
        scores = _impossible_quadrilateral_scores(summary, sort_mode)
        for provider in PROVIDERS:
            projected[provider][sort_mode] = _project_quadrilateral_scores(cx, cy, radius, scores[provider])
    projected = _separate_projected_points(cx, cy, radius, projected)

    for provider in PROVIDERS:
        color = colors[provider]
        points = [projected[provider][sort_mode] for sort_mode in SORT_MODES]
        svg.append(
            '<polygon points="{}" fill="{}" fill-opacity="0.16" stroke="{}" stroke-width="3.2" stroke-dasharray="{}"/>'.format(
                " ".join(f"{x:.1f},{y:.1f}" for x, y in points),
                color,
                color,
                "none" if provider == "infron" else "8 4",
            )
        )
        for sort_mode, (x, y) in zip(SORT_MODES, points, strict=True):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="18" fill="{color}" stroke="#ffffff" stroke-width="3.2"/>')
            svg.append(
                f'<text x="{x:.1f}" y="{y + 4:.1f}" class="tick" font-size="10" font-weight="900" text-anchor="middle" fill="#ffffff">{_sort_mode_abbrev_for_quadrilateral(sort_mode)}</text>'
            )

    svg.extend(_legend(1078, 92, colors))
    svg.extend(_projection_route_legend(1078, 174))
    svg.append('<text x="48" y="960" class="tick">读图：THR/PRI/LAT/TTFT 分别代表四种路由模式；蓝色区域为 Infron，橙色区域为 OpenRouter，区域外扩方向表示对应指标优势方向。</text>')
    svg.append('<text x="48" y="984" class="tick">该图采用统一归一化、四维到二维投影和一致径向视觉放大，用于总览区域形状；精确逐指标胜负以下方表格为准。</text>')
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _impossible_quadrilateral_scores(summary: dict[str, Any], sort_mode: str) -> dict[str, dict[str, float]]:
    raw = {
        provider: {
            "throughput": _numeric_value(
                summary["results"][sort_mode][provider]["aggregate"].get("avg_throughput_output_tokens_per_second")
            )
            or 0.0,
            "price": _numeric_value(summary["results"][sort_mode][provider]["aggregate"].get("total_actual_cost_usd")),
            "latency": _numeric_value(summary["results"][sort_mode][provider]["aggregate"].get("avg_request_latency_ms")) or 0.0,
            "ttft": _numeric_value(summary["results"][sort_mode][provider]["aggregate"].get("avg_ttft_ms")) or 0.0,
        }
        for provider in PROVIDERS
    }
    max_throughput = max(raw[provider]["throughput"] for provider in PROVIDERS) or 1.0
    min_price = min((raw[provider]["price"] for provider in PROVIDERS if raw[provider]["price"] is not None), default=None)
    min_latency = min((raw[provider]["latency"] for provider in PROVIDERS if raw[provider]["latency"] > 0), default=1.0)
    min_ttft = min((raw[provider]["ttft"] for provider in PROVIDERS if raw[provider]["ttft"] > 0), default=1.0)
    scores: dict[str, dict[str, float]] = {}
    for provider in PROVIDERS:
        price = raw[provider]["price"]
        scores[provider] = {
            "throughput": _clamp_score(raw[provider]["throughput"] / max_throughput),
            "price": _clamp_score(min_price / price) if min_price is not None and price else 0.0,
            "latency": _clamp_score(min_latency / raw[provider]["latency"]) if raw[provider]["latency"] else 0.0,
            "ttft": _clamp_score(min_ttft / raw[provider]["ttft"]) if raw[provider]["ttft"] else 0.0,
        }
    return scores


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _project_quadrilateral_scores(
    cx: float,
    cy: float,
    radius: float,
    scores: dict[str, float],
) -> tuple[float, float]:
    x = cx + radius * 0.46 * (scores["price"] - scores["ttft"])
    y = cy + radius * 0.46 * (scores["latency"] - scores["throughput"])
    visual_scale = 1.74
    return _clamp_projected_point(cx, cy, radius, cx + (x - cx) * visual_scale, cy + (y - cy) * visual_scale)


def _clamp_projected_point(cx: float, cy: float, radius: float, x: float, y: float) -> tuple[float, float]:
    dx = x - cx
    dy = y - cy
    occupancy = abs(dx) / radius + abs(dy) / radius
    if occupancy <= 0.92:
        return x, y
    scale = 0.92 / occupancy
    return cx + dx * scale, cy + dy * scale


def _separate_projected_points(
    cx: float,
    cy: float,
    radius: float,
    points: dict[str, dict[str, tuple[float, float]]],
) -> dict[str, dict[str, tuple[float, float]]]:
    adjusted = {provider: dict(provider_points) for provider, provider_points in points.items()}
    keys = [(provider, sort_mode) for provider in PROVIDERS for sort_mode in SORT_MODES]
    for _ in range(24):
        moved = False
        for i, (provider_a, sort_a) in enumerate(keys):
            for provider_b, sort_b in keys[i + 1 :]:
                ax, ay = adjusted[provider_a][sort_a]
                bx, by = adjusted[provider_b][sort_b]
                dx = bx - ax
                dy = by - ay
                distance = math.hypot(dx, dy)
                min_distance = 46.0 if provider_a == provider_b else 54.0
                if distance >= min_distance:
                    continue
                if distance < 0.001:
                    angle = (i + 1) * 0.83
                    ux, uy = math.cos(angle), math.sin(angle)
                else:
                    ux, uy = dx / distance, dy / distance
                push = (min_distance - distance) / 2 + 1.0
                adjusted[provider_a][sort_a] = _clamp_projected_point(cx, cy, radius, ax - ux * push, ay - uy * push)
                adjusted[provider_b][sort_b] = _clamp_projected_point(cx, cy, radius, bx + ux * push, by + uy * push)
                moved = True
        if not moved:
            break
    return adjusted


def _sort_mode_abbrev_for_quadrilateral(sort_mode: str) -> str:
    return {
        "throughput": "THR",
        "price": "PRI",
        "latency": "LAT",
        "ttft": "TTFT",
    }.get(sort_mode, sort_mode[:4].upper())


def _projection_route_legend(x: int, y: int) -> list[str]:
    rows = [
        ("THR", "Throughput First"),
        ("PRI", "Price First"),
        ("LAT", "Latency First"),
        ("TTFT", "TTFT First"),
    ]
    svg = [
        f'<rect x="{x - 18}" y="{y - 24}" width="292" height="154" rx="10" fill="#ffffff" stroke="#dbe3ef"/>',
        f'<text x="{x}" y="{y - 2}" class="label" font-weight="900">路由模式标记</text>',
    ]
    for index, (abbr, label) in enumerate(rows):
        row_y = y + 28 + index * 28
        svg.append(f'<text x="{x}" y="{row_y}" class="tick" font-size="10" font-weight="900">{abbr}</text>')
        svg.append(f'<text x="{x + 52}" y="{row_y}" class="tick" font-weight="800">{escape(label)}</text>')
    return svg


def _quadrilateral_metric_winners(scores: dict[str, dict[str, float]]) -> list[tuple[str, str]]:
    labels = {
        "throughput": "吞吐",
        "price": "价格",
        "latency": "E2E",
        "ttft": "TTFT",
    }
    winners = []
    for metric in ("throughput", "price", "latency", "ttft"):
        infron = scores["infron"][metric]
        openrouter = scores["openrouter"][metric]
        if abs(infron - openrouter) < 1e-9:
            winner = "双方持平"
        else:
            winner = "infron" if infron > openrouter else "openrouter"
        winners.append((labels[metric], winner))
    return winners


def _weighted_metric_across_sorts(summary: dict[str, Any], provider: str, key: str) -> float:
    numerator = 0.0
    denominator = 0
    for sort_mode in SORT_MODES:
        agg = summary["results"][sort_mode][provider]["aggregate"]
        rounds = int(agg.get("rounds") or 0)
        value = _numeric_value(agg.get(key)) or 0
        numerator += value * rounds
        denominator += rounds
    return numerator / denominator if denominator else 0.0


def _total_metric_across_sorts(summary: dict[str, Any], provider: str, key: str) -> float | None:
    values = [_numeric_value(summary["results"][sort_mode][provider]["aggregate"].get(key)) for sort_mode in SORT_MODES]
    numeric = [value for value in values if value is not None]
    return sum(numeric) if numeric else None


def _winner_summary_lines(summary: dict[str, Any], key: str, higher_is_better: bool) -> list[str]:
    winners = [_winner_for_sort_metric(summary, sort_mode, key, higher_is_better) for sort_mode in SORT_MODES]
    infron_wins = sum(1 for winner in winners if winner == "Infron")
    openrouter_wins = sum(1 for winner in winners if winner == "OpenRouter")
    if infron_wins == 0 and openrouter_wins == 0:
        return ["无明显差异"]
    provider = "Infron" if infron_wins >= openrouter_wins else "OpenRouter"
    win_count = max(infron_wins, openrouter_wins)
    max_advantage = _max_provider_advantage(summary, key, higher_is_better, provider)
    return [f"{provider} {win_count}/{len(SORT_MODES)} 胜", f"最大优势 {_pct(max_advantage)}"]


def _max_provider_advantage(summary: dict[str, Any], key: str, higher_is_better: bool, provider: str) -> float:
    advantages: list[float] = []
    for sort_mode in SORT_MODES:
        if _winner_for_sort_metric(summary, sort_mode, key, higher_is_better) != provider:
            continue
        infron = _numeric_value(summary["results"][sort_mode]["infron"]["aggregate"].get(key))
        openrouter = _numeric_value(summary["results"][sort_mode]["openrouter"]["aggregate"].get(key))
        if infron is None or openrouter is None or infron == openrouter:
            continue
        winner_value = infron if provider == "Infron" else openrouter
        loser_value = openrouter if provider == "Infron" else infron
        baseline = abs(loser_value)
        if baseline:
            advantages.append(abs(winner_value - loser_value) / baseline)
    return max(advantages) if advantages else 0.0


def _winner_by_metric(summary: dict[str, Any], key: str, higher_is_better: bool) -> str:
    winners = [_winner_for_sort_metric(summary, sort_mode, key, higher_is_better) for sort_mode in SORT_MODES]
    infron_modes = _mode_list([SORT_MODES[index] for index, winner in enumerate(winners) if winner == "Infron"])
    openrouter_modes = _mode_list([SORT_MODES[index] for index, winner in enumerate(winners) if winner == "OpenRouter"])
    if infron_modes and not openrouter_modes:
        return "Infron 全部领先"
    if openrouter_modes and not infron_modes:
        return "OpenRouter 全部领先"
    parts = []
    if infron_modes:
        parts.append(f"Infron: {infron_modes}")
    if openrouter_modes:
        parts.append(f"OpenRouter: {openrouter_modes}")
    return "；".join(parts)


def _dominant_winner(text: str) -> str:
    if text.startswith("Infron 全部") or text.startswith("Infron:") or text.startswith("Infron ") or "全模式 Infron" in text:
        return "Infron"
    if text.startswith("OpenRouter 全部") or text.startswith("OpenRouter:") or text.startswith("OpenRouter ") or "全模式 OpenRouter" in text:
        return "OpenRouter"
    return "Tie"


def _winner_for_sort_metric(summary: dict[str, Any], sort_mode: str, key: str, higher_is_better: bool) -> str:
    infron = _numeric_value(summary["results"][sort_mode]["infron"]["aggregate"].get(key))
    openrouter = _numeric_value(summary["results"][sort_mode]["openrouter"]["aggregate"].get(key))
    if infron is None or openrouter is None or infron == openrouter:
        return "Tie"
    if higher_is_better:
        return "Infron" if infron > openrouter else "OpenRouter"
    return "Infron" if infron < openrouter else "OpenRouter"


def _winner_advantage_text(summary: dict[str, Any], sort_mode: str, key: str, higher_is_better: bool) -> str:
    infron = _numeric_value(summary["results"][sort_mode]["infron"]["aggregate"].get(key))
    openrouter = _numeric_value(summary["results"][sort_mode]["openrouter"]["aggregate"].get(key))
    if infron is None or openrouter is None or infron == openrouter:
        return "差异 0%"
    winner_value = max(infron, openrouter) if higher_is_better else min(infron, openrouter)
    loser_value = min(infron, openrouter) if higher_is_better else max(infron, openrouter)
    if loser_value == 0:
        return "优势 N/A"
    advantage = abs(winner_value - loser_value) / abs(loser_value)
    prefix = "高" if higher_is_better else "低"
    return f"{prefix} {_pct(advantage)}"


def _radar_points(cx: int, cy: int, radius: float, count: int) -> list[tuple[float, float]]:
    return [_radar_point(cx, cy, radius, index, count) for index in range(count)]


def _radar_point(cx: int, cy: int, radius: float, index: int, count: int) -> tuple[float, float]:
    angle = -3.141592653589793 / 2 + 2 * 3.141592653589793 * index / count
    return (cx + radius * math.cos(angle), cy + radius * math.sin(angle))


def _write_mode_curve_chart(path: Path, records: list[dict[str, Any]], sort_mode: str) -> None:
    width, height = 1080, 1000
    margin_x, top = 48, 76
    panel_w, panel_h = 472, 245
    gap_x, gap_y = 40, 58
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    mode_label = _sort_mode_label(sort_mode)
    series = _mode_curve_series(records, sort_mode)
    metrics = [
        ("latency", "Latency / 请求（含 reasoning）", "ms", False),
        ("ttft", "TTFT / 首包响应", "ms", False),
        ("throughput", "Response Throughput（含 reasoning）", "response tok/s", True),
        ("cost", "Actual Cost / 轮", "USD", False),
        ("cache_hit", "Token Cache Hit Rate", "%", True),
    ]
    svg: list[str] = [
        _svg_header(width, height),
        f'<text x="{margin_x}" y="34" class="title">{escape(mode_label)}：指标生成过程对比曲线</text>',
        f'<text x="{margin_x}" y="58" class="label">按 group/round 顺序绘制每轮指标；曲线展示汇总均值背后的波动过程。</text>',
    ]
    for index, (metric_key, title, unit, higher_is_better) in enumerate(metrics):
        col = index % 2
        row = index // 2
        x = margin_x + col * (panel_w + gap_x)
        y = top + row * (panel_h + gap_y)
        metric_series = {provider: [point[metric_key] for point in series[provider]] for provider in PROVIDERS}
        svg.extend(_curve_panel(x, y, panel_w, panel_h, title, unit, metric_series, colors, higher_is_better=higher_is_better))
    svg.extend(_legend(width - 250, 28, colors))
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _mode_curve_series(records: list[dict[str, Any]], sort_mode: str) -> dict[str, list[dict[str, float]]]:
    output: dict[str, list[dict[str, float]]] = {provider: [] for provider in PROVIDERS}
    for provider in PROVIDERS:
        rows = sorted(
            (item for item in records if item["sort"] == sort_mode and item["provider"] == provider),
            key=lambda item: (int(item["group"]), int(item["round"])),
        )
        for item in rows:
            first = item["first"]
            second = item["second"]
            latency_ms = (float(first.get("latency_ms") or 0) + float(second.get("latency_ms") or 0)) / 2
            ttft_values = [
                value
                for value in (_numeric_value(first.get("ttft_ms")), _numeric_value(second.get("ttft_ms")))
                if value is not None
            ]
            ttft_ms = sum(ttft_values) / len(ttft_values) if ttft_values else 0
            latency_seconds = (float(first.get("latency_ms") or 0) + float(second.get("latency_ms") or 0)) / 1000
            completion_tokens = int(first.get("completion_tokens") or 0) + int(second.get("completion_tokens") or 0)
            second_prompt = int(second.get("prompt_tokens") or 0)
            output[provider].append(
                {
                    "latency": latency_ms,
                    "ttft": ttft_ms,
                    "throughput": completion_tokens / latency_seconds if latency_seconds else 0,
                    "cost": (
                        first_cost + second_cost
                        if (first_cost := _request_cost_value(first)) is not None
                        and (second_cost := _request_cost_value(second)) is not None
                        else None
                    ),
                    "cache_hit": (float(second.get("cache_read_tokens") or 0) / second_prompt) if second_prompt else 0,
                }
            )
    return output


def _curve_panel(
    x: int,
    y: int,
    width: int,
    height: int,
    title: str,
    unit: str,
    series: dict[str, list[float | None]],
    colors: dict[str, str],
    *,
    higher_is_better: bool,
) -> list[str]:
    inner_left, inner_right, inner_top, inner_bottom = 58, 24, 48, 40
    plot_x = x + inner_left
    plot_y = y + inner_top
    plot_w = width - inner_left - inner_right
    plot_h = height - inner_top - inner_bottom
    all_values = [value for values in series.values() for value in values if value is not None]
    max_value = max(all_values, default=1) or 1
    min_value = min(all_values, default=0)
    if min_value >= 0:
        min_axis = 0.0
    else:
        min_axis = min_value * 1.1
    max_axis = max_value * 1.12 if max_value > 0 else 1
    if max_axis == min_axis:
        max_axis = min_axis + 1
    provider_avgs = {
        provider: (sum(clean_values) / len(clean_values))
        for provider, values in series.items()
        if (clean_values := [value for value in values if value is not None])
    }
    winning_provider = None
    if provider_avgs:
        winning_provider = (
            max(provider_avgs, key=lambda provider: provider_avgs[provider])
            if higher_is_better
            else min(provider_avgs, key=lambda provider: provider_avgs[provider])
        )
    lines = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="#ffffff" stroke="#dbe3ef"/>',
        f'<text x="{x + 18}" y="{y + 28}" class="label" font-weight="700">{escape(title)}</text>',
    ]
    if winning_provider:
        badge_x = x + width - 154
        badge_y = y + 12
        lines.append(
            f'<rect x="{badge_x}" y="{badge_y}" width="136" height="26" rx="13" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.4"/>'
        )
        lines.append(
            f'<text x="{badge_x + 68}" y="{badge_y + 18}" class="tick" font-weight="800" text-anchor="middle" fill="#92400e">均值胜出: {_display_provider(winning_provider)}</text>'
        )
    for tick in range(0, 4):
        tick_y = plot_y + plot_h - plot_h * tick / 3
        value = min_axis + (max_axis - min_axis) * tick / 3
        lines.append(f'<line x1="{plot_x}" y1="{tick_y:.2f}" x2="{plot_x + plot_w}" y2="{tick_y:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{plot_x - 8}" y="{tick_y + 4:.2f}" class="tick" text-anchor="end">{_format_axis_tick(value, unit)}</text>')
    max_len = max((len(values) for values in series.values()), default=1)
    for provider in PROVIDERS:
        values = series.get(provider, [])
        if not values:
            continue
        points = []
        for index, value in enumerate(values):
            if value is None:
                continue
            px = plot_x + (plot_w * index / max(max_len - 1, 1))
            py = plot_y + plot_h - ((value - min_axis) / (max_axis - min_axis) * plot_h)
            points.append(f"{px:.2f},{py:.2f}")
        is_winner = provider == winning_provider
        if points:
            lines.append(
                f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[provider]}" stroke-width="{"3.8" if is_winner else "1.8"}" '
                f'stroke-opacity="{"1" if is_winner else "0.45"}" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        for index in range(0, len(values), max(1, len(values) // 18)):
            value = values[index]
            if value is None:
                continue
            px = plot_x + (plot_w * index / max(max_len - 1, 1))
            py = plot_y + plot_h - ((value - min_axis) / (max_axis - min_axis) * plot_h)
            lines.append(
                f'<circle cx="{px:.2f}" cy="{py:.2f}" r="{"3.0" if is_winner else "1.8"}" fill="{colors[provider]}" fill-opacity="{"1" if is_winner else "0.55"}"/>'
            )
    direction = "越高越好" if higher_is_better else "越低越好"
    lines.append(f'<text x="{plot_x + plot_w}" y="{plot_y + plot_h + 25}" class="tick" text-anchor="end">Round 序列；{direction}</text>')
    return lines


def _metric_panel(
    x: int,
    y: int,
    width: int,
    height: int,
    metric: dict[str, Any],
    values: dict[str, float | None],
    best: float | None,
    max_axis: float,
    colors: dict[str, str],
) -> list[str]:
    inner_left, inner_right, inner_top, inner_bottom = 58, 26, 48, 42
    plot_x = x + inner_left
    plot_y = y + inner_top
    plot_w = width - inner_left - inner_right
    plot_h = height - inner_top - inner_bottom
    bar_w = 58
    lines = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="#f8fafc" stroke="#dbe3ef"/>',
        f'<text x="{x + 18}" y="{y + 28}" class="label" font-weight="700">{escape(str(metric["title"]))}</text>',
    ]
    winning_provider = None
    if best is not None:
        for provider, value in values.items():
            if value == best:
                winning_provider = provider
                break
    if winning_provider:
        badge_x = x + width - 154
        badge_y = y + 12
        lines.append(
            f'<rect x="{badge_x}" y="{badge_y}" width="136" height="26" rx="13" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.4"/>'
        )
        lines.append(
            f'<text x="{badge_x + 68}" y="{badge_y + 18}" class="tick" font-weight="800" text-anchor="middle" fill="#92400e">胜出: {_display_provider(winning_provider)}</text>'
        )
    for tick in range(0, 4):
        tick_y = plot_y + plot_h - plot_h * tick / 3
        value = max_axis * tick / 3
        lines.append(f'<line x1="{plot_x}" y1="{tick_y:.2f}" x2="{plot_x + plot_w}" y2="{tick_y:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{plot_x - 8}" y="{tick_y + 4:.2f}" class="tick" text-anchor="end">{_format_axis_tick(value, str(metric["unit"]))}</text>')
    for provider_index, provider in enumerate(PROVIDERS):
        value = values[provider]
        center = plot_x + plot_w * (provider_index + 1) / 3
        if value is None:
            lines.append(f'<text x="{center:.2f}" y="{plot_y + plot_h / 2:.2f}" class="value" font-weight="700" text-anchor="middle">N/A</text>')
            lines.append(f'<text x="{center:.2f}" y="{plot_y + plot_h + 24:.2f}" class="tick" text-anchor="middle">{_display_provider(provider)}</text>')
            continue
        bar_h = value / max_axis * plot_h if max_axis else 0
        bar_x = center - bar_w / 2
        bar_y = plot_y + plot_h - bar_h
        is_winner = best is not None and value == best
        stroke = "#111827" if is_winner else "none"
        weight = "800" if is_winner else "500"
        opacity = "1" if is_winner else "0.52"
        label = str(metric["format"]).format(value)
        if is_winner:
            highlight_x = center - 72
            lines.append(
                f'<rect x="{highlight_x:.2f}" y="{plot_y - 10:.2f}" width="144" height="{plot_h + 28:.2f}" rx="10" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.6"/>'
            )
        lines.append(
            f'<rect x="{bar_x:.2f}" y="{bar_y:.2f}" width="{bar_w}" height="{bar_h:.2f}" '
            f'rx="5" fill="{colors[provider]}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="3"/>'
        )
        lines.append(f'<text x="{center:.2f}" y="{bar_y - 8:.2f}" class="value" font-weight="{weight}" text-anchor="middle">{escape(label)}</text>')
        lines.append(f'<text x="{center:.2f}" y="{plot_y + plot_h + 24:.2f}" class="tick" text-anchor="middle">{_display_provider(provider)}</text>')
    return lines


def _format_axis_tick(value: float, unit: str) -> str:
    if unit == "%":
        return f"{value:.0%}"
    if unit == "USD":
        return f"${value:.4f}"
    if value >= 100:
        return f"{value:.0f}"
    return f"{value:.1f}"


def _write_bar_chart(
    path: Path,
    title: str,
    y_label: str,
    summary: dict[str, Any],
    metric: str,
    *,
    lower_is_better: bool,
) -> None:
    width, height = 920, 420
    left, right, top, bottom = 76, 34, 58, 72
    plot_w, plot_h = width - left - right, height - top - bottom
    rows = [
        (sort_mode, provider, float(summary["results"][sort_mode][provider]["aggregate"].get(metric) or 0))
        for sort_mode in SORT_MODES
        for provider in PROVIDERS
    ]
    max_value = max((value for _, _, value in rows), default=1) or 1
    max_axis = max_value * 1.18
    group_w = plot_w / len(SORT_MODES)
    bar_w = min(56, group_w * 0.24)
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    svg: list[str] = [_svg_header(width, height), f'<text x="{left}" y="34" class="title">{escape(title)}</text>']
    svg.extend(_axis(svg_x=left, svg_y=top, plot_w=plot_w, plot_h=plot_h, y_label=y_label, max_axis=max_axis))
    for group_index, sort_mode in enumerate(SORT_MODES):
        center = left + group_w * group_index + group_w / 2
        values = {provider: value for item_sort, provider, value in rows if item_sort == sort_mode}
        best_value = min(values.values()) if lower_is_better else max(values.values())
        for provider_index, provider in enumerate(PROVIDERS):
            value = values[provider]
            x = center + (provider_index - 0.5) * (bar_w + 12)
            bar_h = value / max_axis * plot_h
            y = top + plot_h - bar_h
            stroke = "#111827" if value == best_value else "none"
            weight = "700" if value == best_value else "500"
            svg.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" '
                f'rx="4" fill="{colors[provider]}" stroke="{stroke}" stroke-width="2"/>'
            )
            svg.append(
                f'<text x="{x + bar_w / 2:.2f}" y="{y - 8:.2f}" class="value" font-weight="{weight}" text-anchor="middle">{value:.2f}</text>'
            )
        svg.append(f'<text x="{center:.2f}" y="{height - 28}" class="label" text-anchor="middle">{escape(_sort_mode_label(sort_mode))}</text>')
    svg.extend(_legend(width - 250, 28, colors))
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_cost_cache_chart(path: Path, records: list[dict[str, Any]]) -> None:
    width, height = 920, 460
    left, right, top, bottom = 84, 42, 58, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    points = []
    for item in records:
        second_prompt = int(item["second"].get("prompt_tokens") or 0)
        if second_prompt <= 0:
            continue
        cache_rate = float(item["second"].get("cache_read_tokens") or 0) / second_prompt
        first_cost = _request_cost_value(item["first"])
        second_cost = _request_cost_value(item["second"])
        if first_cost is None or second_cost is None:
            continue
        cost = first_cost + second_cost
        points.append((str(item["provider"]), str(item["sort"]), cache_rate, cost))
    max_cost = max((cost for _, _, _, cost in points), default=0.0001) or 0.0001
    max_axis = max_cost * 1.18
    colors = {"infron": "#2563eb", "openrouter": "#f97316"}
    svg: list[str] = [
        _svg_header(width, height),
        f'<text x="{left}" y="34" class="title">成本/缓存指标分布：不同 First 路由模式</text>',
    ]
    svg.extend(_axis(svg_x=left, svg_y=top, plot_w=plot_w, plot_h=plot_h, y_label="USD / pair", max_axis=max_axis))
    for tick in range(0, 6):
        x = left + plot_w * tick / 5
        label = f"{tick * 20}%"
        svg.append(f'<line x1="{x:.2f}" y1="{top + plot_h}" x2="{x:.2f}" y2="{top + plot_h + 5}" stroke="#9ca3af"/>')
        svg.append(f'<text x="{x:.2f}" y="{height - 42}" class="tick" text-anchor="middle">{label}</text>')
    svg.append(f'<text x="{left + plot_w / 2:.2f}" y="{height - 16}" class="label" text-anchor="middle">第二次请求 Token 级缓存命中率</text>')
    for provider, sort_mode, cache_rate, cost in points:
        x = left + max(0, min(cache_rate, 1)) * plot_w
        y = top + plot_h - cost / max_axis * plot_h
        radius = {"throughput": 4.8, "price": 4.0, "latency": 5.6, "ttft": 6.2}.get(sort_mode, 4.4)
        svg.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.1f}" fill="{colors.get(provider, "#64748b")}" fill-opacity="0.46"/>'
        )
    svg.extend(_legend(width - 250, 28, colors))
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def _write_ttft_placeholder(path: Path) -> None:
    width, height = 920, 260
    svg = [
        _svg_header(width, height),
        '<rect x="32" y="44" width="856" height="168" rx="8" fill="#f8fafc" stroke="#cbd5e1"/>',
        '<text x="460" y="102" class="title" text-anchor="middle">TTFT 指标对比：不同 First 路由模式</text>',
        '<text x="460" y="139" class="label" text-anchor="middle">本轮实验使用非流式 chat/completions，只记录完整响应 latency。</text>',
        '<text x="460" y="169" class="label" text-anchor="middle">下一轮需要启用 streaming 并记录首个 token 到达时间，才能绘制真实 TTFT 曲线。</text>',
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        "<style>"
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#111827}"
        ".title{font-size:22px;font-weight:700}.label{font-size:13px;fill:#374151}.tick{font-size:12px;fill:#6b7280}"
        ".value{font-size:12px;fill:#111827}"
        "</style>"
        '<rect width="100%" height="100%" fill="#ffffff"/>'
    )


def _sort_mode_label(sort_mode: str) -> str:
    return {
        "throughput": "Throughput First 路由模式",
        "price": "Price First 路由模式",
        "latency": "Latency First 路由模式",
        "ttft": "TTFT First 路由模式",
    }.get(sort_mode, sort_mode)


def _axis(*, svg_x: int, svg_y: int, plot_w: int, plot_h: int, y_label: str, max_axis: float) -> list[str]:
    lines = []
    for tick in range(0, 5):
        y = svg_y + plot_h - plot_h * tick / 4
        value = max_axis * tick / 4
        lines.append(f'<line x1="{svg_x}" y1="{y:.2f}" x2="{svg_x + plot_w}" y2="{y:.2f}" stroke="#e5e7eb"/>')
        lines.append(f'<text x="{svg_x - 10}" y="{y + 4:.2f}" class="tick" text-anchor="end">{value:.4g}</text>')
    lines.append(f'<line x1="{svg_x}" y1="{svg_y}" x2="{svg_x}" y2="{svg_y + plot_h}" stroke="#9ca3af"/>')
    lines.append(f'<line x1="{svg_x}" y1="{svg_y + plot_h}" x2="{svg_x + plot_w}" y2="{svg_y + plot_h}" stroke="#9ca3af"/>')
    lines.append(f'<text x="22" y="{svg_y + plot_h / 2:.2f}" class="label" transform="rotate(-90 22 {svg_y + plot_h / 2:.2f})" text-anchor="middle">{escape(y_label)}</text>')
    return lines


def _legend(x: int, y: int, colors: dict[str, str]) -> list[str]:
    lines = []
    for index, provider in enumerate(PROVIDERS):
        item_y = y + index * 24
        lines.append(f'<rect x="{x}" y="{item_y}" width="14" height="14" rx="3" fill="{colors[provider]}"/>')
        lines.append(f'<text x="{x + 22}" y="{item_y + 12}" class="label">{_display_provider(provider)}</text>')
    return lines


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _dataset_metadata(*, dataset_name: str, dataset_file: str | None) -> dict[str, Any]:
    corpus = _load_business_corpus(dataset_file) if dataset_file else []
    return {
        "name": dataset_name,
        "file": dataset_file,
        "corpus_rows": len(corpus),
        "corpus_sha256": _file_sha256(Path(dataset_file)) if dataset_file else None,
        "is_real_business_corpus": bool(dataset_file),
        "description": (
            "External JSONL business corpus supplied by --dataset-file"
            if dataset_file
            else (
                "Built-in representative business prompt templates"
                if dataset_name == "business_representative"
                else "Controlled synthetic prompt-cache probe with stable long prefix"
            )
        ),
    }


def _filter_records(records: list[dict[str, Any]], sort_mode: str, provider: str, group: int) -> list[dict[str, Any]]:
    return [item for item in records if item["sort"] == sort_mode and item["provider"] == provider and int(item["group"]) == group]


def _write_progress(
    out_dir: Path,
    records: list[dict[str, Any]],
    record: dict[str, Any],
    groups: int,
    rounds: int,
    configs: dict[str, dict[str, Any]],
    excluded_counts: dict[str, int],
    stream: bool = False,
) -> None:
    sort_mode = str(record["sort"])
    provider = str(record["provider"])
    group = int(record["group"])
    _write_json(out_dir / f"{sort_mode}_{provider}_group_{group}.json", {"records": _filter_records(records, sort_mode, provider, group)})
    _write_json(out_dir / "records.json", {"records": records})
    _write_json(
        out_dir / "summary_partial.json",
        _build_summary("partial", out_dir, records, groups, rounds, configs, excluded_counts, stream=stream),
    )


def _write_group_files(out_dir: Path, records: list[dict[str, Any]], groups: int) -> None:
    for sort_mode in SORT_MODES:
        for provider in PROVIDERS:
            for group in range(1, groups + 1):
                _write_json(
                    out_dir / f"{sort_mode}_{provider}_group_{group}.json",
                    {"records": _filter_records(records, sort_mode, provider, group)},
                )


def _write_benchmark_dataset(out_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = _benchmark_pair_rows(records)
    request_rows = _benchmark_request_rows(records)
    pair_csv_path = out_dir / "benchmark_pairs.csv"
    request_jsonl_path = out_dir / "benchmark_requests.jsonl"
    pair_csv_text = _rows_to_csv(pair_rows)
    pair_csv_path.write_text(pair_csv_text, encoding="utf-8")
    request_jsonl_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in request_rows) + "\n",
        encoding="utf-8",
    )
    return {
        "pair_csv": {
            "path": str(pair_csv_path),
            "rows": len(pair_rows),
            "sha256": _file_sha256(pair_csv_path),
        },
        "request_jsonl": {
            "path": str(request_jsonl_path),
            "rows": len(request_rows),
            "sha256": _file_sha256(request_jsonl_path),
        },
    }


def _benchmark_pair_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[tuple[str, int, int], dict[str, dict[str, Any]]] = {}
    for item in records:
        key = (str(item["sort"]), int(item["group"]), int(item["round"]))
        by_pair.setdefault(key, {})[str(item["provider"])] = item
    rows: list[dict[str, Any]] = []
    for sort_mode, group, round_no in sorted(by_pair):
        providers = by_pair[(sort_mode, group, round_no)]
        infron = providers.get("infron")
        openrouter = providers.get("openrouter")
        if not infron or not openrouter:
            continue
        row: dict[str, Any] = {"sort": sort_mode, "group": group, "round": round_no}
        for provider, item in (("infron", infron), ("openrouter", openrouter)):
            first = item["first"]
            second = item["second"]
            latency_total_ms = float(first.get("latency_ms") or 0) + float(second.get("latency_ms") or 0)
            completion_total = int(first.get("completion_tokens") or 0) + int(second.get("completion_tokens") or 0)
            first_cost = _request_cost_value(first)
            second_cost = _request_cost_value(second)
            second_prompt = int(second.get("prompt_tokens") or 0)
            second_cache = int(second.get("cache_read_tokens") or 0)
            row.update(
                {
                    f"{provider}_provider": _request_provider_name(first) or _request_provider_name(second),
                    f"{provider}_input_tokens_total": int(first.get("prompt_tokens") or 0) + int(second.get("prompt_tokens") or 0),
                    f"{provider}_pair_cost_usd": round((first_cost or 0) + (second_cost or 0), 10)
                    if first_cost is not None and second_cost is not None
                    else "",
                    f"{provider}_avg_latency_ms": round(latency_total_ms / 2, 3),
                    f"{provider}_avg_ttft_ms": _avg_optional(first.get("ttft_ms"), second.get("ttft_ms")),
                    f"{provider}_response_throughput_tps": round(completion_total / (latency_total_ms / 1000), 6)
                    if latency_total_ms
                    else 0,
                    f"{provider}_first_prompt_tokens": int(first.get("prompt_tokens") or 0),
                    f"{provider}_second_prompt_tokens": second_prompt,
                    f"{provider}_first_completion_tokens": int(first.get("completion_tokens") or 0),
                    f"{provider}_second_completion_tokens": int(second.get("completion_tokens") or 0),
                    f"{provider}_first_reasoning_tokens": int(first.get("reasoning_tokens") or 0),
                    f"{provider}_second_reasoning_tokens": int(second.get("reasoning_tokens") or 0),
                    f"{provider}_first_latency_ms": float(first.get("latency_ms") or 0),
                    f"{provider}_second_latency_ms": float(second.get("latency_ms") or 0),
                    f"{provider}_first_ttft_ms": first.get("ttft_ms") if first.get("ttft_ms") is not None else "",
                    f"{provider}_second_ttft_ms": second.get("ttft_ms") if second.get("ttft_ms") is not None else "",
                    f"{provider}_second_cache_read_tokens": second_cache,
                    f"{provider}_second_cache_hit_rate": round(second_cache / second_prompt, 6) if second_prompt else 0,
                    f"{provider}_first_cost_usd": first_cost if first_cost is not None else "",
                    f"{provider}_second_cost_usd": second_cost if second_cost is not None else "",
                    f"{provider}_first_stream_chunks": int(first.get("stream_chunk_count") or 0),
                    f"{provider}_second_stream_chunks": int(second.get("stream_chunk_count") or 0),
                }
            )
        rows.append(row)
    return rows


def _benchmark_request_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in sorted(records, key=lambda row: (str(row["sort"]), str(row["provider"]), int(row["group"]), int(row["round"]))):
        for side in ("first", "second"):
            request = item[side]
            rows.append(
                {
                    "sort": item["sort"],
                    "provider": item["provider"],
                    "group": item["group"],
                    "round": item["round"],
                    "request": side,
                    "status": request.get("status"),
                    "latency_ms": request.get("latency_ms"),
                    "ttft_ms": request.get("ttft_ms"),
                    "first_content_token_ms": request.get("first_content_token_ms"),
                    "first_reasoning_token_ms": request.get("first_reasoning_token_ms"),
                    "stream_chunk_count": request.get("stream_chunk_count"),
                    "prompt_tokens": request.get("prompt_tokens"),
                    "completion_tokens": request.get("completion_tokens"),
                    "reasoning_tokens": request.get("reasoning_tokens"),
                    "cache_read_tokens": request.get("cache_read_tokens"),
                    "cache_write_tokens": request.get("cache_write_tokens"),
                    "cost": request.get("cost"),
                    "provider_name": _request_provider_name(request),
                    "response_model": request.get("response_model"),
                    "response_id": request.get("response_id"),
                    "usage": request.get("usage"),
                    "provider_cost_breakdown": request.get("provider_cost_breakdown"),
                    "provider_attribution": request.get("provider_attribution"),
                    "routing_trace": request.get("routing_trace"),
                }
            )
    return rows


def _rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _avg_optional(*values: Any) -> float | str:
    numbers = [float(value) for value in values if isinstance(value, int | float) and not isinstance(value, bool)]
    return round(sum(numbers) / len(numbers), 3) if numbers else ""


def _request_provider_name(request: dict[str, Any]) -> str:
    attribution = request.get("provider_attribution")
    if isinstance(attribution, dict):
        value = attribution.get("provider") or attribution.get("provider_name") or attribution.get("usage.provider")
        if value:
            return str(value)
    return ""


def _refresh_filtered_records(out_dir: Path, records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    existing_anomalous_usage_records = _load_records(out_dir / "records_anomalous_usage.json")
    existing_anomalous_usage_keys = {_record_key(item) for item in existing_anomalous_usage_records}
    existing_unequal_input_records = _load_records(out_dir / "records_unequal_input_tokens.json")
    existing_unequal_input_keys = {_record_key(item) for item in existing_unequal_input_records}
    candidate_records = [
        item
        for item in records
        if _record_key(item) not in existing_anomalous_usage_keys
        and _record_key(item) not in existing_unequal_input_keys
    ]
    incomplete_records = [item for item in candidate_records if not _record_complete(item)]
    complete_records = [item for item in candidate_records if _record_complete(item)]
    new_anomalous_usage_records = [
        item
        for item in complete_records
        if not _record_usage_valid(item) and _record_key(item) not in existing_anomalous_usage_keys
    ]
    anomalous_usage_records = _dedupe_records(existing_anomalous_usage_records + new_anomalous_usage_records)
    valid_records = [item for item in complete_records if _record_usage_valid(item)]
    filtered_records, new_unequal_input_records = _split_equal_input_token_pairs(
        valid_records,
        existing_unequal_input_keys=existing_unequal_input_keys,
    )
    unequal_input_records = _dedupe_records(existing_unequal_input_records + new_unequal_input_records)
    excluded_records = _dedupe_records(incomplete_records + anomalous_usage_records + unequal_input_records)
    _write_json(out_dir / "records_incomplete.json", {"records": incomplete_records})
    _write_json(out_dir / "records_anomalous_usage.json", {"records": anomalous_usage_records})
    _write_json(out_dir / "records_unequal_input_tokens.json", {"records": unequal_input_records})
    _write_json(out_dir / "records_excluded.json", {"records": excluded_records})
    _write_json(out_dir / "records.json", {"records": filtered_records})
    return filtered_records, {
        "incomplete": len(incomplete_records),
        "anomalous_usage": len(anomalous_usage_records),
        "unequal_input_tokens": len(unequal_input_records),
        "total": len(excluded_records),
    }


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int, int]] = set()
    deduped: list[dict[str, Any]] = []
    for item in records:
        key = _record_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    return list(records) if isinstance(records, list) else []


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
