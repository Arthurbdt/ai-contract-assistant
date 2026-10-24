import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from contract_assistant.config import EXTRACTED_DIR, RAW_CONTRACTS_DIR
from contract_assistant.database import initialize_database, insert_contract

if __name__ == "__main__":
    # Initialize database
    initialize_database()
    print("Database initialized")
    
    # Process all extracted JSON files
    for filename in os.listdir(EXTRACTED_DIR):
        if filename.endswith('.json'):
            json_file = os.path.join(EXTRACTED_DIR, filename)
            
            # Find corresponding raw text file
            base_name = os.path.splitext(filename)[0]
            txt_file = os.path.join(RAW_CONTRACTS_DIR, base_name + ".txt")
            
            if os.path.exists(txt_file):
                # Read extracted data
                with open(json_file, 'r', encoding='utf-8') as f:
                    contract_data = json.load(f)
                
                # Read raw text
                with open(txt_file, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                
                # Store in database
                contract_id = insert_contract(
                    contract_data=contract_data,
                    raw_text=raw_text,
                    file_name=filename
                )
                print(f"Imported {filename} with ID: {contract_id}")
            else:
                print(f"Warning: No raw text file found for {filename}")
    
    print("\nAll extracted contracts imported to database!")
