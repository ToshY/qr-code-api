from setuptools import setup, find_packages  # type: ignore
import os
import re


def parse_version():
    """Read __version__ from qr/__init__.py without importing the package."""
    init_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "qr", "__init__.py"
    )
    with open(init_path, encoding="utf-8") as fp:
        match = re.search(
            r'^__version__\s*=\s*["\']([^"\']+)["\']', fp.read(), re.MULTILINE
        )
    if not match:
        raise RuntimeError("Unable to find __version__ in qr/__init__.py")
    return match.group(1)


VERSION = parse_version()


def parse_requirements(filename):
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        encoding="utf-8",
        mode="r",
    ) as file:
        return [
            line.strip() for line in file if line.strip() and not line.startswith("#")
        ]


def parse_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
        mode="r",
    ) as fp:
        return fp.read()


setup(
    name="qr-code-api",
    description="A command-line utility and API for creating QR codes.",
    long_description=parse_long_description(),
    long_description_content_type="text/markdown",
    author="ToshY (https://github.com/ToshY)",
    url="https://github.com/ToshY/qr-code-api",
    project_urls={
        "Issues": "https://github.com/ToshY/qr-code-api/issues",
        "CI": "https://github.com/ToshY/qr-code-api/actions",
        "Releases": "https://github.com/ToshY/qr-code-api/releases",
    },
    license="BSD-3-Clause",
    version=VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "qr=qr.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "qr": ["static/*"],
    },
    install_requires=parse_requirements("requirements.txt"),
    extras_require={
        "dev": parse_requirements("requirements.dev.txt"),
    },
    python_requires=">=3.11",
)
