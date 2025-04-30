from scapy.all import IP, ICMP, send
import time

def send_icmp_requests(dst, count):
    print(f"[+] Sende {count} ICMP Echo Requests an {dst} ...")
    pkt = IP(dst=dst)/ICMP()
    for _ in range(count):
        send(pkt, verbose=0)
        time.sleep(0.05)
