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

from core.burst import burst_send
from core.encoding import SUPPORTED, decompose, decode, dispatch, expected
from core.icmp_sniff import ReplySniffer
from core.targets import load_targets


LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def pick_iface(targets):
    if all(t in LOOPBACK for t in targets):
        return "lo"
    return None


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="icmp_calc.py",
        description="Distributed arithmetic via ICMP echo-reply counts.",
    )
    p.add_argument("--operation", required=True, choices=SUPPORTED)
    p.add_argument("--a", type=int, required=True)
    p.add_argument("--b", type=int, required=True)
    p.add_argument("--targets", required=True, help="path to targets file")
    p.add_argument("--debug", action="store_true", help="log every ICMP packet observed by the sniffer")
    p.add_argument("--drain", type=float, default=1.5, help="seconds to wait for replies after burst")
    return p.parse_args(argv)


def run(operation, a, b, targets_path, debug=False, drain=1.5):
    targets = load_targets(targets_path)
    if not targets:
        print(f"no targets in {targets_path}", file=sys.stderr)
        return 2

    counts = decompose(operation, a, b)
    n_ops = len(counts)
    id_pool = random.sample(range(1, 0x10000), n_ops) if n_ops else []
    ops = dispatch(operation, a, b, targets, id_pool)
    exp = expected(operation, a, b)

    print(f"[+] {operation}({a}, {b}) → {n_ops} atomic op(s) across {len(targets)} ALU(s)")
    for op in ops:
        print(f"    op[{op.op_idx}]: {op.host} ← {op.count} pings (id={op.icmp_id})")

    iface = pick_iface(targets)
    print(f"[+] sniffer iface={iface or 'default'}")
    sniffer = ReplySniffer(ops, iface=iface, debug=debug)
    sniffer.start()
    try:
        burst_send(ops)
    finally:
        sniffer.stop(drain=drain)

    counts_by_op = [sniffer.counts[op.op_idx] for op in ops]
    result = decode(operation, counts_by_op) if ops else 0

    print(f"[+] sniffer observed {sniffer.total_icmp_seen} total ICMP packets")
    print("[+] replies per op:")
    for op, c in zip(ops, counts_by_op):
        print(f"    op[{op.op_idx}] @ {op.host}: {c}")
    print(f"[=] {operation}({a}, {b}) = {result}  (expected {exp})")
    return 0 if result == exp else 1


def main(argv=None):
    args = parse_args(argv)
    if os.geteuid() != 0:
        print("warning: raw sockets usually need root or CAP_NET_RAW", file=sys.stderr)
    return run(args.operation, args.a, args.b, args.targets, debug=args.debug, drain=args.drain)


if __name__ == "__main__":
    sys.exit(main())
