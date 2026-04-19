"""Instruction model for the ICMP calculator.

A calculation decomposes into Y atomic ping-emission operations. Each
atomic op is dispatched to one host (indexed 0..N-1, wrapping by modulo).
Reply counts per op are aggregated to decode the result.

    decompose : (op, a, b) → [count_0, count_1, ..., count_{Y-1}]
    dispatch  : atomic ops + targets + id pool → [AtomicOp, ...]
    decode    : (op, [reply_count_0, ..., reply_count_{Y-1}]) → result
"""
from dataclasses import dataclass

SUPPORTED = ("add", "sub", "mul")


@dataclass
class AtomicOp:
    op_idx: int   # position in the atomic-op sequence (0..Y-1)
    count: int    # ping emissions
    host: str     # dispatched target (the ALU)
    icmp_id: int  # 16-bit id, unique per op for correlation


def decompose(operation, a, b):
    """Break (op, a, b) into per-atomic-op ping counts.

    add(a, b) → [a, b]         — two operands, summed at the decoder
    sub(a, b) → [a, b]         — two operands, decoded as r0 - r1
    mul(a, b) → [a] * b        — b copies of a, summed at the decoder
    """
    if operation == "add":
        return [a, b]
    if operation == "sub":
        return [a, b]
    if operation == "mul":
        return [a] * b
    raise ValueError(f"unsupported operation: {operation}")


def expected(operation, a, b):
    if operation == "add":
        return a + b
    if operation == "sub":
        return a - b
    if operation == "mul":
        return a * b
    raise ValueError(f"unsupported operation: {operation}")


def dispatch(operation, a, b, targets, id_pool):
    """Map each atomic op to a host (round-robin by index) and an ICMP id."""
    if not targets:
        raise ValueError("need at least one target")
    counts = decompose(operation, a, b)
    if len(id_pool) < len(counts):
        raise ValueError("id pool smaller than number of atomic ops")
    return [
        AtomicOp(op_idx=i, count=c, host=targets[i % len(targets)], icmp_id=id_pool[i])
        for i, c in enumerate(counts)
    ]


def decode(operation, counts_per_op):
    """Aggregate per-op reply counts into the final result."""
    if operation == "add":
        return sum(counts_per_op)
    if operation == "sub":
        if len(counts_per_op) != 2:
            raise ValueError("sub requires exactly 2 atomic ops")
        return counts_per_op[0] - counts_per_op[1]
    if operation == "mul":
        return sum(counts_per_op)
    raise ValueError(f"unsupported operation: {operation}")
