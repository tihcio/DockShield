#!/bin/bash
# Script to build DockShield Flatpak

set -e

echo "======================================"
echo "Building DockShield Flatpak"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    print_error "flatpak-builder is not installed"
    echo ""
    echo "Install it with:"
    echo "  Fedora: sudo dnf install flatpak-builder"
    echo "  Ubuntu: sudo apt install flatpak-builder"
    echo "  Arch: sudo pacman -S flatpak-builder"
    exit 1
fi

print_success "flatpak-builder found"

# Check if required runtimes are installed
echo ""
echo "Checking Flatpak runtimes..."

if ! flatpak info org.kde.Platform//6.6 &> /dev/null; then
    print_warning "KDE Platform runtime not found, installing..."
    flatpak install -y flathub org.kde.Platform//6.6
fi

if ! flatpak info org.kde.Sdk//6.6 &> /dev/null; then
    print_warning "KDE SDK not found, installing..."
    flatpak install -y flathub org.kde.Sdk//6.6
fi

if ! flatpak info com.riverbankcomputing.PyQt.BaseApp//6.6 &> /dev/null; then
    print_warning "PyQt BaseApp not found, installing..."
    flatpak install -y flathub com.riverbankcomputing.PyQt.BaseApp//6.6
fi

print_success "All required runtimes are installed"

# Create build directory
BUILD_DIR="flatpak-build"
REPO_DIR="flatpak-repo"

echo ""
echo "Creating build directories..."
mkdir -p "$BUILD_DIR" "$REPO_DIR"

# Build the Flatpak
echo ""
echo "Building Flatpak package..."
echo "This may take a while on first build..."
echo ""

flatpak-builder \
    --force-clean \
    --repo="$REPO_DIR" \
    --install-deps-from=flathub \
    --ccache \
    "$BUILD_DIR" \
    ../com.dockshield.DockShield.yml

if [ $? -eq 0 ]; then
    print_success "Flatpak built successfully!"
else
    print_error "Build failed!"
    exit 1
fi

# Create bundle for distribution
echo ""
echo "Creating Flatpak bundle..."
flatpak build-bundle \
    "$REPO_DIR" \
    DockShield.flatpak \
    com.dockshield.DockShield

if [ $? -eq 0 ]; then
    print_success "Bundle created: DockShield.flatpak"
else
    print_error "Bundle creation failed!"
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}Build Complete!${NC}"
echo "======================================"
echo ""
echo "To install locally:"
echo "  flatpak install --user $REPO_DIR com.dockshield.DockShield"
echo ""
echo "Or install from bundle:"
echo "  flatpak install --user DockShield.flatpak"
echo ""
echo "To run:"
echo "  flatpak run com.dockshield.DockShield"
echo ""
echo "IMPORTANT: Make sure Docker is installed on the host system"
echo "and your user is in the docker group!"
echo ""
