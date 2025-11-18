#!/usr/bin/env python3
"""Update python3-requirements.json to use only precompiled wheels."""

import json

# Mapping: tarball filename → (wheel filename, sha256)
REPLACEMENTS = {
    "charset_normalizer-3.4.4.tar.gz": ("charset_normalizer-3.4.4-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", "840c25fb618a231545cbab0564a799f101b63b9901f2569faecd6b222ac72381"),
    "bcrypt-5.0.0.tar.gz": ("bcrypt-5.0.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", "7aeef54b60ceddb6f30ee3db090351ecf0d40ec6e2abf41430997407a46d2254"),
    "cffi-2.0.0.tar.gz": ("cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", "8941aaadaf67246224cee8c3803777eed332a19d909b47e29c9842ef1e79ac26"),
    "cryptography-46.0.3.tar.gz": ("cryptography-46.0.3-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", "01ca9ff2885f3acc98c29f1860552e37f6d7c7d013d7334ff2a9de43a449315d"),
    "pynacl-1.6.1.tar.gz": ("PyNaCl-1.6.1-cp38-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", "7713f8977b5d25f54a811ec9efa2738ac592e846dd6e8a4d3f7578346a841078"),
    "psutil-7.1.3.tar.gz": ("psutil-7.1.3-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.manylinux_2_28_x86_64.whl", "3bb428f9f05c1225a558f53e30ccbad9930b11c3fc206836242de1091d3e7dd3"),
    "pyyaml-6.0.3.tar.gz": ("PyYAML-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", "b8bb0864c5a28024fac8a632c443c87c5aa6f215c0b126c449ae1a150412f31d"),
}

def get_pypi_url(filename):
    """Get PyPI URL for a file by querying the API."""
    import urllib.request

    # Extract package name from filename
    parts = filename.split("-")
    pkg_name = parts[0].replace("_", "-").lower()

    try:
        url = f"https://pypi.org/pypi/{pkg_name}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

            # Find the file in all releases
            for version, files in data.get("releases", {}).items():
                for file_info in files:
                    if file_info["filename"].lower() == filename.lower():
                        return file_info["url"]
    except:
        pass

    return None

def update_json():
    """Update the JSON file to use wheels."""
    with open("python3-requirements.json", "r") as f:
        data = json.load(f)

    modified_count = 0

    # Process each module
    for module in data.get("modules", []):
        for source in module.get("sources", []):
            url = source.get("url", "")
            filename = url.split("/")[-1]

            if filename in REPLACEMENTS:
                wheel_filename, sha256 = REPLACEMENTS[filename]

                # Get PyPI URL
                pypi_url = get_pypi_url(wheel_filename)

                if pypi_url:
                    print(f"✓ Replacing {filename}")
                    print(f"  with {wheel_filename}")
                    source["url"] = pypi_url
                    source["sha256"] = sha256
                    modified_count += 1
                else:
                    print(f"✗ Could not find URL for {wheel_filename}")

    # Save updated JSON
    with open("python3-requirements.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Updated {modified_count} packages")
    print("✓ Saved to python3-requirements.json")

if __name__ == "__main__":
    update_json()
