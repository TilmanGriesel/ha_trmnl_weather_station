# TRMNL Home Assistant Weather Station

Use your **TRMNL** display to monitor **live CO₂ levels and up to six custom sensors** from your **Netatmo** or other supported stations.

This lightweight Home Assistant integration delivers your data to the TRMNL E-Ink display via the included plugin, for low-power, glanceable monitoring in your home.

![product](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/product.png?raw=true)

## What It Does

Send live sensor data (like CO2, temperature, humidity, and more) to a TRMNL E-Ink display. Works with Netatmo and other Home Assistant-compatible devices with a few simple installation steps.

## Features

- Prominent CO2 gauge and up to 6 extra sensors
- Compatible with temperature, humidity, pressure, CO2, wind speed, precipitation, air quality
- Custom labels
- Plugin included

If you find Home Assistant Weather Station useful, [leaving a star](https://github.com/TilmanGriesel/ha_trmnl_weather_station) would be lovely and will help others discover this integration too.

## Quickstart Guide

> ⚠️ This project is currently under development, so installation is a bit manual for now and the implementation is in subject to change. Full documentation and streamlined setup will follow once it's available in the default HACS repository.

### Step 1: Add custom Integration via HACS

1. Open Home Assistant and navigate to **HACS > Integrations**.
1. Click the three-dot menu (⋮) in the top-right corner and choose **Custom repositories**.
1. Add this repository URL `https://github.com/TilmanGriesel/ha_trmnl_weather_station` as a **"Integration"** type.

### Step 2: Fork Recipe to Your TRMNL Playlist

1. **Visit:** https://usetrmnl.com/recipes/46862/install
1. Click `Fork` to add it to your **TRMNL playlist**.
1. Go to your **TRMNL playlist** and locate **Home Assistant Weather Station**.
1. Click `Edit` on the **Home Assistant Weather Station** settings icon.
1. Set the `refresh rate` to **15 minutes** (or whatever suits you best).
1. **Copy** the `Webhook URL`, **you'll need this to complete** the Home Assistant integration.

### Step 3: Setup Home Assistant Integration

After a restart of Home Assistant, this integration is configurable by via "Add Integration" at "Devices & Services" like any core integration. Select `TRMNL Weather Station` and follow the instructions. The `TRMNL Webhook URL` field is the `Webhook URL` you copied earlier.

![product dark](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/product_dark.png?raw=true)

## Why I am doing this
I’ve always believed in sharing, especially when it comes to knowledge and skills. Whether you're a professional or a hobbyist, I think we build stronger, more sustainable communities when we openly share what we create and support each other in return. A few years ago, I built a Home Assistant e-ink display to show sensor data. It worked well, but setting it up meant flashing a microcontroller and this is not exactly beginner-friendly and thus exclude many people from technological freedom. Back then, I really wished there was an easier way for others to do the same without diving deep into technical setup and even considered starting an open source project but then life happened.

And that’s why I think TRMNL is such a great solution. It makes it simple to display sensor data with minimal setup, saving a lot of time and effort for anyone looking to do the same. It lowers the barrier and makes home automation more accessible. What’s even better is that it’s open-source. So even if the company behind it stops supporting the product, the community can keep it going. That means it’s not just another piece of tech destined for the junk drawer, it's something people can continue to build on.

Feel free to checkout my other little projects:
- https://github.com/TilmanGriesel/graphite - A Calm and Clean Theme for Home Assistant
- https://github.com/TilmanGriesel/chipper - Small AI interface for tinkerers (Ollama, RAG, Python)

---

### Home Assistant Setup Demo
**Note:** This recording is from version 0.3 and slightly outdated. The current configuration is simpler and more flexible.

![setup_speedrun](https://github.com/TilmanGriesel/ha_trmnl_weather_station/blob/main/docs/setup/ha_setup_speedrun.gif?raw=true)

---

### Future Plans

- Publish the integration in the official **HACS** repository.
  - HA Brand MR: https://github.com/home-assistant/brands/pull/7185
  - HACS Default MR (closed): https://github.com/hacs/default/pull/3512
- Refactor and clean up the codebase, simplifying where possible and expanding configuration options as needed.
- Add automated tests and refactor logic into classes to improve maintainability and structure.
- Expand and dynamically adapt TRMNL display output based on sensor input.

---

Inspired by [trmnl-sensor-push](https://github.com/gitstua/trmnl-sensor-push).
