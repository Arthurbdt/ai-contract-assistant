import os
import json
from dotenv import load_dotenv
from mistralai.client import Mistral

# Load API key
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def extract_contract(input_file: str, output_file: str):
    """Extract data from a contract and save as JSON."""
    # Read contract
    with open(input_file, "r", encoding="utf-8") as f:
        contract_text = f.read()

    # Define prompt
    prompt = f"""
    Extract the following fields from this contract text:
    - Parties
    - Effective Date
    - Termination Date
    - Obligations
    - Penalties

    Return only valid JSON. If a field is missing, use null.

    Contract text: {contract_text}
    """

    # Call Mistral API
    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model="mistral-small",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # Save JSON output
    extracted_data = response.choices[0].message.content
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2)

    print(f"Extracted data saved to {output_file}")

# Example usage
if __name__ == "__main__":
    input_file = os.path.join(PROJECT_ROOT, "scripts", "sample_contracts", "license_agreement_fake_1.txt")
    output_file = os.path.join(PROJECT_ROOT, "data", "extracted_contracts", "license_agreement_fake_1.json")
    extract_contract(input_file, output_file)