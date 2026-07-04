import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_script_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "rerun_routing_sort_cache_cost_ab.py"
    spec = importlib.util.spec_from_file_location("rerun_routing_sort_cache_cost_ab", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stream_response_keeps_final_chunk_top_level_cost_fields():
    module = _load_script_module()
    response = [
        b'data: {"id":"abc","model":"deepseek/deepseek-v4-flash","choices":[{"delta":{"reasoning_content":"x"}}]}\n\n',
        (
            b'data: {"id":"abc","provider":"gmicloud","cost":0.0000123,'
            b'"cost_details":{"upstream_inference_cost":0.0000123},'
            b'"usage":{"prompt_tokens":25,"completion_tokens":28,"total_tokens":53},'
            b'"choices":[]}\n\n'
        ),
        b"data: [DONE]\n\n",
    ]

    payload, metrics = module._read_stream_response(response, started=0)

    assert payload["cost"] == 0.0000123
    assert payload["cost_details"] == {"upstream_inference_cost": 0.0000123}
    assert payload["usage"]["prompt_tokens"] == 25
    assert payload["provider"] == "gmicloud"
    assert metrics["stream_chunk_count"] == 2


def test_ttft_first_uses_platform_specific_provider_sort():
    module = _load_script_module()

    infron_payload = module._payload(sort_mode="ttft", provider_name="infron")
    openrouter_payload = module._payload(sort_mode="ttft", provider_name="openrouter")

    assert infron_payload["provider"]["sort"] == "ttft"
    assert openrouter_payload["provider"]["sort"] == "latency"


def test_default_reasoning_effort_omits_reasoning_field():
    module = _load_script_module()

    payload = module._payload(sort_mode="throughput", provider_name="infron")

    assert "reasoning" not in payload


def test_explicit_reasoning_effort_sends_reasoning_field():
    module = _load_script_module()

    payload = module._payload(sort_mode="throughput", provider_name="infron", reasoning_effort="none")

    assert payload["reasoning"] == {"effort": "none"}


def test_api_protocol_parser_accepts_endpoint_aliases():
    module = _load_script_module()

    protocols = module._parse_api_protocols("/v1/messages,/v1/chat/completions,/v1/responses")

    assert protocols == ["messages", "chat_completions", "responses"]


def test_api_protocol_payloads_use_protocol_native_shapes():
    module = _load_script_module()

    chat = module._payload(api_protocol="chat_completions", sort_mode="throughput", provider_name="infron")
    responses = module._payload(api_protocol="responses", sort_mode="throughput", provider_name="infron")
    messages = module._payload(api_protocol="messages", sort_mode="throughput", provider_name="infron")

    assert "messages" in chat
    assert "input" in responses
    assert responses["max_output_tokens"] == 16
    assert "system" in messages
    assert all(item["role"] in {"user", "assistant"} for item in messages["messages"])
    assert "usage" not in messages


def test_endpoint_url_maps_v1_base_to_protocol_paths():
    module = _load_script_module()

    assert module._endpoint_url(base_url="https://llm.onerouter.pro/v1", endpoint_path="/v1/messages") == "https://llm.onerouter.pro/v1/messages"
    assert module._endpoint_url(base_url="https://llm.onerouter.pro", endpoint_path="/v1/responses") == "https://llm.onerouter.pro/v1/responses"


def test_provider_configs_use_same_local_proxy_override():
    module = _load_script_module()
    settings = SimpleNamespace(
        model_probe_base_url="https://llm.onerouter.pro",
        model_probe_api_key="infron-key",
        model_probe_infron_cache_policy="enabled",
        model_probe_infron_proxy_url=None,
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_api_key="openrouter-key",
        model_probe_openrouter_cache_policy="enabled",
        model_probe_openrouter_proxy_url="socks5://127.0.0.1:9999",
        openrouter_http_referer=None,
        openrouter_app_title=None,
    )

    configs = module._provider_configs(settings, local_proxy_url="socks5://127.0.0.1:1086")

    assert configs["infron"]["proxy_url"] == "socks5://127.0.0.1:1086"
    assert configs["openrouter"]["proxy_url"] == "socks5://127.0.0.1:1086"


def test_network_environment_summary_redacts_proxy_credentials():
    module = _load_script_module()
    configs = {
        "infron": {"proxy_url": "http://user:pass@127.0.0.1:8080"},
        "openrouter": {"proxy_url": "http://user:pass@127.0.0.1:8080"},
    }

    summary = module._network_environment_summary(configs)

    assert summary["same_local_proxy"] is True
    assert summary["proxy_enabled"] is True
    assert summary["proxy_url_redacted"] == "http://***:***@127.0.0.1:8080"


def test_input_token_pair_filter_allows_deltas_up_to_50():
    module = _load_script_module()

    def record(provider, first_tokens, second_tokens, api_protocol="chat_completions"):
        return {
            "api_protocol": api_protocol,
            "sort": "throughput",
            "provider": provider,
            "group": 1,
            "round": 1,
            "first": {"prompt_tokens": first_tokens},
            "second": {"prompt_tokens": second_tokens},
        }

    matched, excluded = module._split_equal_input_token_pairs(
        [
            record("infron", 1000, 1500),
            record("openrouter", 1050, 1450),
        ]
    )

    assert len(matched) == 2
    assert excluded == []


def test_input_token_pair_filter_excludes_deltas_over_50():
    module = _load_script_module()

    def record(provider, first_tokens, second_tokens, api_protocol="chat_completions"):
        return {
            "api_protocol": api_protocol,
            "sort": "throughput",
            "provider": provider,
            "group": 1,
            "round": 1,
            "first": {"prompt_tokens": first_tokens},
            "second": {"prompt_tokens": second_tokens},
        }

    matched, excluded = module._split_equal_input_token_pairs(
        [
            record("infron", 1000, 1500),
            record("openrouter", 1051, 1450),
        ]
    )

    assert matched == []
    assert len(excluded) == 2


def test_input_token_pair_filter_keeps_protocols_isolated():
    module = _load_script_module()

    def record(provider, first_tokens, second_tokens, api_protocol):
        return {
            "api_protocol": api_protocol,
            "sort": "throughput",
            "provider": provider,
            "group": 1,
            "round": 1,
            "first": {"prompt_tokens": first_tokens},
            "second": {"prompt_tokens": second_tokens},
        }

    matched, excluded = module._split_equal_input_token_pairs(
        [
            record("infron", 1000, 1500, "chat_completions"),
            record("openrouter", 1000, 1500, "chat_completions"),
            record("infron", 2000, 2500, "responses"),
        ]
    )

    assert len(matched) == 2
    assert len(excluded) == 1
    assert excluded[0]["api_protocol"] == "responses"


def test_prompt_length_tiers_are_parsed_and_assigned_by_round():
    module = _load_script_module()

    tiers = module._parse_prompt_length_tiers("short:1500,medium:8000,long:32000")

    assert [item["label"] for item in tiers] == ["short", "medium", "long"]
    assert [item["target_prompt_tokens"] for item in tiers] == [1500, 8000, 32000]
    assert module._prompt_length_tier_for_round(tiers, group=1, round_no=1)["label"] == "short"
    assert module._prompt_length_tier_for_round(tiers, group=1, round_no=2)["label"] == "medium"
    assert module._prompt_length_tier_for_round(tiers, group=1, round_no=3)["label"] == "long"
    assert module._prompt_length_tier_for_round(tiers, group=1, round_no=4)["label"] == "short"


def test_prompt_length_tier_summary_and_dataset_exports_include_tier(tmp_path):
    module = _load_script_module()
    tiers = module._parse_prompt_length_tiers("short:1500,long:32000")

    def request(prompt_tokens, cache_read_tokens):
        return {
            "status": 200,
            "latency_ms": 1000,
            "ttft_ms": 100,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": 10,
            "reasoning_tokens": 0,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": 0,
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 10},
            "provider_attribution": {"provider": "test-provider"},
        }

    def record(provider, tier, round_no, cache_read_tokens):
        return {
            "sort": "throughput",
            "provider_sort": "throughput",
            "provider": provider,
            "group": 1,
            "round": round_no,
            "prompt_length_tier": tier["label"],
            "target_prompt_tokens": tier["target_prompt_tokens"],
            "prompt_length_tier_index": tier["index"],
            "first": request(tier["target_prompt_tokens"], 0),
            "second": request(tier["target_prompt_tokens"], cache_read_tokens),
        }

    records = [
        record("infron", tiers[0], 1, 1200),
        record("openrouter", tiers[0], 1, 900),
        record("infron", tiers[1], 2, 30000),
        record("openrouter", tiers[1], 2, 10000),
    ]
    summary = module._build_summary(
        "test",
        tmp_path,
        records,
        1,
        2,
        {
            "infron": {"base_url": "https://infron.example/v1", "cache_policy": "enabled", "proxy_url": None},
            "openrouter": {"base_url": "https://openrouter.example/v1", "cache_policy": "enabled", "proxy_url": None},
        },
        prompt_length_tiers=tiers,
    )
    dataset = module._write_benchmark_dataset(tmp_path, records)

    assert summary["execution_profile"]["prompt_length_stratification_enabled"] is True
    assert summary["prompt_length_tiers"]["short"]["providers"]["infron"]["token_cache_hit_rate"] == 0.8
    assert summary["prompt_length_tiers"]["long"]["comparison"]["cache_winner"] == "Infron"
    pair_csv = (tmp_path / "benchmark_pairs.csv").read_text(encoding="utf-8")
    request_jsonl = (tmp_path / "benchmark_requests.jsonl").read_text(encoding="utf-8")
    assert "prompt_length_tier" in pair_csv
    assert "target_prompt_tokens" in pair_csv
    assert '"prompt_length_tier":"long"' in request_jsonl
    assert dataset["pair_csv"]["rows"] == 2
