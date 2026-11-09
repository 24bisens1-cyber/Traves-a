from __future__ import annotations

from services.env_config import load_env_file


def test_env_file_loads_only_missing_values_and_supports_comments(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYPULSEX_TEST_EXISTING", "from-shell")
    source = tmp_path / ".env"
    source.write_text(
        "# comment\n"
        "export CITYPULSEX_TEST_NEW=from-file\n"
        "CITYPULSEX_TEST_QUOTED=\"value with spaces # kept\"\n"
        "CITYPULSEX_TEST_EXISTING=ignored-file-value\n"
        "INVALID KEY=nope\n"
        "CITYPULSEX_TEST_COMMENT=value # comment\n",
        encoding="utf-8",
    )
    loaded = load_env_file(source)
    assert loaded == {"CITYPULSEX_TEST_NEW", "CITYPULSEX_TEST_QUOTED", "CITYPULSEX_TEST_COMMENT"}
    assert __import__("os").environ["CITYPULSEX_TEST_NEW"] == "from-file"
    assert __import__("os").environ["CITYPULSEX_TEST_QUOTED"] == "value with spaces # kept"
    assert __import__("os").environ["CITYPULSEX_TEST_EXISTING"] == "from-shell"
    assert __import__("os").environ["CITYPULSEX_TEST_COMMENT"] == "value"


def test_missing_env_file_is_a_safe_noop(tmp_path):
    assert load_env_file(tmp_path / "missing.env") == set()
