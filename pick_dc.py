import json

import matplotlib.pyplot as plt
from PIL import Image

from extract_maps import classify, sample

IMAGE = "samples/delivery-hover-5.png"
POINTS = "state_points.json"
STATE = "DC"


def flatten(path):
    raw = Image.open(path).convert("RGBA")
    canvas = Image.new("RGB", raw.size, (255, 255, 255))
    canvas.paste(raw, mask=raw.split()[3])
    return canvas


image = flatten(IMAGE)
print("image size {} x {}".format(image.width, image.height))
print("Use the magnifier in the toolbar to zoom hard into DC, then left click it once.")

clicked = []
fig, ax = plt.subplots(figsize=(14, 9))
ax.imshow(image)
ax.set_title("Zoom to DC, then click it once")


def on_click(event):
    if event.inaxes is not ax or event.button != 1:
        return
    if plt.get_current_fig_manager().toolbar.mode:
        return
    clicked.append((int(round(event.xdata)), int(round(event.ydata))))
    plt.close(fig)


fig.canvas.mpl_connect("button_press_event", on_click)
plt.show()

if not clicked:
    raise SystemExit("no click captured")

x, y = clicked[-1]
single = classify(image.getpixel((x, y)))
box = sample(image, x, y)

print("")
print("point        {} {}".format(x, y))
print("single pixel {}".format(single))
print("box mode     {}".format(box))

if single == "no_data":
    raise SystemExit("that pixel is not a palette colour, run again and zoom further")

if single != box:
    raise SystemExit("single pixel and box disagree, DC is smaller than the sample box, do not save")

with open(POINTS, encoding="utf-8") as handle:
    points = json.load(handle)

points[STATE] = [[x, y]]

with open(POINTS, "w", encoding="utf-8") as handle:
    json.dump(points, handle, indent=2, sort_keys=True)

print("saved {} to {}".format(STATE, POINTS))