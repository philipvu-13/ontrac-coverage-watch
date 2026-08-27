import csv
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


ref = {row["zip5"]: row["state"] for row in load("out/zip_to_state.csv")}
surcharge = load("out/zip_surcharge_rows.csv")
maps = load("out/map_coverage_rows.csv")

served = {row["state"] for row in maps if row["outcome"] not in ("unserved", "no_data")}
counts = Counter(ref[row["zip5"]] for row in surcharge)
outside = {state: count for state, count in counts.items() if state not in served}

print("map served states     {}".format(len(served)))
print("pdf states            {}".format(len(counts)))
print("pdf states off map    {}".format(len(outside)))
print("")
print("surcharge zips inside map footprint   {}".format(sum(c for s, c in counts.items() if s in served)))
print("surcharge zips outside map footprint  {}".format(sum(outside.values())))
print("")
for state, count in sorted(outside.items(), key=lambda item: -item[1]):
    print("  {}  {}".format(state, count))