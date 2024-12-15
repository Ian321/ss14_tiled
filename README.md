# Space Station 14 - Tiled

![Screenshot showing what is currently possible.](./Poster.png)

Tooling to use [Tiled](https://www.mapeditor.org/) as map editor for [SS14](https://github.com/space-wizards/space-station-14).

## Prerequisites

Only necessary if you want to build the tile sets yourself.

- [Git](https://git-scm.com/)
- [Python >= 3.11](https://www.python.org/)
- Source code of SS14 (or a fork) somewhere on your system.
  - `git clone https://github.com/space-wizards/space-station-14/`

## Usage

<table>
<tr>
<th>Linux</th>
<th>Windows</th>
</tr>
<tr>
<td>

```sh
# Setup
git clone https://github.com/Ian321/ss14_tiled
cd ss14_tiled
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate or update the tile sets.
python3 -m ss14_tiled /path/to/space-station-14/
```

</td>
<td>

```powershell
# Setup
git clone https://github.com/Ian321/ss14_tiled
cd ss14_tiled
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Generate or update the tile sets.
python -m ss14_tiled /path/to/space-station-14/
```

</td>
</tr>
</table>

- This creates a `dist` directory with all the tile sets.
  - Alternatively you can download them from the [releases page](https://github.com/Ian321/ss14_tiled/releases).
- Once you got the tile sets, you can create a new map in Tiled and drag them in.
  - Make sure the tile size is set to 32x32 (default), cause that's what SS14 uses.

## TODO

- [x] Import (SS14 -> Tiled)
  - [x] Decals
  - [x] Entities
  - [x] Tiles
- [ ] Export (Tiled -> SS14)
