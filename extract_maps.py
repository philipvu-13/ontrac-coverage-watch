import csv
import io
import json
from collections import Counter

import boto3
from PIL import Image

BUCKET = "unclephil-ontrac-coverage-raw"
DT = "2026-08-27"
POINTS = "state_points.json"
OUT = "out/map_coverage_rows.csv"

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

SORT_CENTERS = {
    1: ("Vancouver", "WA"),
    2: ("Hayward", "CA"),
    3: ("Reno", "NV"),
    4: ("Salt Lake City", "UT"),
    5: ("Denver", "CO"),
    6: ("Las Vegas", "NV"),
    7: ("Ontario", "CA"),
    8: ("Visalia", "CA"),
    9: ("Commerce", "CA"),
    10: ("Phoenix", "AZ"),
    11: ("Dallas", "TX"),
    12: ("Columbus", "OH"),
    13: ("Logan Township", "NJ"),
    14: ("Nashville", "TN"),
    15: ("Charlotte", "NC"),
    16: ("Orlando", "FL"),
    17: ("South Brunswick", "NJ"),
    18: ("Chicago", "IL"),
}


def classify(pixel):
    best = "no_data"
    best_distance = None
    for colour, label in PALETTE.items():
        distance = sum((a - b) ** 2 for a, b in zip(pixel, colour)) ** 0.5
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best = label
    if best_distance > TOLERANCE:
        return "no_data"
    return best


def sample(image, x, y):
    votes = Counter()
    for dx in range(-BOX, BOX + 1):
        for dy in range(-BOX, BOX + 1):
            px, py = x + dx, y + dy
            if 0 <= px < image.width and 0 <= py < image.height:
                votes[classify(image.getpixel((px, py)))] += 1
    return votes.most_common(1)[0][0]


def load_map(s3, index):
    key = "raw/source=coverage-maps/dt={}/delivery-hover-{}.png".format(DT, index)
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    raw = Image.open(io.BytesIO(body)).convert("RGBA")
    canvas = Image.new("RGB", raw.size, (255, 255, 255))
    canvas.paste(raw, mask=raw.split()[3])
    return key, canvas


def main():
    with open(POINTS, encoding="utf-8") as handle:
        points = json.load(handle)

    s3 = boto3.client("s3")
    rows = []

    for index in sorted(SORT_CENTERS):
        city, state_code = SORT_CENTERS[index]
        key, image = load_map(s3, index)

        for state in sorted(points):
            readings = [sample(image, x, y) for x, y in points[state]]
            counts = Counter(readings)
            outcome, agreeing = counts.most_common(1)[0]
            split = "yes" if len(set(readings)) > 1 else "no"
            ambiguous = split == "yes" or state == "DC"

            rows.append({
                "sort_center": city,
                "sort_center_state": state_code,
                "map_index": index,
                "state": state,
                "outcome": outcome,
                "points_total": len(readings),
                "points_agreeing": agreeing,
                "split": split,
                "provenance": "coverage_map_png",
                "confidence": "inferred_ambiguous" if ambiguous else "inferred",
                "dt": DT,
                "source_key": key,
            })

        served = sum(
            1 for row in rows
            if row["map_index"] == index and row["outcome"] not in ("unserved", "no_data")
        )
        print("{:>2}  {:<16} served {:>2} of {}".format(index, city, served, len(points)))

    fields = [
        "sort_center", "sort_center_state", "map_index", "state", "outcome",
        "points_total", "points_agreeing", "split", "provenance", "confidence",
        "dt", "source_key",
    ]

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("")
    print("rows      {}".format(len(rows)))
    print("no_data   {}".format(sum(1 for row in rows if row["outcome"] == "no_data")))
    print("split     {}".format(sum(1 for row in rows if row["split"] == "yes")))
    print("wrote     {}".format(OUT))


if __name__ == "__main__":
    main()