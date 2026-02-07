#!/usr/bin/env python3
"""Benchmark old vs new dedup filtering logic.

This simulates the previous O(n^2) list membership filter and the current
set-based filter used in APIAnalyzer._apply_quality_filtering.
"""

from __future__ import annotations

import time
from typing import List, Tuple

from allbeapi.analyzer import FunctionInfo


def build_scored_functions(total: int, dup_ratio: float = 0.5) -> Tuple[List[Tuple[FunctionInfo, float]], List[FunctionInfo]]:
    scored = []
    deduped = []

    dup_cutoff = int(total * dup_ratio)
    for i in range(total):
        qual = f"pkg.mod.func_{i}"
        f = FunctionInfo(
            name=f"func_{i}",
            module="pkg.mod",
            class_name=None,
            qualname=qual,
            signature="func()",
            doc=None,
            parameters=[],
            return_type=None,
            is_async=False,
            http_method="get",
            path=f"/func_{i}",
        )
        scored.append((f, 90.0))
        if i < dup_cutoff:
            deduped.append(f)

    return scored, deduped


def old_filter(scored_functions: List[Tuple[FunctionInfo, float]], deduped: List[FunctionInfo]):
    return [(f, s) for f, s in scored_functions if f in deduped]


def new_filter(scored_functions: List[Tuple[FunctionInfo, float]], deduped: List[FunctionInfo]):
    deduped_qualnames = {f.qualname for f in deduped}
    return [(f, s) for f, s in scored_functions if f.qualname in deduped_qualnames]


def run_once(total: int, loops: int = 5):
    scored, deduped = build_scored_functions(total)

    t0 = time.perf_counter()
    for _ in range(loops):
        old_filter(scored, deduped)
    t1 = time.perf_counter()

    for _ in range(loops):
        new_filter(scored, deduped)
    t2 = time.perf_counter()

    old_time = t1 - t0
    new_time = t2 - t1
    ratio = old_time / new_time if new_time > 0 else float('inf')
    return old_time, new_time, ratio


def main():
    for total in (1_000, 5_000, 10_000, 20_000):
        old_time, new_time, ratio = run_once(total)
        print(f"total={total:>6} | old={old_time:.4f}s | new={new_time:.4f}s | speedup={ratio:.1f}x")


if __name__ == "__main__":
    main()
