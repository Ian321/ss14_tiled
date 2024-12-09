"""Everything for the "tile"-tiles."""
import json
from pathlib import Path

import cv2
import yaml

from ..shared import CacheJSON, Image, create_tsx


def create_tiles(root: Path, out: Path):
    """Create the "tile"-tiles. As in the floor."""
    existing_out = out / ".data" / "tiles.json"
    existing_out.parent.mkdir(exist_ok=True)

    existing: CacheJSON = CacheJSON([], [])
    if existing_out.exists():
        existing = CacheJSON.from_dict(
            json.loads(existing_out.read_text("UTF-8")))
        assert len(existing.ids) == len(existing.images)

    tiles_out = out / ".images" / "tiles"
    tiles_out.mkdir(parents=True, exist_ok=True)

    resources_dir = root / "Resources"
    yml_dir = resources_dir / "Prototypes/Tiles"
    files = [x for x in yml_dir.glob("**/*.yml") if x.is_file()]

    for file in files:
        for tile in yaml.safe_load(file.read_text("UTF-8")):
            if tile["type"] != "tile":
                continue  # alias
            if not "sprite" in tile:
                continue  # space
            if not "variants" in tile:
                tile["variants"] = 1

            sprite = resources_dir / tile["sprite"].strip("/")
            dest: Path = tiles_out / (tile["id"] + sprite.suffix)
            img = cv2.imread(sprite, cv2.IMREAD_UNCHANGED)
            height, width = img.shape[:2]
            width //= tile["variants"]  # only take the first variant
            cv2.imwrite(dest, img[0:height, 0:width])

            # Update the sprite but not the index.
            if tile["id"] in existing.ids:
                continue
            existing.ids.append(tile["id"])
            existing.images.append(
                Image(f"./.images/tiles/{dest.name}", str(width), str(height)))

    existing_out.write_text(json.dumps(existing, default=vars), "UTF-8")
    create_tsx(existing, "Tiles", out / "tiles.tsx")
