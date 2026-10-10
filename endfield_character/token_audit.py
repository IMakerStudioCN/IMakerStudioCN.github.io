"""Audit the recorded model tokens for this Blender request (standard library only).

Reads usage metadata, never exports conversation text. Cache and reasoning counts
are subsets of input/output respectively and are not added to total_tokens again.
Run again after the assistant finishes to include its final response.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


DEFAULT_LOG = Path(
    r"C:\Users\36048\.codex\sessions\2026\09\10"
    r"\rollout-2026-09-10T09-01-32-01a088d5-8e1e-7d12-bd38-8e73769cb0ba.jsonl"
)
DEFAULT_ROOT_TURN = "01a088d7-e020-74e0-850b-5d571a8ce55f"
FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens", "total_tokens",
)


def rows(path: Path):
    # A writer may still be appending the final line. Skip an incomplete tail.
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                if not line.endswith("\n"):
                    break
                raise ValueError(f"Malformed JSON in {path.name}, line {line_number}")


def empty_usage():
    return dict.fromkeys(FIELDS, 0)


def usage_values(value):
    return {field: int(value.get(field, 0)) for field in FIELDS}


def collect(root_log: Path, root_turn_id: str, sessions_dir: Path):
    root_id = None
    request_ordinal = None
    request_timestamp = None
    baseline = empty_usage()
    root_complete = False
    active_turn = None
    for row in rows(root_log):
        payload = row.get("payload", {})
        if row.get("type") == "session_meta":
            root_id = payload.get("id") or payload.get("session_id")
        if row.get("type") == "event_msg" and payload.get("type") == "task_started":
            active_turn = payload.get("turn_id")
        if (
            active_turn == root_turn_id
            and row.get("type") == "response_item"
            and payload.get("role") == "user"
            and any("三视图" in content.get("text", "")
                    for content in payload.get("content", []))
        ):
            request_ordinal = row.get("ordinal")
            request_timestamp = row.get("timestamp")
        if row.get("type") == "event_msg":
            if payload.get("type") in ("task_complete", "task_completed"):
                if (payload.get("turn_id") or active_turn) == root_turn_id:
                    root_complete = True
            if request_ordinal is None and payload.get("type") == "token_count":
                info = payload.get("info") or {}
                baseline = usage_values(info.get("total_token_usage") or {})
    if not root_id:
        raise ValueError("No session metadata found in the root log")

    records = {}
    thread_meta = {}
    files = sorted(set(sessions_dir.rglob("rollout-*.jsonl")) | {root_log})
    for path in files:
        for row in rows(path):
            payload = row.get("payload", {})
            if row.get("type") == "session_meta":
                thread_id = payload.get("id") or payload.get("session_id")
                thread_meta[thread_id] = {
                    "agent_path": payload.get("agent_path") or (
                        "/root" if thread_id == root_id else None),
                    "parent_thread_id": payload.get("parent_thread_id"),
                }
            if row.get("type") != "token_usage_record":
                continue
            if payload.get("root_turn_id") != root_turn_id:
                continue
            if payload.get("session_id") != root_id:
                continue
            response_id = payload.get("response_id")
            if not response_id:
                raise ValueError("Usage record has no response_id; cannot safely deduplicate")
            record = {
                "thread_id": payload["thread_id"],
                "timestamp": row["timestamp"],
                "usage": usage_values(payload.get("usage") or {}),
            }
            if response_id in records:
                old = records[response_id]
                if old["thread_id"] != record["thread_id"] or old["usage"] != record["usage"]:
                    raise ValueError("Conflicting duplicate usage records")
            else:
                records[response_id] = record
    if not records:
        raise ValueError("No usage records for the requested root turn were found")

    aggregate = empty_usage()
    per_thread = defaultdict(lambda: {"response_count": 0, "usage": empty_usage()})
    for record in records.values():
        thread = per_thread[record["thread_id"]]
        thread["response_count"] += 1
        for field in FIELDS:
            thread["usage"][field] += record["usage"][field]
            aggregate[field] += record["usage"][field]
    thread_report = []
    for thread_id, data in per_thread.items():
        thread_report.append({
            "thread_id": thread_id,
            **thread_meta.get(thread_id, {}),
            **data,
        })
    thread_report.sort(key=lambda item: item.get("agent_path") or item["thread_id"])
    if aggregate["input_tokens"] + aggregate["output_tokens"] != aggregate["total_tokens"]:
        raise ValueError("Recorded total_tokens differs from input_tokens + output_tokens")
    return {
        "sampled_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_recorded_response_at_utc": max(item["timestamp"] for item in records.values()),
        "root_thread_id": root_id,
        "root_turn_id": root_turn_id,
        "request_timestamp_utc": request_timestamp,
        "request_ordinal": request_ordinal,
        "root_thread_baseline_before_request": baseline,
        "root_completion_event_observed": root_complete,
        "response_count": len(records),
        "totals": aggregate,
        "uncached_input_tokens": aggregate["input_tokens"] - aggregate["cached_input_tokens"],
        "threads": thread_report,
        "method": "Sum token_usage_record.payload.usage for the exact root_turn_id and session_id; deduplicate response_id across root and descendant logs.",
        "limitations": [
            "Exact for model response usage already recorded locally at sampling time; in-flight responses and unflushed log entries are excluded.",
            "Rerun after the conversation turn completes to include its final answer; observe the sample timestamp when reporting the value.",
            "Cached input is a subset of input tokens; reasoning output is a subset of output tokens. Do not add these subsets again.",
            "Repeated input context is counted on each response. These figures are token usage, not unique text length, account percentage, or monetary cost.",
            "Includes model work performed by the token-audit agent. Blender CPU/GPU rendering is not itself a model token response.",
            "The default scan covers the root log's date folder. For work spanning midnight, pass --sessions-dir with the common date-folder parent.",
        ],
    }


def markdown(report):
    totals = report["totals"]
    lines = [
        "# 本次 Blender 建模 Token 统计", "",
        f"采样时间（UTC）：{report['sampled_at_utc']}", "",
        f"最新已记录模型响应（UTC）：{report['latest_recorded_response_at_utc']}", "",
        f"**已记录总计：{totals['total_tokens']:,} Token**，包含主线程与本次任务的所有已记录子线程响应。", "",
        "| 项目 | Token |", "| --- | ---: |",
        f"| 输入 | {totals['input_tokens']:,} |",
        f"| 其中缓存输入（已包含于输入） | {totals['cached_input_tokens']:,} |",
        f"| 输出 | {totals['output_tokens']:,} |",
        f"| 其中推理输出（已包含于输出） | {totals['reasoning_output_tokens']:,} |",
        f"| 合计 | {totals['total_tokens']:,} |", "",
        "| 线程 | 模型响应次数 | Token |", "| --- | ---: | ---: |",
    ]
    for item in report["threads"]:
        lines.append(f"| {item.get('agent_path') or item['thread_id']} | {item['response_count']} | {item['usage']['total_tokens']:,} |")
    lines += [
        "",
        f"请求起点：{report['request_timestamp_utc']}（主线程记录序号 {report['request_ordinal']}）；请求前主线程累计基线：{report['root_thread_baseline_before_request']['total_tokens']:,}。",
        "",
        "统计方式：筛选本次 root_turn_id 与 session_id 对应的逐响应 token_usage_record，按 response_id 去重后求和。缓存输入和推理输出不重复累加。",
        "",
        "此值精确对应采样时已写入本地日志的模型响应；尚在生成或尚未写入的响应不在其中。请在本轮对话结束后再次运行 token_audit.py，将最终答复计入。模型反复读取上下文也计入输入，所以总数不是文本的去重字数，也不代表费用。统计包含本统计子线程的用量；Blender 渲染本身不额外产生模型 Token。",
        "",
        f"已观察到本轮结束事件：{'是' if report['root_completion_event_observed'] else '否'}。",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--root-turn-id", default=DEFAULT_ROOT_TURN)
    parser.add_argument("--sessions-dir", type=Path,
                        help="Default: the directory containing --root-log")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    report = collect(args.root_log, args.root_turn_id, args.sessions_dir or args.root_log.parent)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "token_usage.json"
    md_path = args.output_dir / "token_usage.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"totals": report["totals"], "response_count": report["response_count"],
                      "latest_recorded_response_at_utc": report["latest_recorded_response_at_utc"],
                      "root_completion_event_observed": report["root_completion_event_observed"],
                      "json_report": str(json_path), "markdown_report": str(md_path)},
                     ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Token audit failed: {error}", file=sys.stderr)
        raise SystemExit(1)
