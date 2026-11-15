# Changelog

## 1.3.0 (2026-11-15)

Built for Home Assistant 2026.11 only.

### Integration

- **Needs Home Assistant 2026.11 or newer.** The Marketplace won't offer this release to older versions; stay on
  1.2.1 until you update Home Assistant.
- The thermostats use Home Assistant 2026.11's new temperature names (`native_temperature_unit`,
  `native_current_temperature`, `native_target_temperature` and its low/high pair). On 2026.11, 1.2.1 logged a
  deprecation warning for each of them at every start, and the old names stop working in 2027.11. Nothing changes
  in what the thermostats show or do: Home Assistant still converts to your units as before.
- Setting up and unloading follow Home Assistant 2026.11's pattern: they return nothing and raise on failure, so
  if the entities ever fail to unload, Home Assistant says why instead of only marking the entry as failed.

### Repository

- `hacs.json` asks for Home Assistant 2026.11.0, and the README and installation guide say so.
- The test stand-ins match Home Assistant 2026.11, and fail if the thermostat goes back to a deprecated name.
- Ruff targets Python 3.14 (what Home Assistant 2026.11 runs on), so it formats for 3.14's syntax.
- CONTRIBUTING.md: the integration tracks the latest Home Assistant release only, with no code kept for older ones.

## 1.2.1 (2026-11-15)

### Integration

- Uses carrier-api 3.8.0 (was 3.6.2). Signing in again after a session expires now goes through Carrier's own
  service, so it works for accounts that sign in with Microsoft as well as Okta, and parallel requests no longer
  refresh the same token twice. Changes to a zone's activities pushed over the live connection now update the right
  activity (3.6.2 could merge them into the wrong one). Nothing changes in how the integration is set up or used.

### Repository

- Gitea is the main copy: its runner checks every push and publishes releases (`.gitea/workflows/`), with nothing
  downloaded from GitHub, so it keeps working when GitHub can't be reached. Gitea push-mirrors to GitHub, and every
  push from it publishes on GitHub the releases GitHub doesn't have yet, with the same files and notes, where the
  Marketplace installs from.
- The release helpers live in `scripts/` and are used by both: the version check and notes, building the zip, and
  publishing on Gitea. Every release's notes now start with how to install it.
- The release's zip is now always `carrier_infinity.zip` (it had the version in its name), so
  `.../releases/latest/download/carrier_infinity.zip` always gets the newest. Each zip is checked before it's published.
- The test that the manifest's version matches the changelog skips `## Unreleased` and reads the newest released
  version, so changes can wait under Unreleased without failing the tests.

## 1.2.0 (2026-11-04)

- Moved to its own repository, [HA-Marketplace-Carrier-Infinity](https://github.com/soullink9/HA-Marketplace-Carrier-Infinity), so it can be installed and updated
  from the Home Assistant Marketplace (Home Assistant 2026.11 and newer). Installing by hand works as before.
- Lists its categories, so it shows up in the right place when browsing the Marketplace. No other changes to how
  the integration works.

## 1.1.1 (2026-11-02)

- No changes to the integration.

## 1.1.0 (2026-11-01)

- No changes to the integration.

## 1.0.2 (2026-11-01)

- A new icon: original artwork of a thermostat, in place of the Carrier logo. The logo images are removed, so
  Home Assistant shows the icon where a logo would go.

## 1.0.0 (2026-11-01)

Initial release.

- A thermostat (climate entity) for every zone: heat, cool, heat/cool, fan only and off; setpoints; fan speed;
  Carrier's activities (home, away, sleep, wake, manual, vacation) as presets, plus "Resume schedule".
- Changing the temperature holds the zone on its manual activity, like the wall control.
- Changes appear in Home Assistant straight away, even while Carrier's cloud is still catching up.
- Changes made on the wall control or in the Carrier app arrive within seconds over Carrier's live connection.
- An outdoor temperature sensor, and one lifetime electricity meter for the whole system that never resets
  (ready for the Energy dashboard).
- Setup and password changes are all in the UI.
