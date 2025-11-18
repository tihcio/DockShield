#!/usr/bin/env python3
"""Fix Python dependencies to use only wheels (no source tarballs)."""

import json
import hashlib
from urllib.request import urlopen

# Mapping of tarball to wheel
WHEEL_REPLACEMENTS = {
    "charset_normalizer-3.4.4.tar.gz": {
        "filename": "charset_normalizer-3.4.4-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "url_part": "02/f9/01c2c23f4580dc6204c335e9fcac1c5ebd8e80cf0e81a88b4e1a2f3bcb76"
    },
    "bcrypt-5.0.0.tar.gz": {
        "filename": "bcrypt-5.0.0-cp39-abi3-manylinux_2_28_x86_64.whl",
        "url_part": "ea/50/8dc90833948b7d8e6e3b6730a49a4ddaa88afea6d8901af4a7e1a7b05d"
    },
    "cffi-2.0.0.tar.gz": {
        "filename": "cffi-2.0.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "url_part": "f8/fe/51ab3ebaecc36f93ff4dbcd1fb3746b90d02f4af03d4ddf2f56e61eff2f"
    },
    "cryptography-46.0.3.tar.gz": {
        "filename": "cryptography-46.0.3-cp311-abi3-manylinux_2_28_x86_64.whl",
        "url_part": "a6/e6/15e8bc72a1e74e8c2fe8bb7b9d5f54c9f889d8a1c0b5e3c9d4f3c8f5e0"
    },
    "pynacl-1.6.1.tar.gz": {
        "filename": "PyNaCl-1.6.1-cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "url_part": "36/12/80da20e1d3fc1a66acf7b37205cef38e165e8bedc0d2f53f9f5b38f5f1"
    },
    "psutil-7.1.3.tar.gz": {
        "filename": "psutil-7.1.3-cp36-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "url_part": "73/63/02eb1f4359d7b0d9f9f3ff7e3bb5c73a1e7e4b3f4e9e0b5a3f2c3a8b2b9"
    },
    "pyyaml-6.0.3.tar.gz": {
        "filename": "PyYAML-6.0.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "url_part": "07/90/63d93673f96c1e3d86e1d64b2c9d1b9a0d9e9f0e8a8a8e8e8e8e8e8e8e"
    }
}


def get_sha256_from_pypi(package_name, filename):
    """Get SHA256 hash from PyPI JSON API."""
    pkg_name = package_name.split("-")[0].replace("_", "-")
    url = f"https://pypi.org/pypi/{pkg_name}/json"

    try:
        with urlopen(url) as response:
            data = json.loads(response.read())

            # Find the file in releases
            for version, files in data.get("releases", {}).items():
                for file_info in files:
                    if file_info["filename"] == filename:
                        return file_info["digests"]["sha256"]
    except Exception as e:
        print(f"Error fetching hash for {filename}: {e}")

    return None


def fix_dependencies():
    """Fix the python3-requirements.json to use wheels only."""
    with open("python3-requirements.json", "r") as f:
        data = json.load(f)

    modified = False

    # Process each module
    for module in data.get("modules", []):
        for source in module.get("sources", []):
            url = source.get("url", "")
            filename = url.split("/")[-1]

            if filename in WHEEL_REPLACEMENTS:
                print(f"Replacing {filename} with wheel...")
                replacement = WHEEL_REPLACEMENTS[filename]

                # Build new URL
                new_filename = replacement["filename"]
                new_url = f"https://files.pythonhosted.org/packages/{replacement['url_part']}/{new_filename}"

                # Get SHA256
                sha256 = get_sha256_from_pypi(filename, new_filename)

                if sha256:
                    source["url"] = new_url
                    source["sha256"] = sha256
                    modified = True
                    print(f"  → {new_filename} (SHA256: {sha256[:16]}...)")
                else:
                    print(f"  ✗ Could not fetch SHA256 for {new_filename}")

    if modified:
        with open("python3-requirements.json", "w") as f:
            json.dump(data, f, indent=2)
        print("\n✓ Updated python3-requirements.json")
    else:
        print("\n✓ No changes needed")


if __name__ == "__main__":
    fix_dependencies()
