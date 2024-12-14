# Space Station 14 - Tiled

![Screenshot showing what is currently possible.](./Poster.png)

Tooling to use [Tiled](https://www.mapeditor.org/) as map editor for [SS14](https://github.com/space-wizards/space-station-14).

```sh
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate or update the tile sets.
python3 -m ss14_tiled /path/to/space-station-14/
```

## TODO

- [ ] Generate (SS14 -> Tiled)
  - [x] Tile sets
    - [x] Decals
    - [x] Entities
    - [x] Tiles
  - [ ] Map
- [ ] Export (Tiled -> SS14)
