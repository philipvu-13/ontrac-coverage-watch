import csv
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


ref = {row["zip5"]: row["state"] for row in load("out/zip_to_state.csv")}
surcharge = load("out/zip_surcharge_rows.csv")

missing = [row["zip5"] for row in surcharge if row["zip5"] not in ref]
states = Counter(ref[row["zip5"]] for row in surcharge if row["zip5"] in ref)

print("reference zips   {}".format(len(ref)))
print("surcharge zips   {}".format(len(surcharge)))
print("not in reference {}".format(len(missing)))
print("states covered   {}".format(len(states)))
print("")

for state, count in states.most_common(15):
    print("  {}  {}".format(state, count))

print("")
print("sample missing {}".format(missing[:10]))

print("")
print("all states {}".format(" ".join(sorted(states))))