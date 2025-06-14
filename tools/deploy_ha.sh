#!/bin/bash

# TRMNL Weather Station - Home Assistant Development Deploy Script
# Syncs the custom component to Home Assistant config directory

set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/custom_components/trmnl_weather_station"
TARGET_DIR="/Volumes/config/custom_components/trmnl_weather_station"

echo "Deploying TRMNL Weather Station to Home Assistant..."
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Check if target volume is mounted
if [ ! -d "/Volumes/config" ]; then
    echo "Error: Home Assistant config volume not mounted at /Volumes/config"
    echo "Please mount your Home Assistant config directory first"
    exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Sync the files
echo "Syncing files..."
rsync -av --delete --include="*.py" --include="*.json" --exclude="*" "$SOURCE_DIR/" "$TARGET_DIR/"

echo "Deploy completed successfully!"
echo "Restart Home Assistant to load the updated integration"