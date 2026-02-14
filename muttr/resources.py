"""Resolve resource paths in both py2app bundle and development mode."""

import os
import sys


def get_resource_path(filename: str) -> str:
    """Return the absolute path to a bundled resource file.

    In a py2app bundle, resources live in ``Contents/Resources/``.
    In development (``pip install -e .``), they live in ``<project>/resources/``.
    """
    if getattr(sys, "frozen", False):
        # Running inside a py2app .app bundle
        from Foundation import NSBundle

        bundle_resource_dir = NSBundle.mainBundle().resourcePath()
        return os.path.join(bundle_resource_dir, filename)

    # Development: <project_root>/resources/<filename>
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "resources", filename)
