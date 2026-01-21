from pathlib import Path

from PIL import Image

ICON = Path(__file__).parent.parent.parent / "ICON.png"


def get_ICON():
    return Image.open(ICON)
