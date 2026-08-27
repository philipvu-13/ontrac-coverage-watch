import csv
from collections import defaultdict

with open("out/map_coverage_rows.csv", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

served = defaultdict(set)
for row in rows:
    if row["outcome"] not in ("unserved", "no_data"):
        served[int(row["map_index"])].add(row["state"])

print("distinct served sets across 18 maps {}".format(len({frozenset(v) for v in served.values()})))

union = set().union(*served.values())
inter = set.intersection(*served.values())

print("union        {}  {}".format(len(union), " ".join(sorted(union))))
print("intersection {}  {}".format(len(inter), " ".join(sorted(inter))))
print("")

for index in sorted(served):
    diff = union - served[index]
    if diff:
        print("  map {:>2} missing {}".format(index, " ".join(sorted(diff))))

print("")
days = defaultdict(set)
for row in rows:
    if row["outcome"] not in ("unserved", "no_data"):
        days[row["state"]].add(row["outcome"])

varies = sum(1 for state in days if len(days[state]) > 1)
print("states whose transit day varies by origin {} of {}".format(varies, len(days)))