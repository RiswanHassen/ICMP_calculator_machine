from scapy.all import IP, ICMP, sniff

def count_icmp_replies(src, timeout=3):
    replies = []

    def handle(pkt):
        if pkt.haslayer(ICMP) and pkt[IP].src == src and pkt[ICMP].type == 0:
            replies.append(pkt)

    print(f"[+] Warte auf ICMP Echo Replies von {src} ...")
    sniff(filter=f"icmp and src host {src}", timeout=timeout, prn=handle, store=0)
    print(f"[+] Empfangen: {len(replies)} Replies")
    return len(replies)
