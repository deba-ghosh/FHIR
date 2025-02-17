from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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
FHIR_ID = "erXuFYUfucBZaryVksYEcMg3"  # Replace with actual FHIR ID for the patient

# Initialize FastAPI
app = FastAPI()


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
        "iat": int(iat.timestamp())  # Issued at time
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
    """Call the Epic FHIR server to get patient data by FHIR ID."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/fhir+json"  # Request JSON format explicitly
    }

    # Use the FHIR ID to get patient data
    patient_url = f"{FHIR_SERVER_URL}/Patient/{FHIR_ID}"  # Replace with actual FHIR ID

    try:
        # Log the full request URL for debugging
        logger.info(f"Requesting patient data from: {patient_url}")

        # Make the GET request to the FHIR server
        response = requests.get(patient_url, headers=headers)

        # Log the status code and raw response for further debugging
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.text}")

        # Check if the response is successful
        if response.status_code == 200:
            patient_data = response.json()
            logger.info(f"Patient data retrieved successfully: {json.dumps(patient_data, indent=2)}")
            return patient_data
        else:
            logger.error(f"Failed to fetch patient data. Status Code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Failed to fetch patient data: {response.text}")

    except Exception as e:
        logger.error(f"Error fetching patient data: {e}")
        raise


# FastAPI endpoint to get patient data with parsed HTML output
@app.get("/get_patient_data", response_class=HTMLResponse)
async def get_patient_data_endpoint():
    try:
        # Step 1: Generate JWT
        jwt_token = generate_jwt()
        logger.info(f"Generated JWT: {jwt_token}")

        # Step 2: Get access token
        access_token = get_access_token(jwt_token)

        # Step 3: Call the Patient resource
        patient_data = get_patient_data(access_token)

        # Generate HTML response with parsed data
        html_content = f"""
        <html>
            <head>
                <title>Patient Data</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    table, th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                </style>
            </head>
            <body>
                <h1>Patient Information</h1>
                <table>
                    <tr><th>Field</th><th>Value</th></tr>
                    <tr><td><strong>Name</strong></td><td>{patient_data['name'][0]['text']}</td></tr>
                    <tr><td><strong>Gender</strong></td><td>{patient_data['gender']}</td></tr>
                    <tr><td><strong>Birth Date</strong></td><td>{patient_data['birthDate']}</td></tr>
                    <tr><td><strong>Phone</strong></td><td>{', '.join([t['value'] for t in patient_data['telecom'] if t['system'] == 'phone'])}</td></tr>
                    <tr><td><strong>Email</strong></td><td>{', '.join([t['value'] for t in patient_data['telecom'] if t['system'] == 'email'])}</td></tr>
                    <tr><td><strong>Address</strong></td><td>{', '.join([f"{a['line'][0]}, {a['city']}, {a['state']} {a['postalCode']}" for a in patient_data['address']])}</td></tr>
                    <tr><td><strong>Marital Status</strong></td><td>{patient_data['maritalStatus']['text']}</td></tr>
                </table>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
