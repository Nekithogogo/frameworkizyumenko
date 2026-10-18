from storage import load_domains, read_json, save_domains


def test_domains_roundtrip(tmp_path):
    filename = str(tmp_path / "domains.json")
    domains = {1: {"id": 1, "name": "example.ru", "owner": "ООО"}}
    save_domains(filename, domains)
    assert load_domains(filename) == domains


def test_missing_and_broken_files(tmp_path):
    assert read_json(str(tmp_path / "missing.json")) == []
    broken = tmp_path / "broken.json"
    broken.write_text("[{", encoding="utf-8")
    assert read_json(str(broken)) == []
