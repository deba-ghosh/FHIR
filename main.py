from fastapi import FastAPI
import requests

app = FastAPI()

FHIR_BASE_URL = "https://hapi.fhir.org/baseR4"


@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    """Fetch patient details from FHIR server."""
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url, headers={"Accept": "application/fhir+json"})

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch patient. Status Code: {response.status_code}"}

# Run the API using: uvicorn main:app --reload