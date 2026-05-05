"""Parallel burst sender — one thread per atomic op, synchronized by a
threading.Barrier so all pings go on the wire as close to simultaneously
as the OS scheduler allows. Each thread owns its own L3 raw socket to
avoid per-send setup cost and serialization inside scapy."""
import logging
import threading
from typing import Sequence

from scapy.all import IP, ICMP, conf

from .encoding import AtomicOp

_log = logging.getLogger(__name__)


def burst_send(ops: Sequence[AtomicOp]) -> None:
    """Fire all atomic ops in parallel. Blocks until every thread is done."""
    if not ops:
        return
    barrier = threading.Barrier(len(ops))
    threads = [
        threading.Thread(target=_fire, args=(op, barrier), daemon=True) for op in ops
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def _fire(op: AtomicOp, barrier: threading.Barrier) -> None:
    sock = conf.L3socket()
    try:
        barrier.wait()  # synchronize burst start across all threads
        for seq in range(op.count):
            sock.send(IP(dst=op.host) / ICMP(id=op.icmp_id, seq=seq))
    finally:
        try:
            sock.close()
        except OSError as exc:
            # socket teardown may race the kernel; nothing actionable, but
            # surface it on WARN so an operator can correlate odd behavior.
            _log.warning("burst.socket_close_failed", extra={"err": repr(exc)})
