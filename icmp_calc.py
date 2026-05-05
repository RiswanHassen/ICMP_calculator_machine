#!/usr/bin/env python3
"""ICMP Calculator Machine — the internet is the computer.

A calculation decomposes into Y atomic operations. Each op is dispatched
to a host (the ALU), which emits its ping count as echo requests. All
atomic ops fire in parallel (burst). Replies are correlated per op via
ICMP id; summing across ops decodes the result.

Requires raw socket privileges (root or CAP_NET_RAW).
"""
import argparse
import os
import random
import sys
from typing import Optional, Sequence

from core.burst import burst_send
from core.encoding import SUPPORTED, decompose, decode, dispatch, expected
from core.errors import ErrorCode
from core.log import for_run, new_run_id, setup as log_setup
from core.sniff import ReplySniffer
from core.targets import load_targets

LOOPBACK = {"127.0.0.1", "::1", "localhost"}
ICMP_ID_MAX = 0x10000  # 16-bit id field
DEFAULT_DRAIN_SEC = 1.5


def pick_iface(targets: Sequence[str]) -> Optional[str]:
    """Loopback replies only show up on `lo`; mixed/remote targets → let
    scapy pick the default interface."""
    if all(t in LOOPBACK for t in targets):
        return "lo"
    return None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="icmp_calc.py",
        description="Distributed arithmetic via ICMP echo-reply counts.",
    )
    p.add_argument("--operation", required=True, choices=SUPPORTED)
    p.add_argument("--a", type=int, required=True)
    p.add_argument("--b", type=int, required=True)
    p.add_argument("--targets", required=True, help="path to targets file")
    p.add_argument("--debug", action="store_true", help="DEBUG-level log incl. per-packet sniff trace")
    p.add_argument(
        "--drain",
        type=float,
        default=DEFAULT_DRAIN_SEC,
        help="seconds to wait for replies after burst",
    )
    return p.parse_args(argv)


def run(
    operation: str,
    a: int,
    b: int,
    targets_path: str,
    debug: bool = False,
    drain: float = DEFAULT_DRAIN_SEC,
) -> tuple[int, ErrorCode]:
    log_setup("DEBUG" if debug else os.environ.get("ICMPCALC_LOG_LEVEL", "INFO"))
    run_id = new_run_id()
    log = for_run("icmp_calc", run_id)

    targets = load_targets(targets_path)
    if not targets:
        log.error("no_targets", extra={"path": targets_path})
        log.error("RUN_FAIL", extra={"code": ErrorCode.NO_TARGETS.value})
        print(f"no targets in {targets_path}", file=sys.stderr)
        return 2, ErrorCode.NO_TARGETS

    counts = decompose(operation, a, b)
    n_ops = len(counts)
    id_pool = random.sample(range(1, ICMP_ID_MAX), n_ops) if n_ops else []
    ops = dispatch(operation, a, b, targets, id_pool)
    exp = expected(operation, a, b)

    log.info(
        "plan",
        extra={"op": operation, "a": a, "b": b, "n_ops": n_ops, "n_targets": len(targets), "expected": exp},
    )
    print(f"[+] {operation}({a}, {b}) → {n_ops} atomic op(s) across {len(targets)} ALU(s)")
    for op in ops:
        print(f"    op[{op.op_idx}]: {op.host} ← {op.count} pings (id={op.icmp_id})")

    iface = pick_iface(targets)
    sniffer = ReplySniffer(ops, iface=iface)
    log.info("sniffer.start", extra={"iface": iface or "default"})
    sniffer.start()
    try:
        log.info("burst.start", extra={"n_ops": n_ops})
        burst_send(ops)
        log.info("burst.end")
    finally:
        sniffer.stop(drain=drain)

    counts_by_op = [sniffer.counts[op.op_idx] for op in ops]
    result = decode(operation, counts_by_op) if ops else 0
    match = result == exp

    log.info(
        "result",
        extra={
            "operation": operation,
            "result": result,
            "expected": exp,
            "match": match,
            "icmp_seen": sniffer.total_icmp_seen,
            "per_op": counts_by_op,
        },
    )
    print("[+] replies per op:")
    for op, c in zip(ops, counts_by_op):
        print(f"    op[{op.op_idx}] @ {op.host}: {c}")
    print(f"[=] {operation}({a}, {b}) = {result}  (expected {exp})")

    if match:
        log.info("RUN_OK", extra={"code": ErrorCode.OK.value})
        return 0, ErrorCode.OK
    log.error("RUN_FAIL", extra={"code": ErrorCode.RESULT_MISMATCH.value})
    return 1, ErrorCode.RESULT_MISMATCH


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if os.geteuid() != 0:
        print("warning: raw sockets usually need root or CAP_NET_RAW", file=sys.stderr)
    exit_code, _ = run(
        args.operation, args.a, args.b, args.targets, debug=args.debug, drain=args.drain
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
