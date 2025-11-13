#!/bin/bash
# DockShield Uninstallation Script

set -e

echo "========================================"
echo "DockShield Uninstallation Script"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to ask yes/no question
ask_yes_no() {
    local prompt="$1"
    local default="${2:-n}"

    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n] "
    else
        prompt="$prompt [y/N] "
    fi

    read -p "$prompt" response
    response=${response:-$default}

    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Detect installation method
INSTALLED_METHOD="none"

if flatpak list --app | grep -q "com.dockshield.DockShield"; then
    INSTALLED_METHOD="flatpak"
elif pip show dockshield &> /dev/null || pip3 show dockshield &> /dev/null; then
    INSTALLED_METHOD="pip"
fi

echo "Detected installation method: $INSTALLED_METHOD"
echo ""

# Uninstall application
if [ "$INSTALLED_METHOD" = "flatpak" ]; then
    print_info "Uninstalling Flatpak package..."

    if ask_yes_no "Uninstall DockShield Flatpak application?" "y"; then
        flatpak uninstall -y com.dockshield.DockShield
        print_success "Flatpak application uninstalled"
    fi

elif [ "$INSTALLED_METHOD" = "pip" ]; then
    print_info "Uninstalling Python package..."

    if ask_yes_no "Uninstall DockShield Python package?" "y"; then
        pip uninstall -y dockshield || pip3 uninstall -y dockshield
        print_success "Python package uninstalled"
    fi

else
    print_warning "DockShield installation not detected"
    print_info "If installed manually, you need to remove it manually"
fi

echo ""

# Remove configuration files
if ask_yes_no "Remove configuration files?" "n"; then
    print_info "Removing configuration files..."

    # Standard config
    if [ -d ~/.config/dockshield ]; then
        rm -rf ~/.config/dockshield
        print_success "Removed ~/.config/dockshield"
    fi

    # Flatpak config
    if [ -d ~/.var/app/com.dockshield.DockShield/config ]; then
        rm -rf ~/.var/app/com.dockshield.DockShield/config
        print_success "Removed Flatpak config"
    fi
fi

echo ""

# Remove data files (logs, cache)
if ask_yes_no "Remove data files (logs, cache)?" "n"; then
    print_info "Removing data files..."

    # Standard data
    if [ -d ~/.local/share/dockshield ]; then
        rm -rf ~/.local/share/dockshield
        print_success "Removed ~/.local/share/dockshield"
    fi

    # Flatpak data
    if [ -d ~/.var/app/com.dockshield.DockShield ]; then
        rm -rf ~/.var/app/com.dockshield.DockShield
        print_success "Removed all Flatpak data"
    fi
fi

echo ""

# Remove backups
BACKUP_DIR="/var/backups/dockshield"
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${RED}WARNING: This will delete ALL your container backups!${NC}"
    if ask_yes_no "Remove backup directory ($BACKUP_DIR)?" "n"; then
        if [ -w "$BACKUP_DIR" ]; then
            rm -rf "$BACKUP_DIR"
            print_success "Removed $BACKUP_DIR"
        else
            sudo rm -rf "$BACKUP_DIR"
            print_success "Removed $BACKUP_DIR (with sudo)"
        fi
    else
        print_info "Backups preserved in $BACKUP_DIR"
    fi
fi

echo ""

# Remove desktop entries
if ask_yes_no "Remove desktop entries and icons?" "y"; then
    print_info "Removing desktop entries..."

    # Desktop files
    if [ -f ~/.local/share/applications/dockshield.desktop ]; then
        rm -f ~/.local/share/applications/dockshield.desktop
        print_success "Removed desktop entry"
    fi

    if [ -f ~/.local/share/applications/com.dockshield.DockShield.desktop ]; then
        rm -f ~/.local/share/applications/com.dockshield.DockShield.desktop
        print_success "Removed Flatpak desktop entry"
    fi

    # Icons
    if ls ~/.local/share/icons/hicolor/*/apps/dockshield.* &> /dev/null; then
        rm -f ~/.local/share/icons/hicolor/*/apps/dockshield.*
        print_success "Removed icons"
    fi

    if ls ~/.local/share/icons/hicolor/*/apps/com.dockshield.DockShield.* &> /dev/null; then
        rm -f ~/.local/share/icons/hicolor/*/apps/com.dockshield.DockShield.*
        print_success "Removed Flatpak icons"
    fi

    # Update caches
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
        print_success "Updated desktop database"
    fi

    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
        print_success "Updated icon cache"
    fi
fi

echo ""

# Cleanup unused Flatpak runtimes
if [ "$INSTALLED_METHOD" = "flatpak" ]; then
    if ask_yes_no "Remove unused Flatpak runtimes? (frees disk space)" "n"; then
        flatpak uninstall --unused -y
        print_success "Removed unused runtimes"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "========================================"
echo ""

# Summary
echo "Summary of what was removed:"
echo "  • DockShield application"
if [ -d ~/.config/dockshield ] || [ -d ~/.var/app/com.dockshield.DockShield ]; then
    echo "  • Configuration files (kept - remove manually if desired)"
else
    echo "  • Configuration files"
fi

if [ -d "$BACKUP_DIR" ]; then
    echo "  • Backups (kept at $BACKUP_DIR)"
else
    echo "  • Backups"
fi

echo ""
echo "Thank you for using DockShield!"
echo ""

# Optional: Remove source directory
if [ -d "$(pwd)/dockshield" ] && [ -f "$(pwd)/setup.py" ]; then
    echo ""
    if ask_yes_no "Remove source directory ($(pwd))?" "n"; then
        cd ..
        SOURCE_DIR="$(basename "$(pwd)")"
        rm -rf "$SOURCE_DIR"
        print_success "Removed source directory"
    fi
fi
