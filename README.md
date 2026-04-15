# ICMP Calculator Machine

**Distributed Arithmetic via Standard ICMP Reply Counts**

A proof-of-concept that performs arithmetic operations by encoding values into ICMP echo request/reply sequences. The result of a calculation is derived from the number of replies received — turning a diagnostic protocol into an unconventional computation channel.

---

## Concept

ICMP is designed for network diagnostics, not data transfer. That's exactly what makes it interesting: most firewalls, IDS/IPS systems, and monitoring tools treat ICMP as benign traffic. This project explores what happens when you repurpose that assumption.

The calculator encodes operands and operations into ping sequences. The "result" emerges from counting replies across distributed nodes. It's impractical for real computation — but it demonstrates a covert channel primitive that has real implications for network security.

## Why This Exists

This is a security research artifact. It illustrates:

- How protocol assumptions create blind spots in network monitoring
- That covert channels can hide in the most mundane traffic
- The gap between what a protocol is *designed* for and what it can *be used* for

## Usage

```bash
python icmp_calc.py --operation "add" --a 5 --b 3 --targets targets.txt
```

Requires raw socket privileges.

## License

See [LICENSE](LICENSE) for details.
