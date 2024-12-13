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

        for entity in group.values():
            sprite = next(
                (x for x in entity["components"] if x["type"] == "Sprite"), None)
            icon = next(
                (x for x in entity["components"] if x["type"] == "Icon"), None)
            if not sprite:
                eprint(f"Entity '{entity['id']}' has no sprite!")
                continue

            # TODO: Directions
            dest: Path = entities_out / (str(entity["id"]) + ".png")

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
                        eprint(f"Entity '{entity['id']}' is missing a sprite!")
                        continue
                if "state" not in layer:
                    if "map" not in layer and not "type" in layer:
                        # Simply ignore if the layer uses a map or custom type.
                        eprint(f"Entity '{entity['id']}' is missing a state!")
                    continue

                layer_rsi_file: Path = resources_dir / "Textures" / \
                    remove_prefix(layer["sprite"], "/Textures/") / "meta.json"
                if not layer_rsi_file.exists():
                    eprint(f"Entity '{entity['id']}' is missing RSI!")
                    continue

                # Some files have a BOM for some reason...
                json_text = layer_rsi_file.read_text(
                    "UTF-8").replace("\uFEFF", "")
                layer_rsa = json.loads(json_text)

                # YAML has some eager boolean parsing...
                if layer["state"] is True:
                    yes = ["y", "yes", "true", "on"]
                    state = next(
                        (x for x in layer_rsa["states"] if x["name"].lower() in yes), None)
                elif layer["state"] is False:
                    no = ["n", "no", "false", "off"]
                    state = next(
                        (x for x in layer_rsa["states"] if x["name"].lower() in no), None)
                else:
                    state = next(
                        (x for x in layer_rsa["states"] if x["name"] == str(layer["state"])), None)

                if not state:
                    eprint(
                        f"Entity '{entity['id']}' is missing state '{layer['state']}!")
                    continue
                if ("directions" in state and state["directions"] != 1) or ("delays" in state):
                    # TODO:
                    eprint(
                        f"Entity '{entity['id']}' has more than one direction!")
                    continue

                layer_image_file = layer_rsi_file.parent / \
                    (state["name"] + ".png")
                layer_image = cv2.imread(
                    layer_image_file, cv2.IMREAD_UNCHANGED)
                height, width, dim = layer_image.shape
                if dim == 3:
                    layer_image = cv2.cvtColor(layer_image, cv2.COLOR_RGB2RGBA)
                    dim = 4
                if img is None:
                    img = layer_image
                else:
                    e_height, e_width, e_dim = img.shape
                    if e_height != height or e_width != width or e_dim != dim:
                        eprint(
                            f"Entity '{entity['id']}' has differently sized layers!")
                        continue
                    add_transparent_image(img, layer_image)

            if img is None:
                eprint(f"Entity '{entity['id']}' has no valid layers!")
                continue
            cv2.imwrite(dest, img)

            # Update the sprite but not the index.
            if entity["id"] in existing.ids:
                continue

            height, width, dim = img.shape
            existing.ids.append(entity["id"])
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
    # TODO: implement
    return [("All", entities)]
