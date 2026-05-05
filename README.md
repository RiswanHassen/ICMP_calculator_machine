# ICMP Calculator Machine

**Distributed Arithmetic via Standard ICMP Reply Counts**

A proof-of-concept that performs arithmetic by turning the internet into a
computer: hosts are the ALUs, ping counts encode operands, and echo-reply
counts form the result register. A diagnostic protocol is repurposed as a
covert computation channel.

---

## Model

| Computer architecture | ICMP calculator           |
|-----------------------|---------------------------|
| ALU                   | remote host               |
| Operand               | ping count                |
| Instruction dispatch  | atomic op → host (i mod N)|
| Execution             | synchronized ping burst   |
| Result register       | per-op echo-reply counts  |

A calculation decomposes into Y atomic ping-emission operations. Each op
is dispatched to one ALU, indexed by its position in `targets.txt`
(wrapping via modulo). All ops fire as a synchronized burst — every
sender thread crosses a `threading.Barrier` and then emits its pings
back-to-back, so they hit their ALUs as close to simultaneously as the
OS scheduler allows. Replies flow back and are correlated per op via a
unique ICMP id, giving a clean per-op reply count regardless of which
host served the op.

```
decompose :  (op, a, b)             → [c_0, ..., c_{Y-1}]
dispatch  :  atomic op i            → targets[i mod N]
execute   :  burst of sync'd threads → echo replies
decode    :  per-op reply counts    → result
```

## Operations

| op  | decomposition | decoding       |
|-----|---------------|----------------|
| add | `[a, b]`      | sum of replies |
| sub | `[a, b]`      | `r[0] − r[1]`  |
| mul | `[a] × b`     | sum of replies |

## Why this exists

This is a security research artifact. It illustrates:

- How protocol assumptions create blind spots in network monitoring.
- That covert channels can hide in the most mundane traffic.
- The gap between what a protocol is *designed* for and what it can *be used* for.

Firewalls, IDS, and flow monitors typically treat ICMP as benign. A
stream of echo requests fanning out to N hosts, with their replies
re-aggregated into arithmetic, sits well inside that blind spot.

## Usage

```bash
sudo python icmp_calc.py --operation add --a 5 --b 3 --targets targets.txt
```

`targets.txt` is a numbered list of hosts (one per line, `#` for
comments). Line position is the dispatch index.

Flags:

- `--operation {add,sub,mul}`
- `--a`, `--b` — operands
- `--targets` — path to host list
- `--debug` — log every ICMP packet the sniffer observes
- `--drain SECONDS` — wait time after burst for late replies (default 1.5)

Requires raw socket privileges (root or `CAP_NET_RAW`).

Logs are emitted as JSON to stderr; the final line is `RUN_OK` or
`RUN_FAIL <code>` (see `core/errors.py`). Set `ICMPCALC_LOG_LEVEL=DEBUG`
or pass `--debug` for per-packet sniff traces.

## Tests

```bash
pytest -v
```

Pure logic (`core/encoding.py`, `core/targets.py`) is fully covered.
Network paths are verified manually against reachable hosts — see
`docs/adr/0003-loopback-not-supported.md` for why CI integration tests
aren't wired up.

## Project layout

```
icmp_calc.py            # CLI entry
core/                   # encoding, dispatch, burst sender, sniffer, log, errors
tests/                  # pytest, pure-logic coverage
docs/adr/               # design decisions
CLAUDE.md               # architecture and rules reference
CHANGELOG.md            # Keep-a-Changelog
targets.txt             # ALU list (one host per line, # comments)
```

## Caveats

- **127.0.0.1 does not work.** `SOCK_RAW` packets to loopback bypass the
  kernel's echo-reply generator. Test against hosts reachable via a real
  NIC.
- Reply counts are noisy in the wild: packet loss, ICMP rate limits, and
  host filtering under-count replies and silently corrupt the result.
- This is not a reliable computation engine — it is a channel-primitive
  demonstration.

## License

See [LICENSE](LICENSE).
