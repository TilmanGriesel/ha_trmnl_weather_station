# TRMNL Home Assistant Weather Station

Use your **TRMNL** display to monitor **live CO₂ levels and up to four custom weather sensors** from your **Netatmo** or other supported stations.

This lightweight Home Assistant integration delivers your data to the TRMNL E-Ink display via the included plugin, for low-power, glanceable monitoring in your home.

## What It Does
Send live sensor data (like CO2, temperature, humidity, and more) to a TRMNL E-Ink display. Works with Netatmo and other Home Assistant-compatible devices. Simple manual install steps included.

## Features
- Prominent CO2 gauge and up to 4 extra sensors
- Compatible with temperature, humidity, pressure, CO2, wind speed, precipitation, air quality
- Custom labels
- Plugin included

If you find Home Assistant Weather Station useful, [leaving a star](https://github.com/TilmanGriesel/ha_trmnl_weather_station) would be lovely and will help others discover this integration too.

![product](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/product.png?raw=true)

## Quickstart Guide

> ⚠️ This project is currently under development, so installation is a bit manual for now and the implementation is in subject to change. Full documentation and streamlined setup will follow once it's available in the default HACS repository.


### Step 1: Add custom Integration via HACS

1. Open Home Assistant and navigate to **HACS > Integrations**.
1. Click the three-dot menu (⋮) in the top-right corner and choose **Custom repositories**.
1. Add this repository URL `https://github.com/TilmanGriesel/ha_trmnl_weather_station` as a **"Integration"** type.

### Step 2: Install the TRMNL Recipe

1. **Visit:** https://usetrmnl.com/recipes/46862/install
2. Click `Install` to add the **Home Assistant Weather Station** recipe to your playlist.
3. Once installed, go to your TRMNL playlist and locate **Home Assistant Weather Station**.
4. Click `Edit` on the recipe.
6. Click on `Advanced Settings` at the bottom of the edit page.
7. Copy the `Webhook URL` you’ll need this to complete the Home Assistant integration.

#### Want to Customize the TRMNL Recipe?

* If you want to **change the look or behavior** of the recipe (e.g., adjust refresh rate, tweak appearance), click `Fork` instead of `Install`.
* Forked Recipes **do not receive automatic updates**, but they allow full customization.
* Installed Recipes are **read-only**, receive automatic improvements, and are easier to manage for non-technical users.

> Recommended: **Install** for most users.
> Advanced: **Fork** if you want full control or anticipate needing edits.

### Step 3: Setup Home Assistant Integration
After a restart of Home Assistant, this integration is configurable by via "Add Integration" at "Devices & Services" like any core integration. Select `TRMNL Weather Station` and follow the instructions. The `TRMNL Webhook URL` field is the `Webhook URL` you copied earlier.

![setup_speedrun](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/setup/ha_setup_speedrun.gif?raw=true)

---

### Future Plans

* Publish the integration in the official **HACS** repository.
  * HA Brand MR: https://github.com/home-assistant/brands/pull/7185
  * HACS Default MR (closed): https://github.com/hacs/default/pull/3512 
* Refactor and clean up the codebase, simplifying where possible and expanding configuration options as needed.
* Add automated tests and refactor logic into classes to improve maintainability and structure.
* Expand and dynamically adapt TRMNL display output based on sensor input.

---

Inspired by [trmnl-sensor-push](https://github.com/gitstua/trmnl-sensor-push).
