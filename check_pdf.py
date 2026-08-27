import csv

EXPECTED = {
    1:  ("standard_das", ["01002", "01007", "01010", "01029", "01032", "01033", "01036", "01038"]),
    25: ("standard_das", ["98385", "98392", "98395", "98439", "98512", "98520", "98522", "98524"]),
    26: ("extended_das", ["01005", "01008", "01011", "01012", "01026", "01031", "01034", "01037"]),
    89: ("extended_das", ["99180", "99181", "99185", "99301", "99320", "99321", "99322", "99326"]),
}

with open("out/zip_surcharge_rows.csv", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

failures = 0

for page in sorted(EXPECTED):
    want_tier, want_zips = EXPECTED[page]
    on_page = [row for row in rows if int(row["page"]) == page]
    got_zips = [row["zip5"] for row in on_page[:8]]
    got_tiers = set(row["tier"] for row in on_page)

    zip_ok = got_zips == want_zips
    tier_ok = got_tiers == {want_tier}

    if not zip_ok:
        failures += 1
        print("page {:>2} ZIP MISMATCH".format(page))
        print("   want {}".format(want_zips))
        print("   got  {}".format(got_zips))

    if not tier_ok:
        failures += 1
        print("page {:>2} TIER MISMATCH want {} got {}".format(page, want_tier, sorted(got_tiers)))

    if zip_ok and tier_ok:
        print("page {:>2} ok  {} rows  {}".format(page, len(on_page), want_tier))

print("")
print("failures {}".format(failures))