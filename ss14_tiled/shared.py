"""Shared stuffs and utility functions."""
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


def eprint(*args, **kwargs):
    """Print to std-error."""
    print(*args, file=sys.stderr, **kwargs)


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


def add_transparent_image(background, foreground):
    """https://stackoverflow.com/a/59211216"""
    bg_h, bg_w, bg_channels = background.shape
    fg_h, fg_w, fg_channels = foreground.shape

    assert bg_h == fg_h
    assert bg_w == fg_w
    assert bg_channels == 4
    assert fg_channels == 4

    alpha_background = background[:, :, 3] / 255.0
    alpha_foreground = foreground[:, :, 3] / 255.0

    # set adjusted colors
    for color in range(0, 3):
        background[:, :, color] = alpha_foreground * foreground[:, :, color] + \
            alpha_background * background[:, :, color] * (1 - alpha_foreground)

    # set adjusted alpha and denormalize back to 0-255
    background[:, :, 3] = (1 - (1 - alpha_foreground)
                           * (1 - alpha_background)) * 255


def remove_prefix(string: str, prefix: str):
    """Remove a prefix from a string if it exists."""
    if string.startswith(prefix):
        return string[len(prefix):]
    return string
