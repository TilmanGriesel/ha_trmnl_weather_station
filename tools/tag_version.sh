#!/bin/bash

set -e

MANIFEST_FILE="custom_components/trmnl_weather_station/manifest.json"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

NEW_VERSION="$1"

if [[ ! "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in semantic versioning format (e.g., 1.0.0)"
    exit 1
fi

if [ ! -f "$MANIFEST_FILE" ]; then
    echo "Error: $MANIFEST_FILE not found"
    exit 1
fi

echo "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean. Please commit or stash changes first."
    exit 1
fi

echo "Updating version in $MANIFEST_FILE to $NEW_VERSION..."
sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$NEW_VERSION\"/" "$MANIFEST_FILE"
rm "$MANIFEST_FILE.bak"

echo "Committing version bump..."
git add "$MANIFEST_FILE"
git commit -m "chore(release): bump version to $NEW_VERSION"

echo "Creating and pushing tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"
git push origin HEAD
git push origin "v$NEW_VERSION"

echo "Successfully tagged version v$NEW_VERSION and pushed to GitHub!"