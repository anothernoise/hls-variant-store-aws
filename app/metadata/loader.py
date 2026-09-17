"""
Metadata loader for Storage Engine specifications and physical architecture configurations.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("variant-store.metadata")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_all_engine_metadata(metadata_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Loads all engine metadata JSON definitions from the specified directory.
    
    Returns a dictionary mapping engine display name to its full configuration dictionary.
    """
    target_dir = metadata_dir or CURRENT_DIR
    metadata_map: Dict[str, Dict[str, Any]] = {}
    items: List[Dict[str, Any]] = []

    if not os.path.exists(target_dir):
        logger.warning("Metadata directory %s does not exist.", target_dir)
        return metadata_map

    for filename in os.listdir(target_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(target_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "name" in data:
                    items.append(data)
        except Exception as e:
            logger.error("Failed to parse metadata file %s: %s", filepath, e)

    # Sort items by display_order
    items.sort(key=lambda x: x.get("display_order", 999))

    for item in items:
        metadata_map[item["name"]] = item

    return metadata_map


def get_supported_engines(metadata_dir: Optional[str] = None) -> List[str]:
    """Returns a list of supported engine display names ordered by display_order."""
    meta = load_all_engine_metadata(metadata_dir)
    return list(meta.keys())
