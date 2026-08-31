from collections import Counter
from pathlib import Path

from PIL import Image

IMAGES = [
    Path("samples/delivery-hover-5.png"),
    Path("samples/delivery-hover-15.png"),
]


def report(path):
    raw = Image.open(path)

    print("=" * 60)
    print("file   " + path.name)
    print("mode   " + raw.mode)
    print("size   {} x {}".format(raw.width, raw.height))

    if raw.mode == "RGBA":
        alpha = Counter(raw.getchannel("A").getdata())
        opaque = alpha.get(255, 0)
        clear = alpha.get(0, 0)
        partial = sum(c for a, c in alpha.items() if 0 < a < 255)
        print("alpha  {:,} opaque".format(opaque))
        print("       {:,} transparent".format(clear))
        print("       {:,} partial".format(partial))

    image = raw.convert("RGB")
    counts = Counter(image.getdata())
    print("colors {:,} distinct".format(len(counts)))
    print("")

    for color, count in counts.most_common(12):
        hexcode = "#%02X%02X%02X" % color
        print("  {}  {:>10,} px".format(hexcode, count))
    print("")


for path in IMAGES:
    report(path)