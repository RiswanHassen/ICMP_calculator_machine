def load_targets(path):
    """Read targets.txt: one host per line, blanks and # comments ignored."""
    with open(path) as f:
        out = []
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out
