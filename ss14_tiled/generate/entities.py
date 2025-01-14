"""Everything for the "entity"-tiles."""
import copy
import json
from pathlib import Path

import cv2
import yaml

from ..shared import (CacheJSON, Image, add_transparent_image, create_tsx,
                      eprint, remove_prefix)


def create_entities(root: Path, out: Path):
    """Create the "entities"-tiles."""
    entities_out = out / ".images" / "entities"
    entities_out.mkdir(parents=True, exist_ok=True)

    entities = find_entities(root)
    entities = filter_entities(entities)
    groups = group_entities(entities)

    resources_dir = root / "Resources"
    for g_name, group in groups:
        existing_out = out / ".data" / f"entities_{g_name}.json"
        existing = CacheJSON.from_json(existing_out)

        for entity in sorted(group.values(), key=lambda x: x["id"]):
            sprite = next(
                (x for x in entity["components"] if x["type"] == "Sprite"), None)
            icon = next(
                (x for x in entity["components"] if x["type"] == "Icon"), None)
            if not sprite:
                eprint(f"Entity '{entity['id']}' has no sprite!")
                continue

            max_directions = 1
            diagonal = "suffix" in entity and "diagonal" in str(entity["suffix"]).lower()
            if diagonal:
                max_directions = 4
            for d, direction in enumerate(("S", "N", "E", "W", "SE", "SW", "NE", "NW")):
                if d >= max_directions:
                    break

                dest: Path = entities_out / (str(entity["id"]) + f"_{direction}.png")
                img = None
                if "layers" not in sprite:
                    if "sprite" in sprite and "state" in sprite:
                        sprite["layers"] = [{
                            "sprite": sprite["sprite"],
                            "state": sprite["state"]
                        }]
                    elif icon is not None and "sprite" in icon and "state" in icon:
                        sprite["layers"] = [{
                            "sprite": icon["sprite"],
                            "state": icon["state"]
                        }]
                    else:
                        eprint(f"Entity '{entity['id']}' has no sprite!")
                        continue

                for layer in sprite["layers"]:
                    # Skip layers that are invisible by default.
                    if "visible" in layer and not layer["visible"]:
                        continue

                    if "sprite" not in layer:
                        if "sprite" in sprite:
                            layer["sprite"] = sprite["sprite"]
                        else:
                            eprint(
                                f"Entity '{entity['id']}' is missing a sprite!")
                            continue
                    if "state" not in layer:
                        if "map" not in layer and not "type" in layer:
                            # Simply ignore if the layer uses a map or custom type.
                            eprint(
                                f"Entity '{entity['id']}' is missing a state!")
                        continue

                    layer_rsi_file: Path = resources_dir / "Textures" / \
                        remove_prefix(layer["sprite"], "/Textures/") / "meta.json"
                    if not layer_rsi_file.exists():
                        eprint(f"Entity '{entity['id']}' is missing RSI!")
                        continue

                    # Some files have a BOM for some reason...
                    json_text = layer_rsi_file.read_text("UTF-8").replace("\uFEFF", "")
                    layer_rsa = json.loads(json_text)

                    # YAML has some eager boolean parsing...
                    if layer["state"] is True:
                        yes = ["y", "yes", "true", "on"]
                        state = next(
                            (x for x in layer_rsa["states"]
                             if x["name"].lower() in yes), None)
                    elif layer["state"] is False:
                        no = ["n", "no", "false", "off"]
                        state = next(
                            (x for x in layer_rsa["states"]
                             if x["name"].lower() in no), None)
                    else:
                        state = next(
                            (x for x in layer_rsa["states"]
                             if x["name"] == str(layer["state"])), None)

                    if not state:
                        eprint(f"Entity '{entity['id']}' is missing state '{layer['state']}!")
                        continue

                    tile_width = layer_rsa["size"]["x"]
                    tile_height = layer_rsa["size"]["y"]

                    directions = 1
                    if "directions" in state:
                        directions = state["directions"]
                        max_directions = max(max_directions, directions)

                    if directions not in (1, 4, 8):
                        eprint(f"Entity '{entity['id']} wants {directions} directions!")
                        continue

                    per_direction = 1
                    if "delays" in state:
                        per_direction = len(state["delays"][0])

                    layer_image_file = layer_rsi_file.parent / (state["name"] + ".png")
                    layer_image = cv2.imread(layer_image_file, cv2.IMREAD_UNCHANGED)
                    height, width, dim = layer_image.shape
                    if dim == 3:
                        layer_image = cv2.cvtColor(layer_image, cv2.COLOR_RGB2RGBA)
                        dim = 4

                    if directions == 1:
                        index = 0
                    elif directions == max_directions:
                        index = per_direction * d
                    else:
                        eprint(f"Entity '{entity['id']} has incompatible directions!")
                        continue

                    tiles_x = width // tile_width
                    y_offset = (index // tiles_x) * tile_height
                    x_offset = (index % tiles_x) * tile_width

                    layer_image = layer_image[
                        y_offset:y_offset+tile_height,
                        x_offset:x_offset+tile_width
                    ]
                    height, width, dim = layer_image.shape

                    if img is None:
                        img = layer_image
                    else:
                        e_height, e_width, e_dim = img.shape
                        if e_dim != dim:
                            eprint(f"Entity '{entity['id']}' has a different number of dimensions!")
                            continue

                        # Expand canvas so that both are the same size.
                        # Just center it, as the only entity that uses this is the gravity-gen.
                        m_height = max(e_height, height)
                        m_width = max(e_width, width)
                        img = cv2.copyMakeBorder(img,
                                                 (m_height - e_height) // 2,
                                                 (m_height - e_height) // 2,
                                                 (m_width - e_width) // 2,
                                                 (m_width - e_width) // 2,
                                                 cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
                        layer_image = cv2.copyMakeBorder(layer_image,
                                                         (m_height - height) // 2,
                                                         (m_height - height) // 2,
                                                         (m_width - width) // 2,
                                                         (m_width - width) // 2,
                                                         cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
                        add_transparent_image(img, layer_image)

                if img is None:
                    eprint(f"Entity '{entity['id']}' has no valid layers!")
                    continue

                if diagonal:
                    if not d:     # S
                        pass
                    elif d == 1:  # N
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif d == 2:  # E
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    elif d == 3:  # W
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    else:
                        raise ValueError(f"Expected d to be 0-3, not '{d}'.")
                cv2.imwrite(dest, img)

                # Update the sprite but not the index.
                if entity["id"] + f"_{directions}" in existing.ids:
                    continue

                height, width, dim = img.shape
                existing.ids.append(entity["id"] + f"_{direction}")
                existing.images.append(
                    Image(f"./.images/entities/{dest.name}", str(width), str(height)))

        existing_out.write_text(json.dumps(existing, default=vars), "UTF-8")
        create_tsx(existing, f"Entities - {g_name}",
                   out / f"entities_{g_name}.tsx")


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
                if isinstance(entity["parent"], str):
                    entity["parent"] = [entity["parent"]]
                children.append(entity)
            else:
                entity["parent"] = []
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


class SafeLoadIgnoreUnknown(yaml.SafeLoader):
    """YAML-Loader that ignores unknown constructors."""

    def ignore_unknown(self, _node):
        """Returns None no matter the node."""
        return None


SafeLoadIgnoreUnknown.add_constructor(
    None, SafeLoadIgnoreUnknown.ignore_unknown)


def merge_entity(child: dict, parent: dict) -> dict:
    """Merge entities."""
    out = copy.deepcopy(parent)
    for (key, value) in child.items():
        if key in ("components", "parent"):
            continue
        out[key] = value

    if "abstract" in child and child["abstract"]:
        out["abstract"] = True
    elif "abstract" in out:
        del out["abstract"]

    out["parent"] = list(set(out["parent"] + child["parent"]))

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


def group_entities(entities: dict) -> list[tuple[str, dict[str, dict]]]:
    """Split entities into groups."""
    pipes = {}
    window_doors = {}
    eat_and_drink = {}
    clothes = {}
    closets = {}
    airlocks = {}
    windows = {}
    walls = {}
    computers = {}
    markers = {}
    signs = {}
    other = {}

    for key, value in entities.items():
        parents = value["parent"]
        if "GasPipeBase" in parents or "DisposalPipeBase" in parents:
            pipes[key] = value
        elif "BaseWindoor" in parents:
            window_doors[key] = value
        elif "FoodBase" in parents or "DrinkBase" in parents:
            eat_and_drink[key] = value
        elif "Clothing" in parents:
            clothes[key] = value
        elif "ClosetBase" in parents or "BaseWallCloset" in parents:
            closets[key] = value
        elif key == "Airlock" or "Airlock" in parents or "BaseFirelock" in parents:
            airlocks[key] = value
        elif key == "Window" or "Window" in parents \
                or key == "WindowDirectional" or "WindowDirectional" in parents \
                or "PlastitaniumWindowBase" in parents:
            windows[key] = value
        elif key == "WallShuttleDiagonal" or "WallShuttleDiagonal" in parents \
                or key == "WallPlastitaniumDiagonalIndestructible" or "BaseWall" in parents:
            walls[key] = value
        elif "BaseComputer" in parents:
            computers[key] = value
        elif "MarkerBase" in parents:
            markers[key] = value
        elif "BaseSign" in parents:
            signs[key] = value
        else:
            other[key] = value

    return [
        ("Pipes", pipes),
        ("Windoors", window_doors),
        ("Eat and Drink", eat_and_drink),
        ("Clothes", clothes),
        ("Closets and Lockers", closets),
        ("Airlocks", airlocks),
        ("Windows", windows),
        ("Walls", walls),
        ("Computers", computers),
        ("Markers", markers),
        ("Signs", signs),
        ("Other", other),
    ]
