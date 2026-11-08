import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("batch", Path(__file__).parent.parent / "scripts" / "batch.py")
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def result(condition, seed, team, ok=True):
    return {"condition": condition, "seed": seed, "dir": f"{condition}-seed{seed}", "ok": ok,
            **({"team": team, "lowest": team / 4, "most_targeted_share": 0.5, "events": {"passed a bug to": 2}} if ok else {})}


def test_a_batch_of_one_summarises():
    summary, text = batch.summarise([result("rue", 0, 30)], ["rue"])
    assert summary["conditions"]["rue"]["runs"] == 1 and summary["conditions"]["rue"]["team_sd"] == 0.0
    assert summary["pairs"] == {} and "| rue | 1 |" in text


def test_paired_differences_use_only_complete_pairs():
    results = [result("rue", 0, 30), result("off", 0, 36), result("rue", 1, 32), result("off", 1, 34),
               result("rue", 2, 20), result("off", 2, 0, ok=False)]
    summary, text = batch.summarise(results, ["rue", "off"])
    pair = summary["pairs"]["off - rue"]
    assert pair["pairs"] == 2 and pair["diffs"] == [6, 2] and pair["higher"] == 2
    assert pair["ci95"][0] <= 4 <= pair["ci95"][1]
    assert summary["failed"] == ["off-seed2"] and "Failed Runs" in text


def test_measure_reads_a_run_directory(tmp_path):
    (tmp_path / "rounds.jsonl").write_text('{"round": 1, "scores": {"a": 9, "b": 7}}\n')
    (tmp_path / "events.jsonl").write_text('{"round": 1, "events": [{"kind": "passed a bug to", "target": "b"}, '
                                           '{"kind": "passed a bug to", "target": "b"}]}\n')
    m = batch.measure(tmp_path)
    assert m == {"scores": {"a": 9, "b": 7}, "team": 16, "lowest": 7,
                 "events": {"passed a bug to": 2}, "most_targeted_share": 1.0}


def test_condition_settings_become_play_flags():
    assert batch.flags({"social": "off", "situations": ["office-history", "bob-defects"],
                        "choosers": {"bob": "claude-haiku"}, "rounds": None}) == [
        "--social", "off", "--situations", "office-history,bob-defects", "--choosers", "bob=claude-haiku"]
    assert batch.flags({"situations": []}) == ["--situations", ""]  # the neutral start


def test_checked_in_experiments_name_known_settings_and_situations():
    import tomllib
    paths = sorted(Path("experiments").glob("*.toml"))
    assert paths
    for path in paths:
        data = tomllib.loads(path.read_text())
        assert Path(data["config"]).exists()
        for name, settings in data["conditions"].items():
            assert set(settings) <= batch.CONDITION_KEYS, (path, name)
            for situation in settings.get("situations", []):
                assert Path("situations", f"{situation}.toml").exists(), (path, name, situation)
