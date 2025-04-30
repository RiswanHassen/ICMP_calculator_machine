# ICMP Calc Machine

Dieses Projekt demonstriert eine kreative Anwendung von ICMP Echo Requests als verteilte Rechenmaschine. Es nutzt Standard-Netzwerkverhalten (Ping) zur Ausführung einfacher Additionen, ohne dass die Remote-Hosts selbst Rechenlogik enthalten.

## Prinzip
- Komplexe Rechenoperationen werden lokal in einstellige Additionen zerlegt.
- Für jede Addition `n1 + n2` werden `n1` und `n2` ICMP-Pakete an einen bestimmten Host gesendet.
- Die Anzahl der erhaltenen Antworten entspricht dem Ergebnis.
- Das Ergebnis wird weiterverarbeitet, bis die gesamte Operation aufgelöst ist.

## Projektstruktur
- `main.py` – Einstiegspunkt
- `core/` – ICMP-Kommunikation (Senden & Empfangen)
- `logic/` – Platz für spätere Rechenlogik & Parser
- `test/` – Unit-Tests (optional)

## Verwendung
```bash
python main.py
```
