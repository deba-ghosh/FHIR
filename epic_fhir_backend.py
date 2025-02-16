import requests
from fastapi import FastAPI
from fastapi.logger import logger
import jwt
import datetime
import uuid

# FastAPI instance
app = FastAPI()

# Configuration (replace with your actual values)
client_id = 'your-client-id'
client_secret = 'your-client-secret'
token_url = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'
patient_url = 'https://fhir.epic.com/interconnect-fhir/patient'
private_key = 'your-private-key'  # The private key used to sign JWT (replace with your actual key)


# Function to generate the JWT
def generate_jwt():
    now = datetime.datetime.now(datetime.timezone.utc)  # Use UTC timezone-aware datetime
    exp_time = now + datetime.timedelta(minutes=5)  # Expires in 5 minutes

    # JWT payload
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": token_url,
        "jti": str(uuid.uuid4()),
        "exp": int(exp_time.timestamp()),
        "nbf": int(now.timestamp()),
        "iat": int(now.timestamp())
    }

    # Encode JWT with RS384 algorithm
    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS384')
    return encoded_jwt


# Function to get access token from Epic
def get_access_token():
    jwt_token = generate_jwt()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'assertion': jwt_token
    }

    response = requests.post(token_url, headers=headers, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        logger.error(f"Failed to get access token. Status Code: {response.status_code}")
        logger.error(response.text)
        return None


# Function to fetch the patient resource
def fetch_patient(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(patient_url, headers=headers)

    if response.status_code == 200:
        logger.info("Patient data fetched successfully.")
        return response.json()  # Return patient data
    else:
        logger.error(f"Failed to fetch patient. Status Code: {response.status_code}")
        return None


# FastAPI root endpoint to trigger the flow
@app.get("/")
async def root():
    logger.info("Starting authentication and patient fetch process.")

    # Authenticate and get access token
    access_token = get_access_token()
    if not access_token:
        return {"error": "Authentication failed. Could not obtain access token."}

    # Fetch the patient resource
    patient_data = fetch_patient(access_token)
    if patient_data:
        logger.info("Successfully fetched patient data.")
        return {"patient": patient_data}
    else:
        return {"error": "Failed to fetch patient data."}


# Health check endpoint (for testing)
@app.get("/health")
async def health():
    return {"status": "ok"}
