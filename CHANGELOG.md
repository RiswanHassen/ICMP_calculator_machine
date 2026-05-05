# Changelog

All notable changes are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `CLAUDE.md` — primary architecture and rules reference.
- `CHANGELOG.md`, `.gitignore`.
- `core/errors.py` — `ErrorCode` enum for machine-readable failure modes.
- `core/log.py` — stdlib JSON logger with per-run `run_id`.
- `tests/` with pytest coverage for `encoding` and `targets` modules.
- `docs/adr/` with ADRs for ALU model, burst architecture, and loopback limit.
- Type hints across `icmp_calc.py` and `core/*`.

### Changed
- Project layout flattened: code promoted from `icmp_calc_machine_full/` to repo root.
- `core/icmp_sniff.py` → `core/sniff.py`.
- `print()` calls replaced with structured logging; user-facing CLI plan/result
  output kept as `print()` (UI, not log).
- Final log line is `RUN_OK` or `RUN_FAIL <code>` for log-scan diagnosis.

## [0.2.0] — 2026-05-05

### Added
- Distributed ALU model: hosts as compute units, atomic ops dispatched by
  index modulo `len(targets)`.
- `core/burst.py` — parallel sender, one thread per atomic op, synchronized
  start via `threading.Barrier`, dedicated `conf.L3socket()` per thread.
- `core/encoding.py` — `decompose` / `dispatch` / `decode` for `add`, `sub`, `mul`.
- Per-op ICMP id correlation in `ReplySniffer`.
- `--debug` flag for per-packet sniff trace.
- `--drain SECONDS` flag for late-reply wait window.

### Removed
- Legacy single-host `main.py` and `core/icmp_send.py`.
- Inner `README.md` redirect.

## [0.1.0] — initial

### Added
- Single-host CLI sketch (`main.py` with interactive `input()` prompts).
- Sequential ICMP sender, blocking sniffer (`count_icmp_replies`).
