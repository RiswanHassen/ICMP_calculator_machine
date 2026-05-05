"""Async ICMP reply counter — correlates echo replies to atomic ops by
ICMP id. Must be started before the burst so it catches replies that
arrive essentially concurrently with the send."""
import logging
import time
from typing import Optional, Sequence

from scapy.all import AsyncSniffer, ICMP, IP

from .encoding import AtomicOp

ICMP_ECHO_REPLY = 0
SNIFFER_WARMUP_SEC = 0.6
DEFAULT_DRAIN_SEC = 1.5

_log = logging.getLogger(__name__)


class ReplySniffer:
    def __init__(
        self,
        ops: Sequence[AtomicOp],
        iface: Optional[str] = None,
    ) -> None:
        self.ops = list(ops)
        self.id_to_op: dict[int, int] = {op.icmp_id: op.op_idx for op in ops}
        self.counts: dict[int, int] = {op.op_idx: 0 for op in ops}
        self.iface = iface
        self.total_icmp_seen = 0
        self._sniffer: Optional[AsyncSniffer] = None

    def _prn(self, pkt) -> None:  # scapy Packet — no public type
        if not pkt.haslayer(ICMP) or not pkt.haslayer(IP):
            return
        self.total_icmp_seen += 1
        _log.debug(
            "sniff.packet",
            extra={
                "src": pkt[IP].src,
                "dst": pkt[IP].dst,
                "type": int(pkt[ICMP].type),
                "id": int(pkt[ICMP].id),
                "seq": int(pkt[ICMP].seq),
            },
        )
        if pkt[ICMP].type != ICMP_ECHO_REPLY:
            return
        op_idx = self.id_to_op.get(pkt[ICMP].id)
        if op_idx is None:
            return
        self.counts[op_idx] += 1

    def start(self) -> None:
        kwargs: dict = dict(filter="icmp", prn=self._prn, store=0)
        if self.iface is not None:
            kwargs["iface"] = self.iface
        self._sniffer = AsyncSniffer(**kwargs)
        self._sniffer.start()
        # give libpcap time to attach before the burst starts
        time.sleep(SNIFFER_WARMUP_SEC)

    def stop(self, drain: float = DEFAULT_DRAIN_SEC) -> None:
        # drain in-flight replies before tearing the sniffer down
        time.sleep(drain)
        if self._sniffer is None:
            return
        try:
            self._sniffer.stop()
        except Exception as exc:
            # sniffer never finished attaching (e.g. permissions or libpcap
            # missing) — there is nothing to tear down. Log so a missing
            # privilege isn't silent.
            _log.warning("sniffer.stop_failed", extra={"err": repr(exc)})
