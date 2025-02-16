import logging
import datetime
import requests
import jwt
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

# FastAPI instance
app = FastAPI()

# Configure logger
logger = logging.getLogger("epic_fhir_backend")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# FHIR Server URLs and authentication details
FHIR_SERVER_BASE_URL = "https://fhir.epic.com/interconnect-fhir"
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
CLIENT_ID = "your-client-id"  # Replace with your client ID
CLIENT_SECRET = "your-client-secret"  # Replace with your client secret
JWK_SET_URL = "your-jwk-set-url"  # Replace with your JWK set URL
PATIENT_RESOURCE_URL = f"{FHIR_SERVER_BASE_URL}/Patient"


# JWT creation function
def create_jwt():
    # Prepare JWT payload and header
    headers = {
        "alg": "RS384",
        "typ": "JWT",
        "kid": "your-kid",  # Replace with your key ID
        "jku": JWK_SET_URL
    }

    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "jti": str(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        "exp": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)).timestamp()),
        "nbf": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    }

    # Load private key and sign the JWT (for this example, we'll use a simple RS384 key)
    private_key = open("your-private-key.pem", "r").read()  # Replace with your private key file
    jwt_token = jwt.encode(payload, private_key, algorithm="RS384", headers=headers)

    return jwt_token


# Token request function
def get_access_token():
    logger.info("Generating JWT for OAuth2 authentication...")
    jwt_token = create_jwt()

    # Exchange JWT for access token
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "assertion": jwt_token
    }

    logger.info(f"Sending request to {TOKEN_URL} for access token...")
    response = requests.post(TOKEN_URL, data=data, headers=headers)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        logger.info("Successfully authenticated and received access token.")
        return access_token
    else:
        logger.error(f"Authentication failed. Status Code: {response.status_code}")
        logger.error(response.text)
        return None


# Fetch patient resource
def fetch_patient_data():
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to authenticate"}

    # Request patient data from the FHIR server
    headers = {"Authorization": f"Bearer {access_token}"}
    logger.info(f"Sending request to {PATIENT_RESOURCE_URL} to fetch patient data...")
    response = requests.get(PATIENT_RESOURCE_URL, headers=headers)

    if response.status_code == 200:
        logger.info(f"Successfully fetched patient data.")
        return response.json()
    else:
        logger.error(f"Failed to fetch patient data. Status Code: {response.status_code}")
        logger.error(response.text)
        return {"error": f"Failed to fetch patient. Status Code: {response.status_code}"}


# Pydantic model to represent the patient data
class PatientData(BaseModel):
    resourceType: str
    id: str
    name: Optional[str]


# Health check route
@app.get("/health")
def health_check():
    return {"status": "OK"}


# Endpoint to call Patient resource
@app.get("/patient")
def get_patient_data():
    patient_data = fetch_patient_data()
    if "error" in patient_data:
        return {"error": patient_data["error"]}

    # Parse the patient data and return
    return PatientData(resourceType=patient_data.get("resourceType", ""), id=patient_data.get("id", ""),
                       name=patient_data.get("name", ""))
