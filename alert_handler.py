import json
import os

import boto3
import snowflake.connector
from cryptography.hazmat.primitives import serialization

SECRET_ID = os.environ["SNOWFLAKE_KEY_SECRET"]
TOPIC_ARN = os.environ["ALERT_TOPIC_ARN"]
ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
USER = os.environ["SNOWFLAKE_USER"]
ROLE = os.environ["SNOWFLAKE_ROLE"]
WAREHOUSE = os.environ["SNOWFLAKE_WAREHOUSE"]
DATABASE = os.environ["SNOWFLAKE_DATABASE"]

QUERY = """
select
    captured_on,
    compared_to,
    source,
    confidence,
    added,
    removed,
    changed,
    total_changes,
    summary
from ontrac.marts.alert_change_summary
where captured_on = (select max(captured_on) from ontrac.marts.alert_change_summary)
order by source
"""


def private_key_der():
    secret = boto3.client("secretsmanager").get_secret_value(SecretId=SECRET_ID)
    key = serialization.load_pem_private_key(
        secret["SecretString"].encode("utf-8"), password=None
    )
    return key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def fetch_rows():
    connection = snowflake.connector.connect(
        account=ACCOUNT,
        user=USER,
        role=ROLE,
        warehouse=WAREHOUSE,
        database=DATABASE,
        private_key=private_key_der(),
    )
    try:
        cursor = connection.cursor()
        cursor.execute(QUERY)
        columns = [column[0].lower() for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        connection.close()


def build_message(rows):
    total = sum(row["total_changes"] for row in rows)

    lines = [
        "OnTrac coverage changed.",
        "",
        "Capture {} compared against the previous capture on {}.".format(
            rows[0]["captured_on"], rows[0]["compared_to"]
        ),
        "{} changes in total.".format(total),
        "",
    ]

    for row in [row for row in rows if row["total_changes"] > 0]:
        lines.append(row["summary"])
        lines.append("Source {}, confidence {}.".format(row["source"], row["confidence"]))
        lines.append("")

    lines.append(
        "A ZIP code appearing in or disappearing from the surcharge listing is a confirmed "
        "change, read directly from the PDF OnTrac publishes."
    )
    lines.append(
        "A change read from the coverage map images is inferred at state level and is a "
        "signal rather than a fact."
    )
    lines.append("")
    lines.append(
        "Detail sits in ONTRAC.MARTS.FCT_ZIP_SURCHARGE_CHANGES and "
        "ONTRAC.MARTS.FCT_MAP_COVERAGE_CHANGES."
    )

    return "\n".join(lines)


def run():
    rows = fetch_rows()
    total = sum(row["total_changes"] for row in rows)

    if not rows or total == 0:
        print("checked {} sources, nothing changed".format(len(rows)))
        return {"published": False, "rows": len(rows), "total_changes": total}

    message = build_message(rows)
    subject = "OnTrac coverage changed, {} updates".format(total)[:100]

    boto3.client("sns").publish(
        TopicArn=TOPIC_ARN, Subject=subject, Message=message
    )

    print(message)
    return {"published": True, "rows": len(rows), "total_changes": total}


def lambda_handler(event, context):
    return run()


if __name__ == "__main__":
    print(json.dumps(run()))