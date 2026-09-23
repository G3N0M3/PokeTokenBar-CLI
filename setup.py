from setuptools import setup, find_packages

setup(
    name="poketokenbar",
    version="1.12.0",
    packages=find_packages(exclude=["tests*", "tests"]),
    entry_points={
        "console_scripts": [
            "poketokenbar = poketokenbar.cli:main",
            "ptb = poketokenbar.cli:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[],
    package_data={
        "poketokenbar": ["assets/sprites/*.png"],
    },
    include_package_data=True,
    extras_require={
        "graphics": ["Pillow>=9.0.0"],
    },
)
