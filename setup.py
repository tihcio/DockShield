#!/usr/bin/env python3
"""
DockShield - Docker Container Backup and Restore for KDE
Setup script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="dockshield",
    version="1.0.0",
    author="DockShield Team",
    author_email="info@dockshield.org",
    description="Docker container backup and restore tool for KDE Plasma",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dockshield",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.5.0",
        "docker>=7.0.0",
        "schedule>=1.2.0",
        "paramiko>=3.4.0",
        "pyyaml>=6.0.1",
        "python-dateutil>=2.8.2",
        "psutil>=5.9.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "cloud": [
            "boto3>=1.28.0",  # AWS S3
            "google-cloud-storage>=2.10.0",  # Google Cloud
            "azure-storage-blob>=12.19.0",  # Azure
        ],
    },
    entry_points={
        "console_scripts": [
            "dockshield=dockshield.main:main",
        ],
        "gui_scripts": [
            "dockshield-gui=dockshield.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dockshield": [
            "resources/icons/*.png",
            "resources/icons/*.svg",
            "resources/translations/*.qm",
            "resources/translations/*.ts",
        ],
    },
    zip_safe=False,
)
