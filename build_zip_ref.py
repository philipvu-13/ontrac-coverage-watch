import csv
from collections import defaultdict

SRC = "out/geonames/US.txt"
OUT = "out/zip_to_state.csv"

FIELDS = [
    "country", "zip5", "place", "state_name", "state", "county_name",
    "county_code", "admin3_name", "admin3_code", "lat", "lon", "accuracy",
]

by_zip = defaultdict(list)
total = 0

with open(SRC, encoding="utf-8") as handle:
    for line in handle:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 5:
            continue
        by_zip[parts[1]].append(dict(zip(FIELDS, parts)))
        total += 1

multi_state = {
    zip5: rows for zip5, rows in by_zip.items()
    if len(set(row["state"] for row in rows)) > 1
}

with open(OUT, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["zip5", "state", "state_name", "place"])
    for zip5 in sorted(by_zip):
        rows = by_zip[zip5]
        chosen = next((row for row in rows if row["state"]), rows[0])
        writer.writerow([zip5, chosen["state"], chosen["state_name"], chosen["place"]])

print("source rows      {}".format(total))
print("unique zips      {}".format(len(by_zip)))
print("zips with >1 row {}".format(sum(1 for rows in by_zip.values() if len(rows) > 1)))
print("zips in >1 state {}".format(len(multi_state)))
print("distinct states  {}".format(len(set(rows[0]["state"] for rows in by_zip.values()))))
print("wrote            {}".format(OUT))

for zip5 in sorted(multi_state)[:10]:
    print("  multi {} {}".format(zip5, sorted(set(row["state"] for row in multi_state[zip5]))))