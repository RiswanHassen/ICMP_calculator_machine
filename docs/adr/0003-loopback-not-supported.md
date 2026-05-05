# ADR 0003 — 127.0.0.1 is not a supported target

- **Status:** accepted
- **Date:** 2026-05-05

## Context

A tester's first instinct is to point the calculator at `127.0.0.1`
because it doesn't need network access. Empirically this fails: the
sender emits N echo requests, `tcpdump -i lo icmp` shows them on the
wire, but no echo replies ever come back. Reply count is always zero.

The cause is that `SOCK_RAW` with `IP_HDRINCL` (which is what scapy's
`conf.L3socket()` uses) sends through a path that bypasses the kernel's
ICMP echo-reply generator when the destination is loopback. The
generator only kicks in for ICMP that arrives via the regular receive
path. On loopback, the raw send and the kernel's reply machinery don't
intersect.

## Decision

Document the limitation, do not work around it. We:

1. Note the constraint in `README.md` and `targets.txt`.
2. Print a warning is *not* added — it would imply the user might do
   something to fix it. They cannot.
3. Do **not** add a SOCK_DGRAM/IPPROTO_ICMP fallback for loopback. That
   would require a parallel send path with different id/seq semantics
   and split the burst sender into two regimes for one weak use case
   (testing without a real network).

The recommended local test target is the default gateway or a
known-reachable public host (e.g. `8.8.8.8`, `1.1.1.1`).

## Consequences

**Positive**

- One send path, one set of correlation rules. Burst sender stays
  minimal.
- The constraint forces tests to exercise the real network path, which
  is what the PoC actually demonstrates.

**Negative**

- A working CI/integration test would need outbound ICMP, which most CI
  runners disallow. Hence we explicitly do *not* set up live tests in
  CI — verification is manual against known-good hosts.
- New users hit this once and have to read the README to understand why.
