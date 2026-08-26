import json
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

IMAGE = Path("samples/delivery-hover-5.png")
POINTS = Path("state_points.json")
TOLERANCE = 20

PALETTE = {
    (211, 49, 56): "1",
    (37, 41, 99): "2",
    (210, 145, 41): "3",
    (158, 203, 202): "4",
    (58, 170, 73): "5",
    (116, 39, 119): "6",
    (249, 214, 4): "7",
    (237, 236, 237): "unserved",
}


def flatten(path):
    raw = Image.open(path).convert("RGBA")
    canvas = Image.new("RGB", raw.size, (255, 255, 255))
    canvas.paste(raw, mask=raw.split()[3])
    return canvas


def nearest(color):
    best = None
    best_distance = None
    for known, label in PALETTE.items():
        gap = sum((a - b) ** 2 for a, b in zip(color, known)) ** 0.5
        if best_distance is None or gap < best_distance:
            best = label
            best_distance = gap
    if best_distance > TOLERANCE:
        return None, best_distance
    return best, best_distance


image = flatten(IMAGE)
points = json.loads(POINTS.read_text())

bad = []
for state in sorted(points):
    x, y = points[state]
    color = image.getpixel((x, y))
    label, gap = nearest(color)
    if label is None:
        bad.append(state)
        print("BAD  {}  {}  off by {:.0f}".format(state, color, gap))

print("")
print("{} good, {} to reclick".format(len(points) - len(bad), len(bad)))

if bad:
    figure, axes = plt.subplots(figsize=(16, 10))
    axes.imshow(image)
    axes.set_axis_off()

    for state in bad:
        axes.set_title("reclick inside " + state, fontsize=20)
        figure.canvas.draw()
        clicked = plt.ginput(n=1, timeout=0)
        if not clicked:
            break
        x, y = clicked[0]
        points[state] = [round(x), round(y)]
        axes.plot(x, y, "ko", markersize=4)
        print("{}  {}, {}".format(state, round(x), round(y)))

    plt.close(figure)
    POINTS.write_text(json.dumps(points, indent=2))
    print("saved")