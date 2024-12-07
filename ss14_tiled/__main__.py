"""Main module. To be split up on a later day."""
import copy
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import yaml


def create_tiles(root: Path, out: Path):
    """Create the "tile"-tiles. As in the floor."""
    tiles_out = out / ".images" / "tiles"
    tiles_out.mkdir(parents=True, exist_ok=True)

    resources_dir = root / "Resources"
    yml_dir = resources_dir / "Prototypes/Tiles"
    files = [x for x in yml_dir.glob("**/*.yml") if x.is_file()]

    root_element = ET.Element("tileset", name="Tiles")
    tile_id = 0
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

            tile_id += 1
            ET.SubElement(
                ET.SubElement(root_element, "tile", id=str(tile_id)),
                "image", source=f"./.images/tiles/{dest.name}",
                width=str(width), height=str(height))

    ET.ElementTree(root_element).write(out / "tiles.tsx",
                                       encoding="UTF-8", xml_declaration=True)


def create_decals(root: Path, out: Path, name: str = "", color: str = "#FFF"):
    """Create the "decals"-tiles."""
    decals = ".images/decals"
    if name:
        decals = f".images/decals_{name}"
    decals_out = out / decals
    decals_out.mkdir(parents=True, exist_ok=True)

    resources_dir = root / "Resources"
    yml_dir = resources_dir / "Prototypes/Decals"
    files = [x for x in yml_dir.glob("**/*.yml") if x.is_file()]

    root_element = ET.Element("tileset", name="Decals")
    if name:
        root_element = ET.Element("tileset", name=f"Decals - {name}")

    properties = ET.SubElement(root_element, "properties")
    ET.SubElement(properties, "property", name="color_name", value=name)
    ET.SubElement(properties, "property", name="color_value", value=color)

    tile_id = 0
    for file in files:
        data = yaml.safe_load(file.read_text("UTF-8"))
        for decal in data:
            if decal["type"] != "decal":
                continue  # alias?
            sprite: Path = resources_dir / "Textures" / \
                decal["sprite"]["sprite"].strip("/Textures") / \
                (str(decal["sprite"]["state"]) + ".png")
            dest: Path = decals_out / (str(decal["id"]) + sprite.suffix)
            img = cv2.imread(sprite, cv2.IMREAD_UNCHANGED)
            height, width, dim = img.shape
            if dim == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
                dim = 4

            img = decal_colors(img, color)
            cv2.imwrite(dest, img)

            tile_id += 1
            ET.SubElement(
                ET.SubElement(root_element, "tile", id=str(tile_id)),
                "image", source=f"./{decals}/{dest.name}",
                width=str(width), height=str(height))

    file_name = "decals.tsx"
    if name:
        file_name = f"decals_{name}.tsx"
    ET.ElementTree(root_element).write(out / file_name,
                                       encoding="UTF-8", xml_declaration=True)


def merge_entity(child: dict, parent: dict) -> dict:
    """Merge entities."""
    out = copy.deepcopy(parent)
    for (key, value) in child.items():
        if key == "components":
            continue
        out[key] = value

    if "abstract" in child and child["abstract"]:
        out["abstract"] = True
    elif "abstract" in out:
        del out["abstract"]

    if "components" in child:
        if not "components" in out:
            out["components"] = child["components"]
        else:
            for child_comp in child["components"]:
                found = False
                for i, out_comp in enumerate(out["components"]):
                    if child_comp["type"] != out_comp["type"]:
                        continue
                    found = True
                    for (key, value) in child_comp.items():
                        out_comp[key] = value
                    out["components"][i] = out_comp
                if not found:
                    out["components"].append(child_comp)

    return out


def find_entities(root: Path) -> list[dict]:
    """Find and return all entities."""

    # Some bases are outside the "Entities" directory,
    # so we have to go over everything.
    yml_dir = root / "Resources/Prototypes"
    files = [x for x in yml_dir.glob("**/*.yml") if x.is_file()]

    children = []
    adults = {}
    for file in files:
        for entity in yaml.load(file.read_text("UTF-8"), Loader=SafeLoadIgnoreUnknown) or []:
            if entity["type"] != "entity":
                continue  # alias?
            if "parent" in entity:
                children.append(entity)
            else:
                adults[entity["id"]] = entity

    while len(children) > 0:
        still_children = []
        for child in children:
            parents = child["parent"]
            if isinstance(parents, str):
                parents = [parents]

            if all(parent in adults for parent in parents):
                merged = adults[parents[0]]
                for parent in parents[1:]:
                    merged = merge_entity(adults[parent], merged)
                adults[child["id"]] = merge_entity(child, merged)
            else:
                still_children.append(child)

        children = still_children

    return adults


def filter_entities(entities: dict) -> dict:
    """Filter out some of the entities."""
    entities = {k: v for k, v in entities.items()
                if "abstract" not in v}
    entities = {k: v for k, v in entities.items()
                if "Sprite" in [x["type"] for x in v["components"]]}
    entities = {k: v for k, v in entities.items()
                if "TimedDespawn" not in [x["type"] for x in v["components"]]}
    entities = {k: v for k, v in entities.items()
                if "suffix" not in v or "DEBUG" not in str(v["suffix"])}
    entities = {k: v for k, v in entities.items()
                if "suffix" not in v or "Admeme" not in str(v["suffix"])}
    entities = {k: v for k, v in entities.items()
                if "suffix" not in v or "DO NOT MAP" not in str(v["suffix"])}
    entities = {k: v for k, v in entities.items()
                if "categories" not in v or "HideSpawnMenu" not in v["categories"]}
    entities = {k: v for k, v in entities.items()
                if "Input" not in [x["type"] for x in v["components"]]}
    entities = {k: v for k, v in entities.items()
                if "RandomHumanoidSpawner" not in [x["type"] for x in v["components"]]}

    return entities


def group_entities(entities: dict) -> list[tuple[str, dict]]:
    """Split entities into groups."""
    # TODO: implement
    return [("All", entities)]


def create_entities(root: Path, out: Path):
    """Create the "entities"-tiles."""
    tiles_out = out / ".images" / "entities"
    tiles_out.mkdir(parents=True, exist_ok=True)

    entities = find_entities(root)
    entities = filter_entities(entities)
    groups = group_entities(entities)
    # TODO: Continue


class SafeLoadIgnoreUnknown(yaml.SafeLoader):
    """YAML-Loader that ignores unknown constructors."""

    def ignore_unknown(self, _node):
        """Returns None no matter the node."""
        return None


SafeLoadIgnoreUnknown.add_constructor(
    None, SafeLoadIgnoreUnknown.ignore_unknown)


def parse_hex(color: str):
    """Parse a hex string to RGBA uint8."""
    if len(color) == 4:
        r = int(color[1], 16)
        r = r + (r << 4)
        g = int(color[2], 16)
        g = g + (g << 4)
        b = int(color[3], 16)
        b = b + (b << 4)
        return (r, g, b, 255)
    if len(color) == 5:
        (r, g, b, _) = parse_hex(color[:-1])
        a = int(color[4], 16)
        a = a + (a << 4)
        return (r, g, b, a)
    if len(color) == 7:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return (r, g, b, 255)
    if len(color) == 9:
        (r, g, b, _) = parse_hex(color[:-2])
        a = int(color[7:9], 16)
        return (r, g, b, a)
    raise ValueError("Unknown hex format.")


def decal_colors(img: cv2.Mat, color: str):
    """Scale the colors of an image."""
    (red, green, blue, alpha) = parse_hex(color)
    b, g, r, a = cv2.split(img)
    b = b * (blue / 255)
    g = g * (green / 255)
    r = r * (red / 255)
    a = a * (alpha / 255)
    return cv2.merge((b, g, r, a))


def get_colors(root: Path) -> list[(str, str)]:
    """Get all color names and values (for decals).

    Returns [("palette_color", "#value")]
    """
    resources_dir = root / "Resources"
    yml_dir = resources_dir / "Prototypes/Palettes"
    glob = yml_dir.glob("**/*")
    files = [x for x in glob if x.is_file()]

    results = []
    for file in files:
        data = yaml.safe_load(file.read_text("UTF-8"))
        for palette in data:
            if palette["type"] != "palette":
                continue  # alias?
            for color in palette["colors"]:
                results.append((
                    palette["name"] + "_" + color,
                    palette["colors"][color]
                ))

    return results


def setup(root: Path):
    """Create tile-sets for Tiled."""
    out = Path("dist")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    create_tiles(root, out)
    create_entities(root, out)
    create_decals(root, out)
    for (name, color) in get_colors(root):
        create_decals(root, out, name, color)


def eprint(*args, **kwargs):
    """Print to std-error."""
    print(*args, file=sys.stderr, **kwargs)


def main():
    """Main entrypoint."""
    if len(sys.argv) != 2:
        eprint("Usage: python3 -m ss14_tiled </path/to/ss14.git/>")
        sys.exit(1)

    setup(Path(sys.argv[1]).expanduser())


if __name__ == "__main__":
    main()
