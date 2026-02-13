from setuptools import setup, find_packages

setup(
    name="muttr",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "faster-whisper>=1.0.0",
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
        "pyobjc-core>=10.0",
        "pyobjc-framework-Cocoa>=10.0",
        "pyobjc-framework-Quartz>=10.0",
    ],
    extras_require={
        "parakeet": ["parakeet-mlx>=0.5.0"],
    },
    entry_points={
        "console_scripts": [
            "muttr=muttr.app:main",
        ],
    },
    python_requires=">=3.11",
)
