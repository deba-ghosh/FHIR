import json
import time
import logging
import requests
import jwt
from datetime import datetime, timedelta, timezone


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Configuration (replace with actual values)
PRIVATE_KEY_PATH = 'C:/Users/User/Documents/Deba/Epic/FHIR Projects/Backend/privatekey.pem'
CLIENT_ID = '4220d596-97d7-4488-a517-989486bdcec5'
TOKEN_URL = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'
FHIR_SERVER_URL = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4'
patient_id = "203713"  # Replace with an actual Patient ID

# Generate JWT signed with the private key
def generate_jwt():
    """Generate a JWT for authentication."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=5)  # Expiration time (max 5 minutes)
    iat = now
    jti = str(int(time.time() * 1000))  # Unique identifier for the JWT

    # JWT Header
    headers = {
        "alg": "RS384",
        "typ": "JWT"
    }

    # JWT Payload
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,  # The token endpoint
        "jti": jti,
        "exp": int(exp.timestamp()),  # Expiration time
        "nbf": int(iat.timestamp()),  # Not before time
        "iat": int(iat.timestamp())   # Issued at time
    }

    # Read the private key (replace with your key file path)
    with open(PRIVATE_KEY_PATH, 'r') as key_file:
        private_key = key_file.read()

    # Generate the JWT
    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS384', headers=headers)
    return encoded_jwt


# Request an access token using the JWT
def get_access_token(jwt_token):
    """Request an access token using the JWT."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",  # As per Epic's instructions
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",  # As per Epic's instructions
        "client_assertion": jwt_token  # The JWT you created
    }

    # Request the token from Epic
    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get('access_token')
        logger.info(f"Access token obtained successfully: {access_token}")
        return access_token
    else:
        logger.error(f"Failed to get access token. Status Code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        raise Exception("Failed to get access token")


# Call the Patient resource using the access token
def get_patient_data(access_token):
    """Call the Epic FHIR server to get patient data."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    patient_url = f"{FHIR_SERVER_URL}/Patient?identifier=MRN|{patient_id}"  # You can modify the resource URL as needed

    # Make the GET request to the FHIR server
    response = requests.get(patient_url, headers=headers)

    if response.status_code == 200:
        patient_data = response.json()
        logger.info(f"Patient data retrieved successfully: {patient_data}")
        return patient_data
    else:
        logger.error(f"Failed to fetch patient data. Status Code: {response.status_code}")
        logger.error(f"Response: {response.text}")
        raise Exception(f"Failed to fetch patient data: {response.text}")


# Main function to authenticate and call the Patient resource
def main():
    try:
        # Step 1: Generate JWT
        jwt_token = generate_jwt()
        logger.info(f"Generated JWT: {jwt_token}")

        # Step 2: Get access token
        access_token = get_access_token(jwt_token)

        # Step 3: Call the Patient resource
        patient_data = get_patient_data(access_token)

        # Print the patient data (for testing purposes)
        logger.info(f"Patient data: {json.dumps(patient_data, indent=2)}")

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
