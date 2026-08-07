"""Dev 环境简单压测：/api/portal 列表类接口并发基线。

用法:
    python scripts/perf_baseline.py --concurrency 20 --requests 200
输出: 每接口的请求数、成功率、平均/中位/p95/p99 延迟、吞吐量。

说明: 仅用于 dev 环境基线参考，非正式压测。AAD_BYPASS=1 下无需鉴权。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import statistics
import time

import requests

DEFAULT_ENDPOINTS = [
    "/api/portal/dashboard",
    "/api/portal/courses",
    "/api/portal/notifications",
    "/api/portal/recommend?position=sales&limit=6",
]


def _parse_args():
    parser = argparse.ArgumentParser(description="dev portal API baseline load test")
    parser.add_argument("--base", default="http://localhost:8080", help="dev base URL")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument(
        "--endpoint",
        action="append",
        default=None,
        help="endpoint path; repeatable (default: the 4 portal list endpoints)",
    )
    return parser.parse_args()


def _run_once(base: str, path: str) -> tuple[float, int]:
    start = time.perf_counter()
    try:
        resp = requests.get(f"{base}{path}", timeout=30)
        return (time.perf_counter() - start) * 1000, resp.status_code
    except Exception:
        return (time.perf_counter() - start) * 1000, 0


def _percentile(sorted_latencies: list[float], pct: float) -> float:
    if not sorted_latencies:
        return 0.0
    index = max(0, min(len(sorted_latencies) - 1, int(len(sorted_latencies) * pct)))
    return sorted_latencies[index]


def main() -> int:
    args = _parse_args()
    endpoints = args.endpoint or DEFAULT_ENDPOINTS
    print(f"压测基线: base={args.base} concurrency={args.concurrency} requests={args.requests}")
    print()

    for path in endpoints:
        latencies: list[float] = []
        statuses: dict[int, int] = {}
        failures = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = [
                pool.submit(_run_once, args.base, path)
                for _ in range(args.requests)
            ]
            for fut in concurrent.futures.as_completed(futures):
                latency_ms, status = fut.result()
                latencies.append(latency_ms)
                if status == 0:
                    failures += 1
                else:
                    statuses[status] = statuses.get(status, 0) + 1

        latencies.sort()
        total_sec = sum(latencies) / 1000.0
        qps = len(latencies) / total_sec if total_sec > 0 else 0.0
        ok = len(latencies) - failures
        success_pct = (ok / len(latencies)) * 100 if latencies else 0.0

        print(f"── {path} ──")
        print(f"  请求数={len(latencies)}  成功={ok}  失败={failures}  "
              f"成功率={success_pct:.1f}%")
        print(f"  延迟(ms) avg={statistics.mean(latencies):.2f}  "
              f"p50={_percentile(latencies, 0.5):.2f}  "
              f"p95={_percentile(latencies, 0.95):.2f}  "
              f"p99={_percentile(latencies, 0.99):.2f}  max={latencies[-1] if latencies else 0:.2f}")
        print(f"  吞吐 QPS={qps:.1f}  HTTP 分布={statuses or {0: failures}}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
