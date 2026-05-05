# CLAUDE.md — ICMP Calculator Machine

> Diese Datei ist die primäre Architektur- und Regelreferenz für dieses Projekt.
> Claude Code lädt sie zu Beginn jeder Session. Wenn du eine Konvention änderst,
> aktualisiere diese Datei im selben Commit — keine Doku-Drift.

## Projekt in einem Satz

**ICMP Calculator Machine** ist ein Security-Research-PoC, der Arithmetik realisiert, indem Operanden als ICMP-Echo-Request-Bursts kodiert, an Remote-Hosts (ALU-Einheiten) dispatcht und Ergebnisse aus den Echo-Reply-Counts decodiert werden — Internet als Compute-Substrat, ICMP als covert Compute-Channel.

**Inhaber:** Riswan Hassen (riswanhassen@proton.me)
**Status:** v0.2.0 — distributed ALU-Implementierung lauffähig (encoding, burst, sniff, decode).
**Kommunikation:** Deutsch in Konversation und Doku, Code/Identifier/Commit-Messages auf Englisch.

## Was es ist — und was nicht

**Es ist:**
- Demonstration einer Covert-Channel-Primitive: Berechnung über das Reply-Verhalten eines Diagnose-Protokolls.
- Lehr-PoC für Computer-Architektur-Metaphern auf Netzwerk-Ebene (ALU-Dispatch, Result Register, Instruction Burst).

**Es ist NICHT:**
- Keine produktive Recheneinheit — Reply-Counts sind durch Packet-Loss, ICMP-Rate-Limits und Host-Filterung systematisch unzuverlässig.
- Kein Datentransport-Tool — die einzige Output-Modalität sind aggregierte Reply-Zähler, kein Bandbreitenkanal.
- Kein Network-Scanner und kein Mass-Pinger — Ziele kommen aus einer expliziten `targets.txt`, nicht aus Discovery.
- Kein Werkzeug für unauthorisierte Operationen — gegen fremde Hosts ohne Erlaubnis nicht einsetzen.

Wenn ein Feature dieser Grenze widerspricht: stoppen und nachfragen, nicht stillschweigend integrieren.

---

## Tech Stack

| Bereich | Tool |
|---|---|
| Sprache | Python 3.12+ |
| Package Manager | pip / venv (keine Lock-Datei nötig — eine Laufzeit-Dependency) |
| Lint + Format | ruff (geplant) |
| Type Check | mypy (geplant, Type-Hints im Code vorhanden) |
| Tests | pytest |
| Datenbank | keine |
| Frontend | keine — CLI |
| Deployment | manuell (`sudo python3 icmp_calc.py ...`) |
| Laufzeit-Dependency | `scapy` (raw socket I/O, AsyncSniffer) |

---

## Projektstruktur

```
ICMP_calculator_machine/
├── CLAUDE.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── icmp_calc.py            # CLI entry
├── targets.txt             # numbered ALU list
├── core/                   # internal module
│   ├── __init__.py
│   ├── encoding.py         # decompose / dispatch / decode (pure)
│   ├── burst.py            # parallel sender (threads + Barrier)
│   ├── sniff.py            # AsyncSniffer wrapper, per-op id correlation
│   ├── targets.py          # targets.txt parser
│   ├── errors.py           # ErrorCode enum
│   └── log.py              # stdlib JSON logger + run_id
├── tests/
│   ├── test_encoding.py
│   └── test_targets.py
└── docs/
    └── adr/
        ├── 0001-distributed-alu-model.md
        ├── 0002-burst-with-barrier.md
        └── 0003-loopback-not-supported.md
```

> Keine Sammelordner (`utils/`, `helpers/`, `misc/`). `core/` ist die *eine* Modulgrenze — nicht "alles was nicht der Entry ist", sondern die Compute-/I/O-Bibliothek hinter dem CLI.

---

## Architektur-Prinzipien

- **Pure Functions im Core, Side Effects an der Boundary:** `encoding.py` ist seiteneffekt-frei und trivial testbar. `burst.py` / `sniff.py` sind die Boundary zur Netzwerk-I/O.
- **Eine Stelle für Schema-Interpretation:** `targets.txt`-Parsing lebt nur in `core/targets.py`, das Operations-Mapping nur in `core/encoding.py`. Wer eine Operation hinzufügt, ändert *eine* Datei.
- **Plugin-Erweiterung über Encoding-Modul:** Neue Operation = neuer Eintrag in `decompose` + `decode` + `expected` + `SUPPORTED`-Tuple, keine Änderung an Burst/Sniff.
- **Klassen nur für State.** `AtomicOp` (dataclass), `ReplySniffer` (hält Sniffer-Thread + Counts) — sonst Funktionen.
- **Dependency Injection an testbaren Pfaden:** `dispatch` bekommt `targets` und `id_pool` als Parameter, kein global-RNG-Aufruf im Core.
- **Eleganz durch Reduktion:** `decode` für `add`/`mul` ist `sum`. Wenn das nicht mehr stimmt, ist die Operation in der falschen Schicht modelliert.

---

## Code-Standards

- **Type Hints** an jeder public Funktion. mypy-strict-konform soll laufen, sobald die Konfig steht.
- **Naming:** `snake_case` Funktionen/Variablen, `PascalCase` Klassen, `UPPER_SNAKE_CASE` Konstanten.
- **Keine Magic Numbers** — `ICMP_ECHO_REPLY = 0`, `ICMP_ID_MAX = 0x10000`, `DEFAULT_DRAIN_SEC = 1.5` als Modulkonstanten.
- **Keine hardcoded Pfade** — `pathlib.Path` für Targets-Datei und alle File-I/O-Pfade.
- **String-Templating** via f-Strings.
- **Keine stillen Fehler** — `except Exception: pass` ist verboten. Wenn ein Sniffer-Teardown fehlschlägt (kann bei Permission-Issue passieren), wird mit Begründung im Kommentar geschwiegen *und* es wird auf WARN geloggt.
- **Kein `print()`** — `core.log.get_logger(__name__)`. Ausnahme: bewusst das CLI-User-Interface (sichtbare Plan-Anzeige, finale Result-Zeile) — das ist UI, kein Logging.
- **Kommentare:** das *warum*. Nicht "set id=icmp_id".

---

## Testing

- **Test-Framework:** pytest.
- **Unit-Tests** für reine Logik (`encoding.py`, `targets.py`) — hier muss Coverage hoch sein, weil das die einzige verlässliche Komponente im PoC ist.
- **Keine Mocks für scapy** — die Boundary-Module (`burst.py`, `sniff.py`) sind so dünn, dass ein Mock mehr Aufwand wäre als der getestete Code. Verifikation: Live-Run mit Konsistenzcheck `replies == expected`.
- **Integration-Test (`@pytest.mark.live`)** ist explizit *nicht* eingerichtet — würde sudo + Internet-Verbindung erfordern und gegen externe Hosts pingen, was scope-fremd ist (PoC-Demo, kein CI-Pflicht).
- **Regression-Fixtures** für Bugs: bisher der "Sniff-vor-Send-Race" — implizit verifiziert durch das `sniffer.start()` vor `burst_send()` im Flow.

```bash
pytest                      # alle Tests
pytest tests/test_encoding.py -v
pytest -k decode
```

---

## Sicherheit

- **Raw Sockets:** das Tool braucht root oder `CAP_NET_RAW`. Das ist im README dokumentiert. Kein Versuch, Privilegien zu erschleichen oder zu droppen.
- **Targets-Validierung** bleibt Aufgabe des Users — wir akzeptieren beliebige Strings als Hosts. Keine DNS-Resolution-Fancy-Logik, keine Reachability-Probes (siehe Don'ts: kein Scanner).
- **Keine Logs sensibler Daten:** ICMP-Payload ist leer (Standard-Echo), wir loggen nur Quell-/Ziel-IPs, IDs, Counts.
- **Keine externe API:** keine TLS-/Auth-/CVE-Themen. Einzige Dependency `scapy` ist via `pip install scapy` aus PyPI — Verifikation per Hash optional.
- **Domain-Allow-List nicht anwendbar** — die "Domain" sind beliebige IPs aus `targets.txt`, vom User explizit gewählt.

### ISO 27xxx-Readiness & Auditierbarkeit (Pflicht)

Auch im PoC gilt das Prinzip — angepasst an die Größe:

- **Audit Trail** über `git log` + strukturiertes Logging (`run_id`, `op`, `targets`, `expected`, `result`, `RUN_OK`/`RUN_FAIL <code>`).
- **Reproduzierbarkeit:** ein Lauf ist vollständig charakterisiert durch (Operation, Operanden, targets.txt, Zeitpunkt). RNG für ICMP-IDs ist nicht reproduzierbar — bewusst, weil Korrelations-Schutz, kein Determinismus-Bedarf.
- **CHANGELOG.md** dokumentiert user-sichtbare Änderungen pro Version.
- **ADRs** in `docs/adr/` für die drei Kern-Designentscheidungen (ALU-Modell, Burst-Architektur, Loopback-Limit).
- **Keine Soft-Deletes / Retention** — kein persistenter State.
- **Kryptografie:** keine.

---

## Datenschutz

- **Keine personenbezogenen Daten** — das Tool verarbeitet IPs und Counts.
- **Keine Telemetrie.**
- **Keine Logs nach extern.**
- **Local-only Output.**

---

## Konfiguration

**Precedence (höchste zuerst):** CLI-Flag → Env-Var → Default.

CLI-Flags:
- `--operation {add,sub,mul}` (required)
- `--a`, `--b` (required, int)
- `--targets PATH` (required)
- `--debug` (Flag, opt-in für per-packet sniff log)
- `--drain SECONDS` (default 1.5)

Env-Vars (für Orchestrator-Aufrufe, optional):
- `ICMPCALC_LOG_LEVEL` — DEBUG/INFO/WARNING/ERROR (default INFO)
- `ICMPCALC_DRAIN_SEC` — Override für `--drain` (CLI gewinnt).

Keine `.env`-Datei nötig. Keine Pydantic-Settings — vier Flags rechtfertigen keine Settings-Klasse (YAGNI).

---

## Logging & Observability

- **Strukturiert:** stdlib `logging` mit JSON-Formatter (`core/log.py`). Keine externe Dependency.
- **Root-Logger einmal konfiguriert** in `core.log.setup(level)`, aufgerufen aus `icmp_calc.main()`.
- **`run_id`** (8-Hex zufällig pro Run) wird via `LoggerAdapter` durchgereicht und in jeder Zeile mitgeloggt.
- **Operationen geloggt:** Plan (Op + Operands + Dispatch), Sniffer-Start, Burst-Start/-End, Per-Op-Counts, Final-Decode.
- **Error-Codes** als Enum (`core/errors.py`): `OK`, `NO_TARGETS`, `RESULT_MISMATCH`, `SNIFFER_ATTACH_FAILED`, `RAW_SOCKET_DENIED`. Codes sind das Auto-Heal-Hook (siehe AI-Readiness).

**Observability-Kriterium (verpflichtend):**

- **`RUN_OK` / `RUN_FAIL <code>` als letzte strukturierte Logzeile** jedes Runs.
- **Plan-Output** (vor Burst) macht den erwarteten Endzustand explizit — wenn er nicht eintritt, ist die Diskrepanz im Log direkt sichtbar.
- **`--debug`** loggt jedes ICMP-Paket, das der Sniffer sieht — primäres Diagnose-Werkzeug bei "0 replies".
- **Heartbeat** entfällt — der Lauf ist kurz (Sekunden). Kein Long-running-Prozess.

---

## AI-Readiness / Self-Healing-Anschluss

**Eiserne Regel** wie im Template — adaptiert an PoC-Größe:

- **Maschinen-lesbare Fehler:** `core/errors.py` definiert Enum-Codes. `RUN_FAIL <code>` ist die finale Logzeile. Ein Self-Healing-Modul scannt Logs nach `RUN_FAIL` und kennt die Code-Bedeutung ohne Stack-Trace-Parsing.
- **Selbst-Diagnose:** `--debug`-Flag liefert per-packet-Trace. Eine `--diagnose`-Subkommando-Erweiterung (Sniffer-Permissions check, Targets-Erreichbarkeit) ist im Code-Design vorgesehen, aber bewusst noch nicht implementiert (YAGNI).
- **Reversibilität:** der PoC ist read-only auf das System (keine Files geändert, kein State persistiert). Reversibel by default.
- **Idempotenz:** zwei Läufe mit gleichen Operanden+Targets liefern (modulo RNG-IDs) das gleiche Ergebnis. Reply-Counts können wegen Netzwerk-Noise variieren — das ist Eigenschaft des PoCs, nicht ein Bug.
- **Action-Risk-Klassifikation:** der Code führt nur A-Stufe aus (Read-only-Diagnostik aus System-Sicht; aus Netzwerk-Sicht: ICMP-Echo-Requests, eskalierbar nach B falls Burst-Größen sehr hoch). Operations-Klassifikation siehe Eskalations-Schema unten.
- **Trennung Diagnose / Plan / Ausführung:** `decompose+dispatch` (Plan), `burst_send` (Ausführung), `sniff.counts → decode` (Diagnose des Ergebnisses). Drei separate Funktionen, kein verschachtelter Try-Block.
- **Audit-Log** über strukturiertes Logging mit `run_id`.
- **Keine impliziten Side Effects.**
- **Public-API stabil:** `core.encoding.{decompose,dispatch,decode,expected}`, `core.burst.burst_send`, `core.sniff.ReplySniffer`, `core.targets.load_targets`. Type-Hints + Docstrings vorhanden.

---

## Plattform-Portabilität

- **Primär-Plattform:** Linux (raw sockets über `AF_INET`/`AF_PACKET`).
- **macOS:** scapy funktioniert, sudo nötig. ICMP-id-Reflection sollte gleich sein.
- **Windows:** scapy braucht Npcap. Loopback-Limitation gilt analog.
- **`pathlib.Path`** für Targets-Pfad.
- **UTF-8 explizit** beim Lesen von `targets.txt`.
- **Concurrency:** `threading` (Barrier + Worker-Threads pro Op). Kein `multiprocessing`.

---

## Git & Commits

- **`main` = lauffähig.** Refactor-Branches optional bei größeren Umbauten.
- **Conventional Commits:** `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- **Eine logische Änderung pro Commit.**
- **`.gitignore` deckt:** `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `*.pcap`, `*.log`.
- **Keine Targets-Listen mit Drittparteien-Hosts im Repo** außer Demo-Werten (8.8.8.8, 1.1.1.1 — Public-DNS).
- **Keine `--no-verify`.**

---

## Lebende Dokumentation

- **`CLAUDE.md`** (diese Datei) — Architektur und Regeln.
- **`README.md`** — Konzept, Modell-Tabelle, Usage, Caveats. Public-facing.
- **`CHANGELOG.md`** — Keep-a-Changelog. Eintrag pro user-sichtbarer Änderung.
- **`docs/adr/`** — ADRs für ALU-Modell, Burst-Architektur, Loopback-Limit.

**Erkenntnis-Regel:** dauerhaft relevante Findings sofort hier — nicht in Commit-Messages versteckt.

---

## Phasen / Roadmap

### Phase 1 — Single-Host-PoC (Status: ✓ done, vor Refactor)
- [x] Lokaler Sender + Sniffer für eine IP

### Phase 2 — Distributed ALU (Status: ✓ done)
- [x] CLI mit argparse, targets.txt-Parser
- [x] Encoding (decompose) + Dispatch + Decode für add/sub/mul
- [x] Burst-Sender mit Barrier, ein Thread pro Op
- [x] AsyncSniffer mit per-op-id-Korrelation
- [x] Live-Verifikation gegen 8.8.8.8 + 1.1.1.1

### Phase 3 — Hardening (Status: in Arbeit)
- [ ] Strukturiertes Logging + Error-Codes
- [ ] Type Hints überall + mypy-strict-config
- [ ] tests/ mit pytest
- [ ] docs/adr/ mit Kern-Entscheidungen
- [ ] CHANGELOG.md

### Phase 4 — optional, nur bei Bedarf
- [ ] `--diagnose`-Subkommando (Permissions, Reachability)
- [ ] CI: ruff + mypy + pytest
- [ ] mehr Operationen (div?, mod? — nur falls didaktisch sinnvoll)

**Definition of Done pro Phase:**
1. Funktion läuft im Standardflow
2. Tests grün (sofern Pure Functions betroffen)
3. CHANGELOG-Eintrag
4. CLAUDE.md aktualisiert falls Konventionen sich verschoben haben

---

## Don'ts

- Kein Reachability-/Discovery-Scanning. Targets sind explizit.
- Kein Datentransport-Channel über die Counts hinaus (kein Multi-Bit-Encoding in seq-Mustern).
- Keine plattform-spezifische Logik im Core — Linux-Spezifika (`iface="lo"`-Fall) sind im CLI gekapselt.
- Keine externen API-Calls / Telemetrie.
- Keine neuen Dependencies ohne Begründung. scapy ist die einzige.
- Kein `--no-verify`, kein Hook-Skip.
- Keine Doku-Drift — Konventions-Änderungen in CLAUDE.md im selben Commit.
- Keine lautlosen Fehler. `RUN_FAIL <code>` ist Pflicht im Fehlerfall.

---

## Regeln für Claude Code

1. **Lies CLAUDE.md zuerst.**
2. **Frag bei Unsicherheit.** Targets-Liste, Operations-Semantik, Network-Fragen.
3. **Plan Mode** für: neue Operationen, neue Module, Schema-/Public-API-Änderungen.
4. **Erkenntnis-Regel:** dauerhaft relevante Findings sofort hier einarbeiten.
5. **Bei Konflikt zwischen Task und CLAUDE.md:** stoppen und melden.

### Eskalations-Schema

| Stufe | Charakter | Beispiele in diesem Projekt | Regel |
|---|---|---|---|
| A — Read-only | Reversibel, kein State-Change | Code lesen, `pytest`, `--debug`-Run | Ohne Rückfrage |
| B — Reversibel, Low-Impact | Lokale Code-Änderungen | Refactor, neue Operation | Sammel-Zustimmung pro Session |
| C — Config/State-Change | Editiert geteilte Konfig | `targets.txt` ändern, `requirements`-Bump | Rückfrage mit Diff |
| D — Irreversibel/High-Impact | Push/Force-Push, große Burst-Counts gegen fremde Hosts | `git push --force`, `mul(1000, 1000)` gegen Public-IP | Vorschlag + Commands, User führt aus |

Im Zweifel eine Stufe höher.

---

## Häufige Befehle

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate && pip install scapy pytest

# Run
sudo -E python3 icmp_calc.py --operation add --a 5 --b 3 --targets targets.txt

# Debug-Lauf (per-packet sniff trace)
sudo -E python3 icmp_calc.py --operation add --a 5 --b 3 --targets targets.txt --debug

# Tests
pytest -v

# Sektionen in CLAUDE.md listen
grep -n "^## " CLAUDE.md
```

---

## Wichtige Hinweise & bekannte Eigenheiten

- **127.0.0.1 funktioniert nicht.** `SOCK_RAW` an loopback umgeht den Kernel-Echo-Reply-Generator (tcpdump zeigt nur type=8, nie type=0). Test gegen erreichbare Hosts über echte NIC. Siehe `docs/adr/0003-loopback-not-supported.md`.
- **Sniffer muss vor dem Burst starten.** `AsyncSniffer.start()` braucht ~0.6s libpcap-Attach-Zeit, sonst werden frühe Replies verpasst. Kein Race im aktuellen Code, aber kritisch beim Refactor.
- **Per-Op-IDs sind 16-bit zufällig** und müssen pro Run unique sein — `random.sample(range(1, 0x10000), n_ops)`. Bei `mul(a, b)` mit b > 65535 läuft `random.sample` aus → bewusste Limitation, im PoC kein Schutzcode.
- **ICMP-Rate-Limits** auf Public-DNS-Servern (8.8.8.8, 1.1.1.1) liegen großzügig — bis ~50 pings/s problemlos. Bei größeren Bursts erst gegen privates Lab testen.
- **Loopback-Sniff zeigt requests doppelt.** Auf `lo` werden Pakete im tx und rx-Pfad sichtbar — irrelevant für unseren Code (wir filtern auf type=0), aber verwirrend im `--debug`-Output.

---

*Last updated: 2026-05-05*
