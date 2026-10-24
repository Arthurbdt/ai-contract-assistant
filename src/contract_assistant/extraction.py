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

    # Define prompt
    prompt = build_contract_prompt(contract_text)

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

    # Define prompt
    prompt = build_contract_prompt(contract_text)

    # Call Mistral API
    client = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # Parse extracted data
    extracted_data = json.loads(response.choices[0].message.content)
    
    # Store in database
    contract_id = insert_contract(
        contract_data=extracted_data,
        raw_text=contract_text,
        file_name=os.path.basename(input_file)
    )
    
    print(f"Contract stored in database with ID: {contract_id}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
    return contract_id
