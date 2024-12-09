"""Everything CLI."""
import sys
from pathlib import Path

from .generate import generate


def eprint(*args, **kwargs):
    """Print to std-error."""
    print(*args, file=sys.stderr, **kwargs)


def main():
    """Main entrypoint."""
    if len(sys.argv) != 2:
        if sys.argv[0].endswith("/ss14-tiled"):
            eprint("Usage: ss14-tiled </path/to/ss14.git/>")
        else:
            eprint("Usage: python3 -m ss14_tiled </path/to/ss14.git/>")
        sys.exit(1)

    generate(Path(sys.argv[1]).expanduser())


if __name__ == "__main__":
    main()
