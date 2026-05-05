# ADR 0002 — Burst execution via threads + Barrier

- **Status:** accepted
- **Date:** 2026-05-05

## Context

The original send loop ran `scapy.send()` sequentially with a 50 ms
sleep between packets, all from one thread. That defeats the point of
treating multiple hosts as parallel ALUs: the "burst" was actually a
serial drip, latencies stacked up, and the dispatched-to-host metaphor
collapsed into "talk to host A, then host B".

We needed all atomic ops to leave roughly together, and each host to
see its full count back-to-back so the kernel-side echo-reply pipeline
runs at full speed.

## Decision

One Python thread per atomic op. All threads share a `threading.Barrier`
sized to the number of ops; each thread builds its own L3 raw socket
during setup, then blocks on `barrier.wait()`. When the last thread
arrives, the barrier releases and every thread fires its `count` pings
back-to-back through its own socket.

Two specific choices that fall out of this:

1. **One socket per thread**, not a shared socket. Scapy's send path
   serializes on a per-socket lock; sharing would re-introduce the
   serial behavior we're trying to avoid.
2. **No inter-ping sleep.** The kernel's send queue is the natural rate
   limiter; adding sleeps makes the burst slower without adding
   reliability.

## Consequences

**Positive**

- True parallel dispatch across N ALUs.
- Barrier guarantees we don't accidentally start sending before some
  threads have finished socket setup.
- Per-thread sockets eliminate scapy-internal contention.

**Negative**

- Spawns one OS thread per atomic op. For `mul(a, big_b)` that's `b`
  threads. Acceptable for the demo range; anything beyond a few hundred
  would warrant a thread pool.
- Raw sockets need `CAP_NET_RAW`; if a thread fails to acquire its
  socket, the others will deadlock waiting at the barrier. Not a real
  problem in practice (either all sockets succeed or none do, since
  the privilege check is process-wide), but worth noting.
- Burst timing is still subject to OS scheduling — "simultaneous" is
  best-effort.
