import json
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

IMAGE = Path("samples/delivery-hover-15.png")
OUTPUT = Path("state_points.json")

STATES = [
    "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL",
    "GA", "IA", "ID", "IL", "IN", "KS", "KY", "LA",
    "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT",
    "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY",
    "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY",
]

image = Image.open(IMAGE)
points = {}

figure, axes = plt.subplots(figsize=(16, 10))
axes.imshow(image)
axes.set_axis_off()

for state in STATES:
    axes.set_title("click inside " + state, fontsize=20)
    figure.canvas.draw()
    clicked = plt.ginput(n=1, timeout=0)
    if not clicked:
        break
    x, y = clicked[0]
    points[state] = [round(x), round(y)]
    axes.plot(x, y, "wo", markersize=4)
    print("{}  {}, {}".format(state, round(x), round(y)))

plt.close(figure)
OUTPUT.write_text(json.dumps(points, indent=2))
print("saved {} points".format(len(points)))