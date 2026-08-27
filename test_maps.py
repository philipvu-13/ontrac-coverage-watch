import csv
import sys

KEYS = {
    5: "samples/ground-truth-delivery-hover-5.csv",
    15: "samples/ground-truth-delivery-hover-15.csv",
}

EQUIVALENT = {"none": "unserved"}


def load(path):
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


extracted = {
    (int(row["map_index"]), row["state"]): row
    for row in load("out/map_coverage_rows.csv")
}

failures = []
checked = 0

for index in sorted(KEYS):
    for key_row in load(KEYS[index]):
        state = key_row["state"].strip()
        raw = key_row["transit_days"].strip()
        wants = [EQUIVALENT.get(value, value) for value in raw.split("|")]
        want = " or ".join(wants)

        got_row = extracted.get((index, state))
        if got_row is None:
            failures.append((index, state, want, "NOT EXTRACTED", ""))
            continue

        checked += 1
        got = got_row["outcome"]
        if got not in wants:
            failures.append((index, state, want, got, key_row.get("note", "") or ""))
        elif len(wants) > 1 and got_row["split"] != "yes":
            failures.append((index, state, "split=yes", "split=" + got_row["split"], "key calls this state ambiguous"))

print("checked  {}".format(checked))
print("failures {}".format(len(failures)))
print("")

for index, state, want, got, note in failures:
    print("  map {:>2}  {:<3} want {:<9} got {:<9} {}".format(index, state, want, got, note))

sys.exit(1 if failures else 0)