import logging
import requests
import jwt
import uuid
import time
from fastapi import FastAPI, HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Epic OAuth & FHIR Configuration
CLIENT_ID = "4220d596-97d7-4488-a517-989486bdcec5"  # Replace with your Epic client ID
PRIVATE_KEY_PATH = 'C:/Users/User/Documents/Deba/Epic/FHIR Projects/Backend/privatekey.pem'  # Path to your private key for JWT signing
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
FHIR_BASE_URL = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"


# Function to generate JWT for authentication
def generate_jwt():
    current_time = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "jti": str(uuid.uuid4()),
        "exp": current_time + 300,  # Expires in 5 minutes
        "nbf": current_time,
        "iat": current_time
    }

    with open(PRIVATE_KEY_PATH, "r") as key_file:
        private_key = key_file.read()

    jwt_token = jwt.encode(payload, private_key, algorithm="RS384")
    logging.info(f"✅ JWT successfully created for authentication.")

    return jwt_token


# Function to get an access token from Epic
def get_access_token():
    jwt_token = generate_jwt()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token
    }

    logging.info(f"🔄 Requesting access token from Epic...")

    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        logging.info(f"✅ Authentication successful. Access token received: {access_token[:10]}... (truncated)")
        return access_token
    else:
        logging.error(f"❌ Authentication failed: {response.text}")
        raise HTTPException(status_code=response.status_code, detail="Authentication failed")


# API to fetch Patient resource
@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    access_token = get_access_token()

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"

    logging.info(f"🔄 Fetching patient resource: {url}")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        logging.info(f"✅ Successfully retrieved patient data.")
        return response.json()
    else:
        logging.error(f"❌ Failed to fetch patient data: {response.text}")
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch patient data")
