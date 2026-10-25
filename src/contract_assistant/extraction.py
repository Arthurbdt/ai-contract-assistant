from mistralai.client import Mistral
from contract_assistant.config import MISTRAL_API_KEY, MISTRAL_MODEL
from contract_assistant.prompts.contract_prompts import build_contract_prompt
from contract_assistant.database import insert_contract, initialize_database
import json
import os


def extract_contract(input_file: str, output_file: str):
    """Extract data from a contract and save as JSON."""
    # Read contract
    with open(input_file, "r", encoding="utf-8") as f:
        contract_text = f.read()
        print(contract_text[:100])

    # Define prompt - use all fields including contract_type and governing_law
    prompt = build_contract_prompt(
        contract_text,
        fields=['contract_type', 'governing_law', 'parties', 'effective_date', 'termination_date']
    )

    # Call Mistral API
    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # Save JSON output
    extracted_data = response.choices[0].message.content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(extracted_data)

    print(f"Extracted data saved to {output_file}")

    # Estimate tokens used
    print(f"Tokens used: {response.usage.total_tokens}")
    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Completion tokens: {response.usage.completion_tokens}")


def extract_and_store_contract(input_file: str) -> int:
    """Extract contract data and store in DuckDB database.
    
    Args:
        input_file: Path to the contract text file
        
    Returns:
        The contract_id of the stored contract
    """
    # Read contract
    with open(input_file, "r", encoding="utf-8") as f:
        contract_text = f.read()

    # Define prompt - use all fields including contract_type and governing_law
    prompt = build_contract_prompt(
        contract_text,
        fields=['contract_type', 'governing_law', 'parties', 'effective_date', 'termination_date']
    )

    # Call Mistral API
    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # Parse extracted data
    extracted_data = json.loads(response.choices[0].message.content)
    
    # Log what we received
    print(f"Raw extracted data type: {type(extracted_data)}")
    print(f"Raw extracted data: {extracted_data}")
    
    # Normalize the extracted data structure
    normalized_data = {}
    
    # Handle case where extracted_data is a list (e.g., just parties)
    if isinstance(extracted_data, list):
        normalized_data['parties'] = extracted_data
    elif isinstance(extracted_data, dict):
        normalized_data = extracted_data
    else:
        # For other types, create empty structure
        normalized_data = {}
    
    # Ensure parties is a list of dicts
    if 'parties' in normalized_data:
        if not isinstance(normalized_data['parties'], list):
            normalized_data['parties'] = []
        else:
            # Convert any non-dict items in parties list to dict format
            new_parties = []
            for party in normalized_data['parties']:
                if isinstance(party, dict):
                    new_parties.append(party)
                elif isinstance(party, str):
                    new_parties.append({'name': party, 'address': None, 'role': None})
                # Skip other types
            normalized_data['parties'] = new_parties
    else:
        normalized_data['parties'] = []
    
    # Ensure all expected fields exist
    for field in ['contract_type', 'governing_law', 'effective_date', 'termination_date']:
        if field not in normalized_data:
            normalized_data[field] = None
    
    extracted_data = normalized_data
    
    # Store in database
    contract_id = insert_contract(
        contract_data=extracted_data,
        raw_text=contract_text,
        file_name=os.path.basename(input_file)
    )
    
    print(f"Contract stored in database with ID: {contract_id}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
    return contract_id
