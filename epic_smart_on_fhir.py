import requests
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import logging
from xml.dom import minidom

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("epic_smart_on_fhir")

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Epic FHIR OAuth2 Details
CLIENT_ID = "293de336-3a05-4ded-ac16-ec140c665796"
REDIRECT_URI = "http://localhost:8080/callback"  # Make sure this matches the one registered with Epic
AUTH_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
FHIR_SERVER = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"


# Pretty-printing XML function
def pretty_print_xml(xml_data):
    # Parse the XML data and pretty-print it
    xml_obj = minidom.parseString(xml_data)
    pretty_xml = xml_obj.toprettyxml(indent="  ")
    return pretty_xml


@app.get("/")
async def home(request: Request):
    """ Renders the home page with a Sign-in button """
    authorize_link = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=patient.read%20patient.search"
        f"&state=1234&aud={FHIR_SERVER}/api/FHIR/R4"  # Added the aud parameter
    )
    logger.debug(f"Authorization link: {authorize_link}")

    return templates.TemplateResponse(
        "index.html", {"request": request, "authorize_link": authorize_link}
    )


@app.get("/callback")
async def callback(request: Request):
    """ Handles Epic OAuth2 callback and exchanges code for token """
    code = request.query_params.get("code")
    if not code:
        return {"error": "Authorization failed. No code received."}

    # Exchange authorization code for access token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
    }

    response = requests.post(TOKEN_URL, data=token_data)

    try:
        token_response = response.json()  # Parse the response as JSON
    except ValueError as e:
        logger.error(f"Failed to parse token response as JSON: {e}")
        return {"error": "Failed to parse token response", "details": response.text}

    if "access_token" not in token_response:
        logger.error(f"Failed to retrieve access token. Response: {token_response}")
        return {"error": "Failed to retrieve access token", "details": token_response}

    access_token = token_response["access_token"]
    patient_id = token_response.get("patient", "Unknown")

    # Fetch patient data
    headers = {"Authorization": f"Bearer {access_token}"}
    patient_response = requests.get(f"{FHIR_SERVER}/Patient/{patient_id}", headers=headers)

    # Log the raw response text for debugging
    logger.debug(f"Patient response: {patient_response.text}")

    # Check if the response is in XML format
    if patient_response.headers["Content-Type"].startswith("application/xml"):
        patient_data = pretty_print_xml(patient_response.text)
    else:
        # If not XML, attempt to parse as JSON
        try:
            patient_data = patient_response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to decode patient data: {e}")
            return {"error": "Failed to decode patient data", "details": patient_response.text}

    # Check for any issues with the patient data
    if patient_response.status_code != 200:
        logger.error(f"Failed to fetch patient data. Response: {patient_response.text}")
        return {"error": "Failed to fetch patient data", "details": patient_response.text}

    return templates.TemplateResponse(
        "patient.html",
        {"request": request, "patient": patient_data, "access_token": access_token},
    )


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("epic_smart_on_fhir:app", host="127.0.0.1", port=8080, reload=True)
