# DockShield Flatpak Build Guide

This guide explains how to build and distribute DockShield as a Flatpak package.

## Prerequisites

1. **Install Flatpak**:
   ```bash
   # Fedora
   sudo dnf install flatpak

   # Ubuntu/Debian
   sudo apt install flatpak
   ```

2. **Install flatpak-builder**:
   ```bash
   # Fedora
   sudo dnf install flatpak-builder

   # Ubuntu/Debian
   sudo apt install flatpak-builder
   ```

3. **Add Flathub repository** (if not already added):
   ```bash
   flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
   ```

## Quick Build

Simply run the build script:

```bash
./build-flatpak.sh
```

The script will:
- Check for required dependencies
- Install KDE runtime and PyQt6 base app if needed
- Build the Flatpak package
- Create a local repository

## Manual Build

If you prefer to build manually:

```bash
# Install required runtimes
flatpak install -y flathub org.kde.Platform//6.6 org.kde.Sdk//6.6
flatpak install -y flathub com.riverbankcomputing.PyQt.BaseApp//6.6

# Build the Flatpak
flatpak-builder --force-clean --repo=_flatpak_repo _flatpak_build com.dockshield.DockShield.yml

# Install locally
flatpak install --user _flatpak_repo com.dockshield.DockShield

# Run the app
flatpak run com.dockshield.DockShield
```

## Create Distribution Bundle

To create a single file bundle for distribution:

```bash
flatpak build-bundle _flatpak_repo dockshield.flatpak com.dockshield.DockShield
```

Users can then install it with:
```bash
flatpak install dockshield.flatpak
```

## Files Overview

- `com.dockshield.DockShield.yml` - Main Flatpak manifest
- `com.dockshield.DockShield.metainfo.xml` - AppStream metadata
- `dockshield.desktop` - Desktop entry file
- `python3-requirements.json` - Generated Python dependencies (from flatpak-pip-generator)
- `requirements-flatpak.txt` - List of Python dependencies
- `build-flatpak.sh` - Build helper script

## Updating Python Dependencies

If you need to update Python dependencies:

1. Update `requirements-flatpak.txt` with new versions
2. Regenerate the dependencies JSON:
   ```bash
   git clone https://github.com/flatpak/flatpak-builder-tools.git
   cd flatpak-builder-tools/pip
   python3 flatpak-pip-generator -r ../../requirements-flatpak.txt -o ../../python3-requirements.json
   ```
3. Update the modules section in `com.dockshield.DockShield.yml` with the new data

## Permissions

DockShield requires the following permissions:

- **Docker socket access** (`/var/run/docker.sock`) - Required to manage Docker containers
- **Home directory access** - For backup storage
- **Network access** - For cloud storage backends
- **Session bus** - For KDE notifications
- **SSH directory** (read-only) - For SSH/SFTP backups

## Publishing to Flathub

To publish DockShield on Flathub:

1. Fork the [Flathub repository](https://github.com/flathub/flathub)
2. Create a new repository for `com.dockshield.DockShield`
3. Submit the manifest and required files
4. Follow the Flathub submission guidelines

## Troubleshooting

### Build fails with "No module named 'PyQt6'"

The PyQt6 base app should provide PyQt6. Make sure you have:
```bash
flatpak install flathub com.riverbankcomputing.PyQt.BaseApp//6.6
```

### Docker socket permission denied

Make sure your user is in the `docker` group:
```bash
sudo usermod -aG docker $USER
```

Then restart your session or run:
```bash
newgrp docker
```

### App doesn't start

Check the logs:
```bash
flatpak run --verbose com.dockshield.DockShield
journalctl -f | grep dockshield
```

## Development

For development and testing:

```bash
# Build without installing
flatpak-builder _flatpak_build com.dockshield.DockShield.yml

# Run without installing
flatpak-builder --run _flatpak_build com.dockshield.DockShield.yml dockshield

# Enable debug output
flatpak-builder --verbose _flatpak_build com.dockshield.DockShield.yml
```

## Clean Up

To remove build artifacts:

```bash
rm -rf _flatpak_build _flatpak_repo
```

To uninstall the Flatpak:

```bash
flatpak uninstall com.dockshield.DockShield
```
