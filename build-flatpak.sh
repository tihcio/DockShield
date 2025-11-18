#!/bin/bash
# Build script for DockShield Flatpak

set -e

APP_ID="com.dockshield.DockShield"
BUILD_DIR="_flatpak_build"
REPO_DIR="_flatpak_repo"

echo "========================================="
echo "DockShield Flatpak Build Script"
echo "========================================="
echo ""

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "Error: flatpak-builder is not installed"
    echo ""
    echo "On Fedora, install with:"
    echo "  sudo dnf install flatpak-builder"
    echo ""
    echo "On Ubuntu/Debian, install with:"
    echo "  sudo apt install flatpak-builder"
    echo ""
    exit 1
fi

# Check if KDE runtime is installed
if ! flatpak list --user --runtime | grep -q "org.kde.Platform.*6.6"; then
    echo "Installing required KDE runtime and SDK..."
    flatpak install --user -y flathub org.kde.Platform//6.6 org.kde.Sdk//6.6
fi

# Check if PyQt base app is installed
if ! flatpak list --user | grep -q "com.riverbankcomputing.PyQt.BaseApp"; then
    echo "Installing required PyQt6 base app..."
    flatpak install --user -y flathub com.riverbankcomputing.PyQt.BaseApp//6.6
fi

echo ""
echo "Building Flatpak..."
echo ""

# Build the Flatpak
flatpak-builder --force-clean --repo="${REPO_DIR}" "${BUILD_DIR}" "${APP_ID}.yml"

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "========================================="
echo ""
echo "To install locally, run:"
echo "  flatpak install --user ${REPO_DIR} ${APP_ID}"
echo ""
echo "To run the app after installation:"
echo "  flatpak run ${APP_ID}"
echo ""
echo "To create a bundle for distribution:"
echo "  flatpak build-bundle ${REPO_DIR} dockshield.flatpak ${APP_ID}"
echo ""
