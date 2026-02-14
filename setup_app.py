"""py2app build configuration for MuttR.app."""

import sys

# modulegraph's AST visitor can exceed the default recursion limit
# on deeply nested source files in dependencies (e.g. numpy, ctranslate2).
sys.setrecursionlimit(5000)

from setuptools import setup

APP = ["muttr/app.py"]

DATA_FILES = [
    ("", ["resources/menubar-icon.png"]),
]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/MuttR.icns",
    "plist": {
        "CFBundleName": "MuttR",
        "CFBundleDisplayName": "MuttR",
        "CFBundleIdentifier": "com.muttr.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "LSUIElement": True,
        "LSMinimumSystemVersion": "13.0",
        "NSMicrophoneUsageDescription": (
            "MuttR needs microphone access for voice dictation."
        ),
        "NSHighResolutionCapable": True,
    },
    "frameworks": [
        ".venv/lib/python3.14/site-packages/_sounddevice_data/portaudio-binaries/libportaudio.dylib",
    ],
    "packages": [
        "muttr",
        "faster_whisper",
        "ctranslate2",
        "sounddevice",
        "_sounddevice_data",
        "numpy",
        "huggingface_hub",
        "tokenizers",
    ],
    "excludes": [
        "parakeet_mlx",
        "mlx",
        "scipy",
        "matplotlib",
        "tkinter",
        "test",
        "unittest",
        "setuptools",
        "pip",
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
