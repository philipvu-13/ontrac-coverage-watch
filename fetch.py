import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HEADERS = {"User-Agent": "ontrac-coverage-watch/0.1 (philiphvu13@gmail.com)"}
TIMEOUT = 60
RETRIES = 4
BACKOFF_SECONDS = 3
PAUSE_SECONDS = 1
OUT_ROOT = Path("out")

MAP_BASE = "https://www.ontrac.com/wp-content/themes/ontrac/assets/images/map/"
ZIP_PDF = "https://www.ontrac.com/wp-content/uploads/pdf/ontrac-area-surcharge-zip-codes.pdf"


def coverage_map_files():
    files = []
    for index in range(1, 19):
        name = "delivery-hover-{}.png".format(index)
        files.append((name, MAP_BASE + name))
    return files


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
        "files": [("document.pdf", ZIP_PDF)],
    },
]


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


def build_key(slug, dt, filename):
    return "raw/source={}/dt={}/{}".format(slug, dt, filename)


def validate(source, body, content_type):
    want = source["content_type"]
    if want not in content_type:
        raise ValueError("content type {}, expected {}".format(content_type, want))
    if len(body) < source["min_bytes"]:
        raise ValueError("only {} bytes".format(len(body)))


def store(key, body):
    path = OUT_ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def main():
    dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print("run dt={}".format(dt))

    for source in SOURCES:
        slug = source["slug"]
        print("")
        print("{}  {} files".format(slug, len(source["files"])))

        for filename, url in source["files"]:
            key = build_key(slug, dt, filename)

            if (OUT_ROOT / key).exists():
                print("  skip  {}".format(filename))
                continue

            try:
                response = get_with_retry(url)
                body = response.content
                content_type = response.headers.get("Content-Type", "")
                validate(source, body, content_type)
                store(key, body)

                digest = hashlib.sha256(body).hexdigest()
                meta = {
                    "slug": slug,
                    "filename": filename,
                    "source_url": url,
                    "source_type": "live",
                    "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "bytes": len(body),
                    "sha256": digest,
                }
                meta_key = build_key(slug, dt, filename + ".meta.json")
                store(meta_key, json.dumps(meta, indent=2).encode("utf-8"))

                print("  ok    {:<24} {:>8} bytes".format(filename, len(body)))

            except Exception as error:
                print("  FAIL  {}  {}".format(filename, error))

            time.sleep(PAUSE_SECONDS)

    print("")
    print("done")


if __name__ == "__main__":
    main()