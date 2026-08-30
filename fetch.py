import hashlib
import json
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import boto3
import requests
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

HEADERS = {"User-Agent": "ontrac-coverage-watch/0.1 (philiphvu13@gmail.com)"}
TIMEOUT = 60
RETRIES = 4
BACKOFF_SECONDS = 3
PAUSE_SECONDS = 1

BUCKET = "unclephil-ontrac-coverage-raw"
s3 = boto3.client("s3")

MAP_BASE = "https://www.ontrac.com/wp-content/themes/ontrac/assets/images/map/"
SURCHARGE_PAGE = "https://www.ontrac.com/surchargesandrates/"
SERVICE_ALERTS = "https://www.ontrac.com/service-alerts/"


def get_with_retry(url):
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except Exception as error:
            last_error = error
            if attempt < RETRIES:
                wait = BACKOFF_SECONDS * 2 ** (attempt - 1)
                print("      retry {} in {}s".format(attempt, wait))
                time.sleep(wait)
    raise last_error


def coverage_map_files():
    files = []
    for index in range(1, 19):
        name = "delivery-hover-{}.png".format(index)
        files.append((name, MAP_BASE + name))
    return files


def resolve_zip_pdf_url():
    response = get_with_retry(SURCHARGE_PAGE)
    soup = BeautifulSoup(response.text, "html.parser")

    for anchor in soup.find_all("a"):
        label = " ".join(anchor.get_text().split()).lower()
        if "current" in label and "das" in label and "zip" in label:
            href = anchor.get("href")
            if not href:
                continue
            absolute = urljoin(SURCHARGE_PAGE, href)
            clean = absolute.split("?")[0]
            print("  link  {} -> {}".format(label, clean))
            return clean

    raise ValueError("no anchor matching current das zip on {}".format(SURCHARGE_PAGE))


SOURCES = [
    {
        "slug": "coverage-maps",
        "content_type": "image/png",
        "min_bytes": 20000,
        "files": coverage_map_files(),
    },
    {
        "slug": "zip-surcharge",
        "content_type": "application/pdf",
        "min_bytes": 20000,
        "resolve": resolve_zip_pdf_url,
        "resolved_from": SURCHARGE_PAGE,
    },

        {
        "slug": "service-alerts",
        "content_type": "text/html",
        "min_bytes": 10000,
        "files": [("document.html", SERVICE_ALERTS)],
    },
]


def build_key(slug, dt, filename):
    return "raw/source={}/dt={}/{}".format(slug, dt, filename)


def validate(source, body, content_type):
    want = source["content_type"]
    if want not in content_type:
        raise ValueError("content type {}, expected {}".format(content_type, want))
    if len(body) < source["min_bytes"]:
        raise ValueError("only {} bytes".format(len(body)))


def exists(key):
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except ClientError as error:
        if error.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def store(key, body, content_type):
    s3.put_object(Bucket=BUCKET, Key=key, Body=body, ContentType=content_type)
    return key


def run():
    dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print("run dt={} bucket={}".format(dt, BUCKET))

    stored = 0
    skipped = 0
    failed = 0

    for source in SOURCES:
        slug = source["slug"]
        resolved_from = source.get("resolved_from")

        if "resolve" in source:
            try:
                url = source["resolve"]()
                files = [("document.pdf", url)]
            except Exception as error:
                failed += 1
                print("{} FAIL resolve  {}".format(slug, error))
                continue
        else:
            files = source["files"]

        print("{} {} files".format(slug, len(files)))

        for filename, url in files:
            key = build_key(slug, dt, filename)

            if exists(key):
                skipped += 1
                print("  skip  {}".format(filename))
                continue

            try:
                response = get_with_retry(url)
                body = response.content
                content_type = response.headers.get("Content-Type", "")
                validate(source, body, content_type)
                store(key, body, source["content_type"])

                digest = hashlib.sha256(body).hexdigest()
                meta = {
                    "slug": slug,
                    "filename": filename,
                    "source_url": url,
                    "resolved_from": resolved_from,
                    "source_type": "live",
                    "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "bytes": len(body),
                    "sha256": digest,
                }
                meta_key = build_key(slug, dt, filename + ".meta.json")
                body_json = json.dumps(meta, indent=2).encode("utf-8")
                store(meta_key, body_json, "application/json")

                stored += 1
                print("  ok    {:<24} {:>8} bytes".format(filename, len(body)))

            except Exception as error:
                failed += 1
                print("  FAIL  {}  {}".format(filename, error))

            time.sleep(PAUSE_SECONDS)

    summary = {
        "dt": dt,
        "bucket": BUCKET,
        "stored": stored,
        "skipped": skipped,
        "failed": failed,
    }
    print(json.dumps(summary))
    return summary


def lambda_handler(event, context):
    return run()


if __name__ == "__main__":
    run()