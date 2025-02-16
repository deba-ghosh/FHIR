from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import json
import base64

def convert_pem_to_jwk(pem_file):
    with open(pem_file, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    numbers = public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": base64.urlsafe_b64encode(numbers.n.to_bytes(256, "big")).decode().rstrip("="),
        "e": base64.urlsafe_b64encode(numbers.e.to_bytes(3, "big")).decode().rstrip("="),
    }

    return json.dumps({"keys": [jwk]}, indent=2)

# Convert and save the JWK Set file
jwk_set = convert_pem_to_jwk("public_key.pem")
with open("jwks.json", "w") as f:
    f.write(jwk_set)

print(jwk_set)  # Print to verify