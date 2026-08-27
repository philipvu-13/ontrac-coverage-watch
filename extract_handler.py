import csv
import io
import json
import os

import boto3

from extract_maps import BUCKET, MAP_FIELDS, build_rows
from parse_pdf import FIELDS as PDF_FIELDS, parse

POINTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state_points.json")


def latest_dt(s3, slug):
    prefix = "raw/source={}/".format(slug)
    result = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix, Delimiter="/")

    dates = []
    for entry in result.get("CommonPrefixes", []):
        part = entry["Prefix"][len(prefix):].strip("/")
        if part.startswith("dt="):
            dates.append(part[3:])

    if not dates:
        raise ValueError("no captures under {}".format(prefix))
    return sorted(dates)[-1]


def write_csv(s3, key, fields, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
    print("wrote {}  {} rows".format(key, len(rows)))
    return key


def run(event):
    s3 = boto3.client("s3")

    dt_maps = event.get("dt_maps") or latest_dt(s3, "coverage-maps")
    dt_pdf = event.get("dt_pdf") or latest_dt(s3, "zip-surcharge")
    print("maps dt={}  pdf dt={}".format(dt_maps, dt_pdf))

    with open(POINTS, encoding="utf-8") as handle:
        points = json.load(handle)

    map_rows = build_rows(s3, dt_maps, points)
    write_csv(
        s3,
        "structured/source=coverage-maps/dt={}/rows.csv".format(dt_maps),
        MAP_FIELDS,
        map_rows,
    )

    pdf_key = "raw/source=zip-surcharge/dt={}/document.pdf".format(dt_pdf)
    body = s3.get_object(Bucket=BUCKET, Key=pdf_key)["Body"].read()
    pdf_rows = parse(io.BytesIO(body))
    write_csv(
        s3,
        "structured/source=zip-surcharge/dt={}/rows.csv".format(dt_pdf),
        PDF_FIELDS,
        pdf_rows,
    )

    summary = {
        "bucket": BUCKET,
        "dt_maps": dt_maps,
        "dt_pdf": dt_pdf,
        "map_rows": len(map_rows),
        "pdf_rows": len(pdf_rows),
        "map_no_data": sum(1 for row in map_rows if row["outcome"] == "no_data"),
        "map_split": sum(1 for row in map_rows if row["split"] == "yes"),
    }

    print(json.dumps(summary))
    return summary


def lambda_handler(event, context):
    return run(event or {})


if __name__ == "__main__":
    run({})