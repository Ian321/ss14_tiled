"""Shared stuffs and utility functions."""
from pathlib import Path
from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass
class Image:
    """Image inside a tsx file."""
    source: str
    width: str
    height: str


@dataclass
class CacheJSON:
    """Cache file content."""
    ids: list[str]
    images: list[Image]

    @staticmethod
    def from_dict(d: dict) -> "CacheJSON":
        """Build this object recursively from a dict."""
        images = [Image(x["source"], x["width"], x["height"])
                  for x in d["images"]]
        return CacheJSON(d["ids"], images)


def create_tsx(cache: CacheJSON, name: str, output: Path, extra: dict = None):
    """All the XML writing."""
    root_element = ET.Element("tileset", name=name)

    if extra:
        properties = ET.SubElement(root_element, "properties")
        for (key, value) in extra.items():
            ET.SubElement(properties, "property", name=key, value=value)

    for i, image in enumerate(cache.images):
        ET.SubElement(
            ET.SubElement(root_element, "tile", id=str(i+1)),
            "image", source=image.source,
            width=str(image.width), height=str(image.height))
    ET.ElementTree(root_element).write(output,
                                       encoding="UTF-8", xml_declaration=True)
