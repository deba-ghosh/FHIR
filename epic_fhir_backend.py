from fastapi import FastAPI, HTTPException
import jwt
import time
import uuid
import requests
from pydantic import BaseModel

# FastAPI instance
app = FastAPI(title="Epic FHIR Backend Integration", description="OAuth2 Client Credentials with JWT", version="1.0")

# Configuration
client_id = "4220d596-97d7-4488-a517-989486bdcec5"  # Replace with your Epic client ID
token_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"  # Replace with Epic token endpoint
fhir_url = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/Patient"  # Replace with FHIR base URL
private_key_path = 'C:/Users/User/Documents/Deba/Epic/FHIR Projects/Backend/privatekey.pem'  # Path to your RSA private key

# Load private key
with open(private_key_path, "r") as key_file:
    private_key = key_file.read()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class PatientResponse(BaseModel):
    status_code: int
    data: dict


def generate_jwt():
    """Generate JWT for client authentication"""
    jwt_headers = {
        "alg": "RS384",
        "typ": "JWT"
    }
    now = int(time.time())
    jwt_payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": token_url,
        "jti": str(uuid.uuid4()),
        "exp": now + 300,  # 5 minutes expiration
        "nbf": now,
        "iat": now
    }
    return jwt.encode(jwt_payload, private_key, algorithm="RS384", headers=jwt_headers)


@app.get("/get-token", response_model=TokenResponse)
async def get_token():
    """Fetch OAuth Token from Epic"""
    jwt_token = generate_jwt()
    token_data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token
    }

    response = requests.post(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@app.get("/get-patient", response_model=PatientResponse)
async def get_patient():
    """Fetch Patient Resource from Epic"""
    token_response = await get_token()
    access_token = token_response["access_token"]

    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/fhir+json"}
    response = requests.get(fhir_url, headers=headers)

    if response.status_code == 200:
        return {"status_code": 200, "data": response.json()}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

# Run with: uvicorn script_name:app --reload
