"""targets.txt parser — one host per line, blanks and ``#`` comments
are ignored. Line position is the dispatch index used by ``encoding.dispatch``."""
from pathlib import Path


def load_targets(path: str | Path) -> list[str]:
    out: list[str] = []
    with Path(path).open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out
