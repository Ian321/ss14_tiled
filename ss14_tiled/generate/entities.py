"""Everything for the "entity"-tiles."""
import copy
from pathlib import Path

import yaml


def create_entities(root: Path, out: Path):
    """Create the "entities"-tiles."""
    tiles_out = out / ".images" / "entities"
    tiles_out.mkdir(parents=True, exist_ok=True)

    entities = find_entities(root)
    entities = filter_entities(entities)
    groups = group_entities(entities)
    # TODO: Continue


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


def group_entities(entities: dict) -> list[tuple[str, dict]]:
    """Split entities into groups."""
    # TODO: implement
    return [("All", entities)]
