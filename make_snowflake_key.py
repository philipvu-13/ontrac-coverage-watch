from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

OUT_DIR = Path.home() / ".snowflake"
OUT_DIR.mkdir(exist_ok=True)

private_path = OUT_DIR / "ontrac_dbt_key.p8"
public_path = OUT_DIR / "ontrac_dbt_key.pub"

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

private_path.write_bytes(key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
))

public_bytes = key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_path.write_bytes(public_bytes)

body = public_bytes.decode("utf-8")
body = body.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "")
body = "".join(body.split())

print("private key {}".format(private_path))
print("public key  {}".format(public_path))
print("")
print("ALTER USER UNCLEPHIL SET RSA_PUBLIC_KEY='{}';".format(body))