# Contributing to Carrier Infinity (Cloud)

Thanks for helping. This page is for anyone changing the code: where things live, the rules the code keeps, how to
check a change, and how to release one.

## Ground rules

- **Keep it slim.** The integration does one job: a thermostat per zone, outdoor temperature and one electricity
  meter. New entities or options need a good reason.
- **All cloud traffic goes through carrier_api.** The integration never builds its own requests to Carrier.
  [carrier_api](https://github.com/dahlb/carrier_api) knows Carrier's private API and is updated when Carrier changes
  it; the version is pinned in `manifest.json` (see [Updating carrier_api](#updating-carrier_api)).
- **Secrets stay out of the log.** The password and Carrier's tokens must never be logged. `coordinator.py` filters
  the gql library's debug output, and websocket errors are logged as a message only (a traceback can include the
  token, which is part of the websocket address).
- **Never sign in over and over.** A rejected password stops the integration and asks the user (reauth), so a
  wrong password can't lock the Carrier account.
- **The electricity meter only goes up, and its saves keep loading.** Its state is saved by Home Assistant (see
  `extra_restore_state_data` in `sensor.py`). Adding a key is safe; renaming or reshaping one needs a conversion in
  `Electricity.async_added_to_hass` so existing totals carry over. Any change to the meter gets the full 30-year
  simulation before it ships (see below).
- **Entity unique ids never change.** They are `<serial>_<zone id>`, `<serial>_outdoor_temperature` and
  `<serial>_electricity`. Changing one would orphan people's entities, history and Energy dashboard settings.

## Where things live

```
custom_components/carrier_infinity/
  __init__.py      setup and unload of a Carrier account (a config entry)
  const.py         shared constants: domain, refresh interval, timings
  coordinator.py   the cloud connection: 5-minute refresh, websocket, sign-in retry, showing just-written values
  entity.py        the base class: one Home Assistant device per Carrier system
  climate.py       the thermostat for each zone
  sensor.py        outdoor temperature and the lifetime electricity meter
  config_flow.py   the sign-in form and the password-changed form
  translations/    the text shown in the UI
  brand/           the icon (original artwork; its source is docs/images/icon.svg)
tests/
  stubs.py             small stand-ins for Home Assistant (and for carrier_api's network layer)
  test_integration.py  the whole integration against recorded Carrier data
  test_energy_soak.py  years-long simulation of the electricity meter
  test_release.py      the release scripts, publishing against a fake Gitea server
  fixtures/            recorded Carrier responses (from carrier_api's tests; see fixtures/README.md)
  requirements.txt     what the tests need: carrier-api (and ruff)
  README.md            what each test checks
scripts/               the release helpers both release workflows use (see Releasing)
.gitea/workflows/      tests and releases on Gitea, the main copy (no GitHub needed)
.github/workflows/     GitHub's checks (hassfest, the Marketplace's) and its copy of each release
```

The usual places to make a change:

| To change | Look in |
|---|---|
| How a Carrier mode, activity or fan speed shows in Home Assistant | `MODES`, `FANS` and the properties in `climate.py` |
| What happens when a setting is changed from Home Assistant | the `async_set_*` methods in `climate.py` |
| How long a just-written value wins over the cloud, refresh and reconnect timings | `const.py` |
| Sign-in, refresh, websocket handling | `coordinator.py` |
| The forms and their messages | `config_flow.py` and `translations/en.json` |
| The electricity meter | `Electricity` in `sensor.py` (its module docstring explains the approach) |

The [Development](docs/Development.md) page explains how
data flows from Carrier to the entities.

## Checking a change

You need Python 3.14 (what Home Assistant 2026.9 uses). Then:

```sh
pip install -r tests/requirements.txt
```

| Command | Time | When |
|---|---|---|
| `ruff check custom_components tests` and `ruff format custom_components tests` | seconds | every change |
| `python3 tests/test_integration.py` | seconds | every change |
| `python3 tests/test_energy_soak.py` | a few minutes (12 years, 6 seeds, all scenarios, on all cores) | any change to `sensor.py` or `coordinator.py` |
| `python3 tests/test_energy_soak.py 30 6` | longer | before releasing a change to the electricity meter |
| `python3 tests/test_release.py` | seconds | any change to `scripts/` or the release workflows |
| `python3 scripts/build_package.py` | seconds | builds `dist/carrier_infinity.zip` and checks it installs; the workflows run it on every push |

The simulation plays years of a thermostat hour by hour: restarts, crashes, outages of up to 20 months, bad
readings, and Carrier's quirks (a late New Year, a stale or missing "last year" figure, once-a-day updates). It ends
with `N/N runs within bounds`; each run must finish within a few kWh of Carrier's own figures, allowing only for
data that no meter could have seen.

The tests use stand-ins for Home Assistant (`tests/stubs.py`), written to match Home Assistant 2026.9. If Home
Assistant changes an API the integration uses, update the stand-in to match. Gitea's runner checks every push
(`.gitea/workflows/test.yml`: the lint, the tests, a 3-year simulation, building the zip); on GitHub, the same
checks run plus Home Assistant's `hassfest` and the Marketplace's own checks, which come from GitHub and can only run
there. [tests/README.md](tests/README.md) lists what each test checks.

Code style: `ruff` settles formatting and import order (see `pyproject.toml`). Every function and class has a
docstring, and comments say why, not what.

## Documentation

[README.md](README.md) is the front page, and every other page lives in [`docs/`](docs). When a change alters
something a page describes, update that page in the same commit.

## Updating carrier_api

Carrier's API is private and can change. When it does, [carrier_api](https://github.com/dahlb/carrier_api) usually
gets a fix first. A new value Carrier starts sending (a new preset or fan speed, say) also needs a newer carrier_api:
until then the update fails to parse and the entities show unavailable.

1. Change the version in `manifest.json` (`requirements`) and in `tests/requirements.txt`.
2. Read carrier_api's changes for anything the integration uses (the `System`, `Status`, `Config` and `Energy`
   models, the `set_*`/`update_*` methods, the websocket).
3. Run the checks above, including `python3 tests/test_energy_soak.py`.

## Standards for every change

- **Readable over clever.** Write code a newcomer can follow on the first read. Prefer a few plain lines with a named
  variable to a dense one-liner, a nested conditional expression, or a trick that needs a comment to decode.
- **Comment the why.** Every function and class has a docstring. Comments explain why the code does something
  non-obvious (a quirk of the device or service, a Home Assistant rule, a deliberate trade-off), not what each line
  does.
- **Keep names consistent.** Follow the names already used in the integration: the same words for
  the same things, Home Assistant's conventions for entities and config entries, `snake_case` for Python names and
  `camelCase` for JavaScript.
- **Keep the docs in step.** When you change a function, class or behaviour, update its docstring, its comments and the
  pages under `docs/` (and the README) that describe it in the same commit.
- **Keep the tests green.** Every change keeps existing behaviour and passes all of the tests. When you
  fix a bug, add the situation that caused it to the tests so it stays fixed.
- **No new dependencies without approval.** Don't add a third-party library (to a `manifest.json`, a
  `requirements.txt` or CI) without asking in an issue first. This page says what it already depends on and why.

### Test layout

The tests use these names:

```
tests/
  stubs.py                stand-ins for Home Assistant and the libraries the integration uses
  test_integration.py     the real integration against the stand-ins and a fake device or service
  test_<subject>.py       any other checks (test_engine.py, test_blueprint.py, test_live_proxy.py)
  test_<subject>_soak.py  a long simulation: it takes a length as an argument, and CI runs a short one
  fake_<service>.py       a fake device or service, when it's too big to live inside the test
  requirements.txt        what the tests need beyond Python, if they need anything
```

Every `test_*.py` is a plain script, not a pytest suite: run it with `python3` from the repository root, and it
exits non-zero if any check fails.

### The Marketplace

`hacs.json` at the root is the Marketplace's file: the name it lists and the oldest Home Assistant version the
integration works with. Keep that version in step with the README's requirements.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): a type, an optional scope, then a short summary in
the imperative.

```
feat: add a diagnostics download
fix: keep the last value when the service is briefly unreachable
refactor: split the coordinator's update into steps
docs: explain the safety settings
test: cover a reply with a missing field
chore: update the CI actions
```

## Releasing

Gitea is the main copy of this repository. It push-mirrors to GitHub, which is the public copy: the Marketplace
installs from GitHub's releases, so every link in the docs and release notes points there.

1. Change `version` in `custom_components/carrier_infinity/manifest.json`. Versions go up together: there is only
   this one.
2. Add the release to the top of [CHANGELOG.md](CHANGELOG.md), under a heading `## X.Y.Z (date)` (move what's under
   `## Unreleased` into it). The tests fail if the manifest and the newest changelog section disagree.
3. Run the checks above.
4. Commit and push to Gitea, then publish with Gitea's **Release** workflow (`.gitea/workflows/release.yml`),
   either way:
   - **Actions → Release → Run workflow**, and enter the version without the `v` (for example `1.2.1`). It
     creates the tag `v1.2.1` on the commit it releases.
   - or push a version tag: `git tag v1.2.1 && git push origin v1.2.1`.

   The workflow checks the version matches the manifest and `CHANGELOG.md` (`scripts/release_notes.py`), runs every
   check, builds `carrier_infinity.zip` and checks it installs as `custom_components/carrier_infinity/`
   (`scripts/build_package.py`), and publishes the release on Gitea with the zip and notes: install steps, then that
   version's changelog section (`scripts/publish_gitea_release.py`). A version with a suffix (`-beta`) is published
   as a pre-release. If any check fails, nothing is published. Running it again for the same version updates the
   release and replaces its zip.

5. Gitea's push mirror then sends the commits and the new tag to GitHub, at its next push (every 8 hours). Every push
   from it starts GitHub's own **Release** workflow (`.github/workflows/release.yml`), which publishes each version
   tag that has no GitHub release yet: the same checks, then the same files (the builds are repeatable, byte for
   byte), title and notes, so GitHub's releases match Gitea's. The Marketplace picks it up from GitHub. If GitHub is
   down, the mirror catches up later; the Gitea release is already done. Don't make releases or tags on GitHub
   itself: the mirror deletes tags Gitea doesn't have, and GitHub follows Gitea on its own.

The Gitea workflows use no actions (`actions/checkout` and the like download from GitHub): each job runs in a plain
image from Docker Hub (`python:3.14-bookworm`) and fetches the code from Gitea with git, so testing and releasing
keep working when GitHub can't be reached. The tests' packages still come from PyPI. When the runner's jobs can't
reach Gitea at its public address (a runner on the same Docker network as Gitea, say), set an Actions variable
`GITEA_INTERNAL_URL` to the address they can reach (`http://gitea-server:3000`); both workflows and the publish
script use it.

Keep every tag on Gitea: the push mirror makes GitHub's tags match Gitea's, so a tag missing from Gitea is deleted on
GitHub, and the GitHub release on it turns into a draft.

## Reporting bugs

[Open an issue](https://github.com/soullink9/HA-Marketplace-Carrier-Infinity/issues/new/choose) with your Home Assistant
version, the integration's version, your thermostat's model and software version, what you did and what you expected.
A debug log helps: on the integration's page choose **Enable debug logging**, reproduce the problem, then **Disable
debug logging** to download it. It contains your thermostat's serial number, so check it before posting.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).
