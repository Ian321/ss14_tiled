"""Some tests."""
import unittest

from deepdiff import DeepDiff

from . import __main__


class TestMergeEntity(unittest.TestCase):
    """Tests to see if merging entities works."""
    def test_basalt(self):
        """From /Resources/Prototypes/Entities/Tiles/basalt.yml"""
        child = {
            "type": "entity",
            "id": "BasaltTwo",
            "parent": "BasaltOne",
            "placement": {
                "mode": "SnapgridCenter"
            },
            "components": [{
                "type": "Sprite",
                "layers": [{
                    "state": "basalt2",
                    "shader": "unshaded"
                }]
            }]
        }
        parent = {
            "type": "entity",
            "id": "BasaltOne",
            "description": "Rock.",
            "placement": {
                "mode": "SnapgridCenter"
            },
            "components": [{
                "type": "Clickable",
            }, {
                "type": "Sprite",
                "sprite": "/Textures/Tiles/Planet/basalt.rsi",
                "layers": [{
                    "state": "basalt1",
                    "shader": "unshaded"
                }]
            }, {
                "type": "SyncSprite",
            }, {
                "type": "RequiresTile",
            }, {
                "type": "Transform",
                "anchored": True
            }, {
                "type": "Tag",
                "tags": ["HideContextMenu"]
            }]
        }
        expected = {
            "type": "entity",
            "id": "BasaltTwo",
            "parent": "BasaltOne",
            "description": "Rock.",
            "placement": {
                "mode": "SnapgridCenter"
            },
            "components": [{
                "type": "Clickable",
            }, {
                "type": "Sprite",
                "sprite": "/Textures/Tiles/Planet/basalt.rsi",
                "layers": [{
                    "state": "basalt2",
                    "shader": "unshaded"
                }]
            }, {
                "type": "SyncSprite",
            }, {
                "type": "RequiresTile",
            }, {
                "type": "Transform",
                "anchored": True
            }, {
                "type": "Tag",
                "tags": ["HideContextMenu"]
            }]
        }
        actual = __main__.merge_entity(child, parent)
        diff = DeepDiff(actual, expected, ignore_order=True)
        assert not diff

    def test_new_component(self):
        """If the child has a new component."""
        child = {
            "id": "B",
            "parent": "A",
            "components": [{
                "type": "test_2"
            }]
        }
        parent = {
            "id": "A",
            "components": [{
                "type": "test_1"
            }]
        }
        expected = {
            "id": "B",
            "parent": "A",
            "components": [{
                "type": "test_1"
            }, {
                "type": "test_2"
            }]
        }
        actual = __main__.merge_entity(child, parent)
        diff = DeepDiff(actual, expected, ignore_order=True)
        assert not diff

if __name__ == "__main__":
    unittest.main()
