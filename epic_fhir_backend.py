import logging
import jwt
import requests
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException

# FastAPI app initialization
app = FastAPI()

# Setup logging
logging.basicConfig(
    format='%(message)s',
    level=logging.INFO
)

# Config variables (Make sure to replace these with your actual values)
CLIENT_ID = "your-client-id"
PRIVATE_KEY_PATH = "path/to/your/private_key.pem"
AUTH_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
FHIR_BASE_URL = "https://fhir.epic.com/interconnect-fhir/api/FHIR/dstu2"


# Helper function to generate JWT
def generate_jwt():
    private_key = open(PRIVATE_KEY_PATH, "r").read()
    now = datetime.now(timezone.utc)
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": AUTH_URL,
        "jti": str(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "nbf": int(now.timestamp()),
        "iat": int(now.timestamp())
    }

    # Encode JWT with RS256
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256", headers={"alg": "RS256", "typ": "JWT"})
    return encoded_jwt


# Function to get access token
def get_access_token():
    jwt_token = generate_jwt()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {jwt_token}'
    }

    data = {
        'grant_type': 'client_credentials',
        'scope': 'patient/Patient.read'
    }

    response = requests.post(AUTH_URL, headers=headers, data=data)
    if response.status_code != 200:
        logging.error(f"Failed to get access token: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to get access token: {response.text}")

    access_token = response.json().get('access_token')
    logging.info("Access token obtained successfully.")
    return access_token


# Endpoint to check health
@app.get("/health")
async def health_check():
    return {"status": "OK"}


# Endpoint to get patient information
@app.get("/patient")
async def get_patient():
    try:
        access_token = get_access_token()
    except HTTPException:
        raise HTTPException(status_code=500, detail="Authentication failed.")

    # Call Epic FHIR Patient resource
    patient_url = f"{FHIR_BASE_URL}/Patient"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(patient_url, headers=headers)

    if response.status_code == 404:
        logging.error(f"Patient resource not found. Status Code: {response.status_code}")
        raise HTTPException(status_code=404, detail="Patient resource not found.")
    elif response.status_code != 200:
        logging.error(f"Failed to fetch patient. Status Code: {response.status_code}, Response: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch patient. {response.text}")

    patient_data = response.json()
    logging.info("Patient data fetched successfully.")
    return patient_data
