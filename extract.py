import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image

POINTS = Path("state_points.json")
TOLERANCE = 20
BOX = 4

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

EQUIVALENT = {
    "none": "unserved",
    "no_data": "unknown",
    "not_rendered": "unknown",
}

MAPS = [
    ("delivery-hover-5", "Denver"),
    ("delivery-hover-15", "Charlotte"),
]


def flatten(path):
    raw = Image.open(path).convert("RGBA")
    canvas = Image.new("RGB", raw.size, (255, 255, 255))
    canvas.paste(raw, mask=raw.split()[3])
    return canvas


def classify(color):
    best = None
    best_gap = None
    for known, label in PALETTE.items():
        gap = sum((a - b) ** 2 for a, b in zip(color, known)) ** 0.5
        if best_gap is None or gap < best_gap:
            best = label
            best_gap = gap
    if best_gap > TOLERANCE:
        return "unknown"
    return best


def read_at(image, x, y):
    votes = Counter()
    for dx in range(-BOX, BOX + 1):
        for dy in range(-BOX, BOX + 1):
            votes[classify(image.getpixel((x + dx, y + dy)))] += 1
    return votes.most_common(1)[0][0]


def read_state(image, coordinates):
    votes = Counter()
    for x, y in coordinates:
        votes[read_at(image, x, y)] += 1
    dominant = votes.most_common(1)[0][0]
    return dominant, len(votes) == 1, votes


def load_key(path):
    key = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key[row["state"].strip()] = row["transit_days"].strip()
    return key


points = json.loads(POINTS.read_text())

for slug, name in MAPS:
    image = flatten("samples/" + slug + ".png")
    key = load_key("samples/ground-truth-" + slug + ".csv")

    hits = 0
    misses = []
    splits = []

    for state in sorted(key):
        if state not in points:
            continue
        dominant, uniform, votes = read_state(image, points[state])
        want = EQUIVALENT.get(key[state], key[state])

        if dominant == want:
            hits += 1
        else:
            misses.append((state, want, dominant))

        if not uniform:
            parts = []
            for label, count in votes.most_common():
                parts.append("{} x{}".format(label, count))
            splits.append((state, ", ".join(parts)))

    total = hits + len(misses)
    print("")
    print("{}  {} of {} dominant values correct".format(name, hits, total))

    for state, want, got in misses:
        print("   MISS  {}  key {}  got {}".format(state, want, got))

    for state, detail in splits:
        print("   SPLIT {}  {}".format(state, detail))