"""Async ICMP reply counter — correlates echo replies to atomic ops by
ICMP id. Must be started before the burst so it catches replies that
arrive essentially concurrently with the send."""
import sys
import time

from scapy.all import AsyncSniffer, ICMP, IP


class ReplySniffer:
    def __init__(self, ops, iface=None, debug=False):
        self.ops = ops
        self.id_to_op = {op.icmp_id: op.op_idx for op in ops}
        self.counts = {op.op_idx: 0 for op in ops}
        self.iface = iface
        self.debug = debug
        self.total_icmp_seen = 0
        self._sniffer = None

    def _prn(self, pkt):
        if not pkt.haslayer(ICMP) or not pkt.haslayer(IP):
            return
        self.total_icmp_seen += 1
        if self.debug:
            print(
                f"[sniff] src={pkt[IP].src} dst={pkt[IP].dst} "
                f"type={pkt[ICMP].type} id={pkt[ICMP].id} seq={pkt[ICMP].seq}",
                file=sys.stderr,
            )
        if pkt[ICMP].type != 0:
            return
        op_idx = self.id_to_op.get(pkt[ICMP].id)
        if op_idx is None:
            return
        self.counts[op_idx] += 1

    def start(self):
        kwargs = dict(filter="icmp", prn=self._prn, store=0)
        if self.iface is not None:
            kwargs["iface"] = self.iface
        self._sniffer = AsyncSniffer(**kwargs)
        self._sniffer.start()
        # give libpcap time to attach before the burst starts
        time.sleep(0.6)

    def stop(self, drain=1.5):
        # drain in-flight replies before tearing the sniffer down
        time.sleep(drain)
        if self._sniffer is None:
            return
        try:
            self._sniffer.stop()
        except Exception:
            # sniffer never finished attaching (e.g. perms) — nothing to tear down
            pass
