# Changelog

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
