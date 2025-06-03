# TRMNL Home Assistant Weather Station

Use your **TRMNL** display to monitor **live CO₂ levels and up to four custom weather sensors** from your **Netatmo** or other supported stations.

This lightweight Home Assistant integration delivers your data to the TRMNL E-Ink display via the included plugin, for low-power, glanceable monitoring in your home.


![splash](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/splash.png?raw=true)


## Key Features
While the integration is currently developed and tested with the Netatmo Weather Station, the configuration process lets you mix and match your preferred sensors. It supports a range of common sensor types, including temperature, humidity, pressure, CO₂, wind speed, precipitation, air quality, and more.

![product](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/product.png?raw=true)

If you find Home Assistant Weather Station useful, [leaving a star ⭐](https://github.com/TilmanGriesel/ha_trmnl_weather_station) would be lovely and will help others discover this integration too 🙏.

## Quickstart Guide

> ⚠️ This project is currently under development, so installation is a bit manual for now and the implementation is in subject to change. Full documentation and streamlined setup will follow once it's available in the default HACS repository.


### Step 1: Add custom Integration via HACS

1. Open Home Assistant and navigate to **HACS > Integrations**.
1. Click the three-dot menu (⋮) in the top-right corner and choose **Custom repositories**.
1. Add this repository URL `https://github.com/TilmanGriesel/ha_trmnl_weather_station` as a **"Integration"** type.

### Step 2: Install the TRMNL Recipe

1. Go to https://usetrmnl.com/recipes/46862/install
1. Click `Install`.
1. Search for `Home Assistant Weather Station` in your playlist and click `Edit` on it.
1. Set the `Refresh rate` to `Every 15 mins` or to any value that suits you best.
1. Click on `Advanced Settings` and copy the `Webhook URL` from the bottom of the edit page, you will need it to setup the Home Assistant integration.

### Step 3: Setup Home Assistant Integration
After a restart of Home Assistant, this integration is configurable by via "Add Integration" at "Devices & Services" like any core integration. Select `TRMNL Weather Station` and follow the instructions. The `TRMNL Webhook URL` field is the `Webhook URL` you copied earlier.

![setup_speedrun](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/setup/ha_setup_speedrun.gif?raw=true)

---

### Future Plans

* Publish the integration in the official **HACS** directory.
* Refactor and clean up the codebase, simplifying where possible and expanding configuration options as needed.
* Add automated tests and refactor logic into classes to improve maintainability and structure.
* Expand and dynamically adapt TRMNL display output based on sensor input.

---

Inspired by [trmnl-sensor-push](https://github.com/gitstua/trmnl-sensor-push).
