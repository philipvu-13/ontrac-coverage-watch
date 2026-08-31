import json
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

IMAGE = Path("samples/delivery-hover-5.png")
POINTS = Path("state_points.json")
EXTRA = 4

SPLIT = ["AZ", "CA", "IL", "NC", "OR", "UT", "VA"]


def flatten(path):
    raw = Image.open(path).convert("RGBA")
    canvas = Image.new("RGB", raw.size, (255, 255, 255))
    canvas.paste(raw, mask=raw.split()[3])
    return canvas


points = json.loads(POINTS.read_text())

for state, value in points.items():
    if value and isinstance(value[0], int):
        points[state] = [value]

image = flatten(IMAGE)

figure, axes = plt.subplots(figsize=(16, 10))
axes.imshow(image)
axes.set_axis_off()

for state in SPLIT:
    for n in range(EXTRA):
        title = "{}  extra point {} of {}".format(state, n + 1, EXTRA)
        axes.set_title(title, fontsize=20)
        figure.canvas.draw()
        clicked = plt.ginput(n=1, timeout=0)
        if not clicked:
            break
        x, y = clicked[0]
        points[state].append([round(x), round(y)])
        axes.plot(x, y, "ko", markersize=4)
        print("{}  {}, {}".format(state, round(x), round(y)))

plt.close(figure)
POINTS.write_text(json.dumps(points, indent=2))
print("saved")