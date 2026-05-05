from core.targets import load_targets


def test_load_targets_strips_blanks_and_comments(tmp_path):
    p = tmp_path / "targets.txt"
    p.write_text(
        "# header comment\n"
        "8.8.8.8\n"
        "\n"
        "  1.1.1.1  \n"
        "# another comment\n"
        "9.9.9.9\n",
        encoding="utf-8",
    )
    assert load_targets(p) == ["8.8.8.8", "1.1.1.1", "9.9.9.9"]


def test_load_targets_preserves_order(tmp_path):
    """Order matters — line position is the dispatch index."""
    p = tmp_path / "targets.txt"
    p.write_text("c\na\nb\n", encoding="utf-8")
    assert load_targets(p) == ["c", "a", "b"]


def test_load_targets_empty_file(tmp_path):
    p = tmp_path / "targets.txt"
    p.write_text("", encoding="utf-8")
    assert load_targets(p) == []


def test_load_targets_only_comments(tmp_path):
    p = tmp_path / "targets.txt"
    p.write_text("# only comments\n# nothing here\n", encoding="utf-8")
    assert load_targets(p) == []


def test_load_targets_accepts_path_or_str(tmp_path):
    p = tmp_path / "targets.txt"
    p.write_text("h\n", encoding="utf-8")
    assert load_targets(p) == ["h"]
    assert load_targets(str(p)) == ["h"]
