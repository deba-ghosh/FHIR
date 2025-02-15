import requests

# Define the base URL of an open FHIR server
FHIR_BASE_URL = "https://hapi.fhir.org/baseR4"


def get_patient(patient_id):
    """Fetch patient data from the FHIR server."""
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url, headers={"Accept": "application/fhir+json"})

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch patient. Status Code: {response.status_code}"}


if __name__ == "__main__":
    patient_id = "example"  # Replace with a real patient ID
    patient_data = get_patient(patient_id)
    print(patient_data)
