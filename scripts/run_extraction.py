import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from contract_assistant.config import RAW_CONTRACTS_DIR, EXTRACTED_DIR
from contract_assistant.database import initialize_database
from contract_assistant.extraction import extract_contract, extract_and_store_contract

# Rate limit delay in seconds (Mistral free tier: ~30 requests per minute)
RATE_LIMIT_DELAY = 2.5

if __name__ == "__main__":
    # Initialize database
    initialize_database()
    print("Database initialized")
    
    # Process all contracts in raw_contracts directory
    for filename in os.listdir(RAW_CONTRACTS_DIR):
        if filename.endswith('.txt'):
            input_file = os.path.join(RAW_CONTRACTS_DIR, filename)
            output_file = os.path.join(EXTRACTED_DIR, os.path.splitext(filename)[0] + ".json")
            
            print(f"\nProcessing {filename}...")
            
            try:
                # Extract and save to JSON
                extract_contract(input_file, output_file)
                
                # Also store in database
                contract_id = extract_and_store_contract(input_file)
                print(f"Stored in database with ID: {contract_id}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
            
            # Rate limiting: wait before next request
            if filename != os.listdir(RAW_CONTRACTS_DIR)[-1]:  # Don't wait after last file
                print(f"Waiting {RATE_LIMIT_DELAY} seconds for rate limit...")
                time.sleep(RATE_LIMIT_DELAY)
