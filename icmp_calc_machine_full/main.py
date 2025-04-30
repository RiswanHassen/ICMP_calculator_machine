from core.icmp_send import send_icmp_requests
from core.icmp_sniff import count_icmp_replies

if __name__ == "__main__":
    target = input("Ziel-IP: ").strip()
    amount = int(input("Anzahl Requests: ").strip())
    send_icmp_requests(target, amount)
    result = count_icmp_replies(target)
    print(f"[=] Ergebnis (Antwortanzahl): {result}")
