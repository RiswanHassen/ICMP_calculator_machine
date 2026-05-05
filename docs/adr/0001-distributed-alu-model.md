# ADR 0001 — Distributed ALU model

- **Status:** accepted
- **Date:** 2026-05-05

## Context

The original sketch (v0.1) sent `n1` then `n2` pings to a single host and
counted replies. That design conflated three separate ideas — the
operand encoding, the host as compute target, and the result decoding —
inside one serial code path. It also gave no leverage for the project's
core narrative ("the internet is the computer").

A redesign needed to (a) make the analogy to a CPU explicit, (b) allow
real parallelism across the network, and (c) keep the decoding rule
trivial enough to fit in one line per operation.

## Decision

Model every calculation as a list of *atomic operations*. Each atomic op
is a tuple `(count, host, icmp_id)`. An operation's `decompose` rule
produces this list; a `dispatch` step assigns hosts by index modulo the
number of targets; a `decode` rule turns the per-op reply counts back
into the result.

| op  | decomposition | decoding       |
|-----|---------------|----------------|
| add | `[a, b]`      | sum            |
| sub | `[a, b]`      | `r[0] - r[1]`  |
| mul | `[a] * b`     | sum            |

Hosts are the ALUs; line position in `targets.txt` is the dispatch
index; per-op ICMP id is the correlation key that lets us attribute a
reply to the op that produced it, even when two ops landed on the same
host.

## Consequences

**Positive**

- New operations are added in *one* file (`core/encoding.py`) — no
  changes to the burst sender or the sniffer.
- The decoder is pure, side-effect free, and trivially testable
  (`tests/test_encoding.py`).
- The "internet as computer" framing is now load-bearing in the code,
  not just narrative in the README.

**Negative**

- `sub` only works for two operands. Generalizing to arbitrary arity
  would need a different decoder shape.
- `mul(a, b)` produces `b` atomic ops, which can grow large. We don't
  guard against pathological inputs — the user is expected to pick
  sensible operands (the PoC is a demo, not a stress tester).
- Reply count is bounded by what the chosen ALU returns; a flaky or
  rate-limited host quietly under-counts. The ALU model exposes this
  cleanly (per-op count) but does not solve it.
