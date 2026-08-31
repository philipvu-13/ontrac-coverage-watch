import csv
import io
import json
import os

import boto3
import requests
from bs4 import BeautifulSoup

from extract_maps import BUCKET, MAP_FIELDS, build_rows
from parse_pdf import FIELDS as PDF_FIELDS, parse

POINTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state_points.json")

ANTHROPIC_SECRET = os.environ.get("ANTHROPIC_KEY_SECRET", "ontrac/anthropic-key")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

GITHUB_SECRET = os.environ.get("GITHUB_TOKEN_SECRET", "ontrac/github-token")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "philipvu-13/ontrac-coverage-watch")
GITHUB_WORKFLOW = os.environ.get("GITHUB_WORKFLOW", "dbt.yml")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "master")

ALERT_FIELDS = [
    "captured_on", "characters", "provenance", "confidence", "source_key", "alert_text",
]

PARSED_FIELDS = [
    "captured_on", "event_type", "cause", "posted_date", "states", "cities",
    "summary", "provenance", "confidence", "model", "source_key",
]

PROMPT = (
    "You are given the visible text of OnTrac's public Service Alerts page.\n"
    "Return ONLY a JSON array. No prose, no explanation, no code fences.\n"
    "One object per distinct service alert, with exactly these keys.\n"
    "  event_type   a short label such as weather, fire, holiday, facility\n"
    "  cause        the stated cause in a few words\n"
    "  posted_date  ISO date if the page states one, otherwise null\n"
    "  states       array of two letter US state codes named or clearly implied\n"
    "  cities       array of city names named\n"
    "  summary      one sentence in plain language\n"
    "Use null or an empty array where the text does not say.\n"
    "If the page shows no current alerts, return an empty array.\n\n"
    "Page text follows.\n\n"
)


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


def extract_alerts(s3, dt):
    key = "raw/source=service-alerts/dt={}/document.html".format(dt)
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()

    soup = BeautifulSoup(body, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    main = soup.find("main") or soup.body
    text = " ".join(main.get_text(" ").split())

    return [{
        "captured_on": dt,
        "characters": len(text),
        "provenance": "service_alerts_html",
        "confidence": "confirmed",
        "source_key": key,
        "alert_text": text,
    }]


def anthropic_headers():
    secret = boto3.client("secretsmanager").get_secret_value(SecretId=ANTHROPIC_SECRET)
    return {
        "x-api-key": secret["SecretString"].strip(),
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }


def call_anthropic(text):
    headers = anthropic_headers()
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": PROMPT + text}],
    }

    response = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        print("anthropic {} {}".format(response.status_code, response.text[:600]))
        listing = requests.get(
            "https://api.anthropic.com/v1/models", headers=headers, timeout=30
        )
        print("available models {}".format(listing.text[:1200]))
        response.raise_for_status()

    raw = response.json()["content"][0]["text"].strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


def parsed_rows(dt, alert_text, source_key):
    rows = []

    for alert in call_anthropic(alert_text):
        rows.append({
            "captured_on": dt,
            "event_type": alert.get("event_type"),
            "cause": alert.get("cause"),
            "posted_date": alert.get("posted_date"),
            "states": "|".join(alert.get("states") or []),
            "cities": "|".join(alert.get("cities") or []),
            "summary": alert.get("summary"),
            "provenance": "service_alerts_html",
            "confidence": "llm_extracted",
            "model": ANTHROPIC_MODEL,
            "source_key": source_key,
        })

    return rows


def trigger_dbt():
    secret = boto3.client("secretsmanager").get_secret_value(SecretId=GITHUB_SECRET)

    url = "https://api.github.com/repos/{}/actions/workflows/{}/dispatches".format(
        GITHUB_REPO, GITHUB_WORKFLOW
    )
    headers = {
        "Authorization": "Bearer {}".format(secret["SecretString"].strip()),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.post(url, headers=headers, json={"ref": GITHUB_BRANCH}, timeout=30)

    if response.status_code != 204:
        raise RuntimeError(
            "github dispatch {} {}".format(response.status_code, response.text[:400])
        )

    print("dbt workflow dispatched on {}".format(GITHUB_BRANCH))


def run(event):
    s3 = boto3.client("s3")

    dt_maps = event.get("dt_maps") or latest_dt(s3, "coverage-maps")
    dt_pdf = event.get("dt_pdf") or latest_dt(s3, "zip-surcharge")
    dt_alerts = event.get("dt_alerts") or latest_dt(s3, "service-alerts")
    print("maps dt={}  pdf dt={}  alerts dt={}".format(dt_maps, dt_pdf, dt_alerts))

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

    alert_rows = extract_alerts(s3, dt_alerts)
    write_csv(
        s3,
        "structured/source=service-alerts/dt={}/rows.csv".format(dt_alerts),
        ALERT_FIELDS,
        alert_rows,
    )

    try:
        rows = parsed_rows(
            dt_alerts, alert_rows[0]["alert_text"], alert_rows[0]["source_key"]
        )
        write_csv(
            s3,
            "structured/source=service-alerts-parsed/dt={}/rows.csv".format(dt_alerts),
            PARSED_FIELDS,
            rows,
        )
        parsed_count = len(rows)
    except Exception as error:
        parsed_count = -1
        print("FAIL alert parse  {}".format(error))

    try:
        trigger_dbt()
        dbt_triggered = True
    except Exception as error:
        dbt_triggered = False
        print("FAIL dbt dispatch  {}".format(error))

    summary = {
        "bucket": BUCKET,
        "dt_maps": dt_maps,
        "dt_pdf": dt_pdf,
        "dt_alerts": dt_alerts,
        "map_rows": len(map_rows),
        "pdf_rows": len(pdf_rows),
        "alert_characters": alert_rows[0]["characters"],
        "parsed_alerts": parsed_count,
        "dbt_triggered": dbt_triggered,
        "map_no_data": sum(1 for row in map_rows if row["outcome"] == "no_data"),
        "map_split": sum(1 for row in map_rows if row["split"] == "yes"),
    }

    print(json.dumps(summary))
    return summary


def lambda_handler(event, context):
    return run(event or {})


if __name__ == "__main__":
    run({})