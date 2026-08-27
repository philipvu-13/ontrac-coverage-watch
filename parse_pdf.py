import csv
import re
import sys

import pdfplumber

PDF = sys.argv[1] if len(sys.argv) > 1 else "out/ontrac-zip-2026.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out/zip_surcharge_rows.csv"

ZIP_RE = re.compile(r"^\d{5}$")
DATE_RE = re.compile(r"Effective\s+(.+)$")


def tier_of(header):
    if header.startswith("Extended"):
        return "extended_das"
    return "standard_das"


def effective_of(header):
    match = DATE_RE.search(header)
    if match:
        return match.group(1).strip()
    return ""


def parse(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            lines = (page.extract_text() or "").splitlines()
            if len(lines) < 2:
                continue

            header = lines[1]
            tier = tier_of(header)
            effective = effective_of(header)

            for line in lines[2:]:
                tokens = line.split()
                if not tokens:
                    continue
                if not all(ZIP_RE.match(token) for token in tokens):
                    continue
                for token in tokens:
                    rows.append({
                        "zip5": token,
                        "tier": tier,
                        "effective_date": effective,
                        "page": number,
                        "provenance": "area_surcharge_pdf",
                        "confidence": "confirmed",
                    })
    return rows


def main():
    rows = parse(PDF)

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "zip5", "tier", "effective_date", "page", "provenance", "confidence",
        ])
        writer.writeheader()
        writer.writerows(rows)

    zips = [row["zip5"] for row in rows]
    standard = sum(1 for row in rows if row["tier"] == "standard_das")

    print("rows        {}".format(len(rows)))
    print("standard    {}".format(standard))
    print("extended    {}".format(len(rows) - standard))
    print("unique zips {}".format(len(set(zips))))
    print("duplicates  {}".format(len(zips) - len(set(zips))))
    print("wrote       {}".format(OUT))


if __name__ == "__main__":
    main()