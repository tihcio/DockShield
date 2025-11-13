#!/bin/bash
# DockShield Installation Script
# This script helps install DockShield and its dependencies

set -e

echo "=================================="
echo "DockShield Installation Script"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    print_error "Cannot detect Linux distribution"
    exit 1
fi

print_success "Detected: $DISTRO $VERSION"

# Check if Docker is installed
echo ""
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    print_success "Docker is installed: $(docker --version)"
else
    print_warning "Docker is not installed"
    read -p "Do you want to install Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        case "$DISTRO" in
            fedora|rhel|centos)
                sudo dnf install -y docker
                ;;
            ubuntu|debian)
                curl -fsSL https://get.docker.com -o get-docker.sh
                sudo sh get-docker.sh
                rm get-docker.sh
                ;;
            arch)
                sudo pacman -S --noconfirm docker
                ;;
            *)
                print_error "Automatic Docker installation not supported for $DISTRO"
                echo "Please install Docker manually: https://docs.docker.com/engine/install/"
                exit 1
                ;;
        esac

        sudo systemctl enable docker
        sudo systemctl start docker
        print_success "Docker installed and started"
    else
        print_error "Docker is required. Please install it manually."
        exit 1
    fi
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    print_warning "Docker daemon is not running or you don't have permissions"

    # Try to start Docker
    if systemctl is-active --quiet docker; then
        print_warning "Docker service is active but you may need to add your user to docker group"
    else
        sudo systemctl start docker
    fi
fi

# Add user to docker group
echo ""
echo "Checking Docker permissions..."
if groups $USER | grep -q '\bdocker\b'; then
    print_success "User is in docker group"
else
    print_warning "Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_success "User added to docker group"
    print_warning "You need to logout and login for this to take effect"
fi

# Check Python version
echo ""
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python is installed: $PYTHON_VERSION"

    # Check if version is >= 3.10
    REQUIRED_VERSION="3.10"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        print_success "Python version is compatible"
    else
        print_error "Python 3.10 or higher is required"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."

case "$DISTRO" in
    fedora|rhel|centos)
        sudo dnf install -y python3-pip python3-devel python3-PyQt6
        ;;
    ubuntu|debian)
        sudo apt update
        sudo apt install -y python3-pip python3-venv python3-pyqt6
        ;;
    arch)
        sudo pacman -S --noconfirm python-pip python-pyqt6
        ;;
esac

print_success "System dependencies installed"

# Install DockShield
echo ""
echo "Installing DockShield..."

# Check if we're in the source directory
if [ -f "setup.py" ] && [ -f "requirements.txt" ]; then
    print_success "Installing from source directory"

    # Create virtual environment (optional but recommended)
    read -p "Do you want to create a virtual environment? (recommended) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 -m venv venv
        source venv/bin/activate
        print_success "Virtual environment created and activated"
    fi

    # Install
    pip install -r requirements.txt
    pip install -e .

    print_success "DockShield installed from source"
else
    # Install from pip (if published)
    pip install dockshield
    print_success "DockShield installed from PyPI"
fi

# Create configuration directory
echo ""
echo "Setting up configuration..."
mkdir -p ~/.config/dockshield
if [ ! -f ~/.config/dockshield/config.yml ]; then
    if [ -f "config.example.yml" ]; then
        cp config.example.yml ~/.config/dockshield/config.yml
        print_success "Configuration file created: ~/.config/dockshield/config.yml"
    fi
fi

# Create backup directory
echo ""
echo "Creating backup directory..."
BACKUP_DIR="/var/backups/dockshield"
if [ ! -d "$BACKUP_DIR" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown $USER:$USER "$BACKUP_DIR"
    print_success "Backup directory created: $BACKUP_DIR"
else
    print_success "Backup directory already exists: $BACKUP_DIR"
fi

# Install desktop entry
echo ""
read -p "Do you want to install desktop entry? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p ~/.local/share/applications
    if [ -f "dockshield.desktop" ]; then
        cp dockshield.desktop ~/.local/share/applications/
        print_success "Desktop entry installed"
    fi
fi

# Installation complete
echo ""
echo "=================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. If you were added to docker group, logout and login"
echo "2. Edit configuration: nano ~/.config/dockshield/config.yml"
echo "3. Run DockShield: dockshield"
echo ""
echo "For help: dockshield --help"
echo "For documentation: cat README.md"
echo ""

# Check if docker group change requires relogin
if ! groups $USER | grep -q '\bdocker\b'; then
    print_warning "IMPORTANT: You need to logout and login for docker group changes to take effect"
else
    # Try to run a quick test
    if docker ps &> /dev/null 2>&1; then
        print_success "Docker permissions are working correctly"
        echo ""
        read -p "Do you want to start DockShield now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            dockshield &
        fi
    fi
fi
