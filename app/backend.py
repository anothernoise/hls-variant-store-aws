"""
Backend Data Access Layer for the Genomic Variant Store Explorer.
Facade providing full backwards-compatibility for existing imports.
Modular implementation located in app.backend_modules.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.backend_modules.base import VariantStoreBackend

__all__ = ["VariantStoreBackend", "PROJECT_ROOT"]
