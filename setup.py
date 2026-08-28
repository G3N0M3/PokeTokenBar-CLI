from setuptools import setup, find_packages

setup(
    name="poketokenbar",
    version="1.8.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "poketokenbar = poketokenbar.cli:main",
            "ptb = poketokenbar.cli:main",
        ],
    },
    python_requires=">=3.8",
    install_requires=[
        "Pillow>=9.0.0",
    ],
)
