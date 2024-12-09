"""Expose a "generate"-function."""
from pathlib import Path

from .decals import create_decals
from .entities import create_entities
from .tiles import create_tiles


def generate(root: Path):
    """Create tile-sets for Tiled."""
    out = Path("dist")
    out.mkdir(exist_ok=True)

    create_decals(root, out)
    create_entities(root, out)
    create_tiles(root, out)
