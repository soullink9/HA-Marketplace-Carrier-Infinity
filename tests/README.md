# Tests

Run everything from the repository root. Each test is a plain Python script, not a pytest suite: it prints what it
checks and exits non-zero if anything failed. These are the commands the Test workflow runs:

```sh
pip install -r tests/requirements.txt
python3 tests/test_integration.py
python3 tests/test_energy_soak.py 3 2
python3 tests/test_release.py
```

| Script | What it checks |
|---|---|
| `test_energy_soak.py` | Long-run simulation of the lifetime electricity meter (sensor.py), against a model of Carrier's cloud |
| `test_integration.py` | Integration test: the whole Home Assistant side (coordinator, climate, sensors, config flow, log filter) against Home Assistant stand-ins (stubs.py) and recorded Carrier data (tests/fixtures) |
| `test_release.py` | The release scripts in `scripts/`: the version check and notes, building and checking the zip, publishing to a fake Gitea server, and working out which releases GitHub still needs |

[CONTRIBUTING.md](../CONTRIBUTING.md#checking-a-change) says which to run for which change, and how long each takes.
The tests stand in for Home Assistant (`stubs.py`), so they can't prove the integration works on a real Home
Assistant: try changes on a real installation too.
