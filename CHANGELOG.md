# Changelog

## 1.4.1 (2026-11-22)

Fixes from a security review.

### Integration

- Passwords and tokens are now blanked out of log lines (shown as `**REDACTED**`) instead of the whole line being
  dropped, so debug logs keep the rest of what Carrier sent. This covers the gql and carrier_api loggers and the
  integration's own, including a token in the websocket's address or in an error's traceback.
- A websocket message the integration can't read is logged by its type and size, no longer with its whole body.
- New **Download diagnostics** on the integration's page: the config entry and everything Carrier reports for each
  system, with the username, password and tokens redacted. Attach it to bug reports.
- If a change only partly goes through (for example Carrier accepts the new setpoints but refuses the hold), the
  integration now reloads from Carrier straight away, so the thermostat shows what the zone really has.
- Reloading the integration no longer risks adding the log filter a second time.

### Repository

- GitHub workflows pin every action to a commit (actions/checkout v7.0.1, actions/setup-python v7.1.0, hassfest
  2026.11.0, and the HACS action's current main), and each job gets only the permissions it needs: read-only
  everywhere except the job that publishes GitHub releases. Checkouts no longer keep the job's token.
- Gitea releases: a re-run uploads the new file before removing the old one, so a failed upload leaves the release
  with its previous file instead of none.
- New tests for all of the above.

## 1.4.0 (2026-11-20)

### Integration

- Uses carrier-api 3.12.0 (was 3.8.0). When Carrier rejects a request's token before it was due to expire, the
  library now refreshes it and tries the request again by itself, and signs in again with the saved password if the
  refresh is rejected too. A websocket message for a thermostat that isn't on the account is skipped quietly.
- Talks to Carrier's cloud through Home Assistant's shared web session instead of opening one of its own, as Home
  Assistant recommends for integrations. The sign-in check in the setup and password forms does the same.

### Repository

- GitHub workflows use actions/checkout v7 and actions/setup-python v7 (were v5 and v6). Nothing else changes in
  what they run.
- New tests: the coordinator and the sign-in forms pass Home Assistant's shared session to carrier-api, and a
  websocket message for another system leaves the data alone.

## 1.3.1 (2026-11-19)

### Integration

- A one-off failure to reach Carrier's cloud no longer logs an error or makes the thermostats unavailable. When the
  5-minute refresh can't connect (for example "Carrier connection failed during GraphQL operation:
  getInfinitySystems"), it waits 10 seconds and asks once more before giving up.
- If Carrier is still unreachable, the entities go unavailable as before, but the next try comes after 1 minute
  instead of 5, so they come back soon after Carrier does.

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
