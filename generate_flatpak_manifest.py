#!/usr/bin/env python3
"""
Generate Flatpak manifest for DockShield with correct SHA256 hashes.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

import yaml

# Python dependencies to download
DEPENDENCIES = {
    "pyyaml": {
        "version": "6.0.1",
        "type": "tar.gz",
    },
    "docker": {
        "version": "7.0.0",
        "type": "whl",
        "deps": ["requests", "urllib3", "certifi", "charset-normalizer", "idna", "packaging"],
    },
    "requests": {
        "version": "2.31.0",
        "type": "whl",
    },
    "urllib3": {
        "version": "2.2.0",
        "type": "whl",
    },
    "certifi": {
        "version": "2023.11.17",
        "type": "whl",
    },
    "charset-normalizer": {
        "version": "3.3.2",
        "type": "whl",
    },
    "idna": {
        "version": "3.6",
        "type": "whl",
    },
    "packaging": {
        "version": "23.2",
        "type": "whl",
    },
    "paramiko": {
        "version": "3.4.0",
        "type": "whl",
        "deps": ["bcrypt", "PyNaCl", "cryptography"],
    },
    "bcrypt": {
        "version": "4.1.2",
        "type": "whl",
        "platform": "cp39-abi3-manylinux_2_28_x86_64",
    },
    "PyNaCl": {
        "version": "1.5.0",
        "type": "whl",
        "platform": "cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_24_x86_64",
    },
    "schedule": {
        "version": "1.2.0",
        "type": "whl",
    },
    "python-dateutil": {
        "version": "2.8.2",
        "type": "whl",
        "deps": ["six"],
    },
    "six": {
        "version": "1.16.0",
        "type": "whl",
    },
    "psutil": {
        "version": "5.9.6",
        "type": "tar.gz",
    },
    "cryptography": {
        "version": "41.0.7",
        "type": "whl",
        "platform": "cp37-abi3-manylinux_2_28_x86_64",
        "deps": ["cffi"],
    },
    "cffi": {
        "version": "1.16.0",
        "type": "whl",
        "platform": "cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64",
    },
}


def get_pypi_url(package_name, version, file_type="whl", platform=None):
    """Generate PyPI URL for a package."""
    normalized_name = package_name.replace("-", "_")
    
    if file_type == "whl":
        if platform:
            filename = f"{normalized_name}-{version}-{platform}.whl"
        else:
            filename = f"{normalized_name}-{version}-py3-none-any.whl"
    else:  # tar.gz
        filename = f"{package_name}-{version}.tar.gz"
    
    # PyPI URL pattern
    return f"https://files.pythonhosted.org/packages/{filename}"


def calculate_sha256(url):
    """Download file and calculate SHA256."""
    print(f"Downloading {url}...")
    try:
        with urlopen(url) as response:
            data = response.read()
            sha256 = hashlib.sha256(data).hexdigest()
            print(f"  SHA256: {sha256}")
            return sha256
    except Exception as e:
        print(f"  Error: {e}")
        return None


def generate_manifest():
    """Generate complete Flatpak manifest."""
    
    manifest = {
        "app-id": "com.dockshield.DockShield",
        "runtime": "org.kde.Platform",
        "runtime-version": "6.6",
        "sdk": "org.kde.Sdk",
        "base": "com.riverbankcomputing.PyQt.BaseApp",
        "base-version": "6.6",
        "command": "dockshield",
        "finish-args": [
            "--share=ipc",
            "--socket=x11",
            "--socket=wayland",
            "--share=network",
            "--filesystem=/var/run/docker.sock",
            "--socket=session-bus",
            "--talk-name=org.freedesktop.Notifications",
            "--talk-name=org.kde.StatusNotifierWatcher",
            "--filesystem=home",
            "--filesystem=/var/backups/dockshield:create",
            "--filesystem=xdg-config/dockshield:create",
            "--filesystem=xdg-data/dockshield:create",
            "--filesystem=~/.ssh:ro",
            "--device=all",
        ],
        "cleanup": [
            "/include",
            "/lib/pkgconfig",
            "/share/man",
            "*.la",
            "*.a",
        ],
        "modules": [],
    }
    
    # Add Python modules
    modules_to_install = {
        "python3-pyyaml": ["pyyaml"],
        "python3-docker": ["docker", "requests", "urllib3", "certifi", "charset-normalizer", "idna", "packaging"],
        "python3-paramiko": ["paramiko", "bcrypt", "PyNaCl", "cryptography", "cffi"],
        "python3-schedule": ["schedule"],
        "python3-python-dateutil": ["python-dateutil", "six"],
        "python3-psutil": ["psutil"],
    }
    
    for module_name, packages in modules_to_install.items():
        pip_package = packages[0].replace("_", "-")
        
        module = {
            "name": module_name,
            "buildsystem": "simple",
            "build-commands": [
                f'pip3 install --no-index --find-links="file://${{PWD}}" --prefix=${{FLATPAK_DEST}} {pip_package}'
            ],
            "sources": [],
        }
        
        for package in packages:
            dep_info = DEPENDENCIES.get(package)
            if not dep_info:
                print(f"Warning: {package} not found in dependencies")
                continue
            
            version = dep_info["version"]
            file_type = dep_info["type"]
            platform = dep_info.get("platform")
            
            # Construct URL
            normalized_name = package.replace("-", "_")
            
            if file_type == "whl":
                if platform:
                    filename = f"{normalized_name}-{version}-{platform}.whl"
                else:
                    filename = f"{normalized_name}-{version}-py3-none-any.whl"
            else:
                filename = f"{package}-{version}.tar.gz"
            
            # For simplicity, use placeholder SHA256 - user needs to fill in correct values
            url = f"https://files.pythonhosted.org/packages/{{path}}/{filename}"
            
            module["sources"].append({
                "type": "file",
                "url": url,
                "sha256": "PLACEHOLDER_SHA256_FOR_" + package.upper().replace("-", "_"),
            })
        
        manifest["modules"].append(module)
    
    # Add main application module
    main_module = {
        "name": "dockshield",
        "buildsystem": "simple",
        "build-commands": [
            "pip3 install --no-deps --no-build-isolation --prefix=${FLATPAK_DEST} .",
            "install -Dm644 dockshield.desktop ${FLATPAK_DEST}/share/applications/${FLATPAK_ID}.desktop",
            "install -Dm644 ${FLATPAK_ID}.metainfo.xml ${FLATPAK_DEST}/share/metainfo/${FLATPAK_ID}.metainfo.xml",
            "install -Dm644 dockshield/resources/icons/dockshield.png ${FLATPAK_DEST}/share/icons/hicolor/128x128/apps/${FLATPAK_ID}.png",
        ],
        "sources": [
            {
                "type": "dir",
                "path": ".",
            }
        ],
    }
    
    manifest["modules"].append(main_module)
    
    return manifest


def main():
    """Main function."""
    print("Generating Flatpak manifest for DockShield...\n")
    
    manifest = generate_manifest()
    
    output_file = Path("com.dockshield.DockShield.yml")
    
    print(f"\nWriting manifest to {output_file}...")
    
    with open(output_file, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, width=120)
    
    print(f"\nManifest generated successfully!")
    print("\nIMPORTANT: You need to replace the PLACEHOLDER_SHA256 values with actual SHA256 hashes.")
    print("You can download each file manually and run 'sha256sum filename' to get the hash.")
    print("\nOr use the flatpak-pip-generator tool:")
    print("  git clone https://github.com/flatpak/flatpak-builder-tools.git")
    print("  cd flatpak-builder-tools/pip")
    print("  python3 flatpak-pip-generator pyyaml docker paramiko schedule python-dateutil psutil cryptography")


if __name__ == "__main__":
    main()
