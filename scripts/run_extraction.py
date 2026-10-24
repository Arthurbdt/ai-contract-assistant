import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from contract_assistant.config import RAW_CONTRACTS_DIR, EXTRACTED_DIR
from contract_assistant.extraction import extract_contract

if __name__ == "__main__":
    input_file = os.path.join(RAW_CONTRACTS_DIR, "license_agreement_fake_1.txt")
    output_file = os.path.join(EXTRACTED_DIR, "license_agreement_fake_1.json")
    extract_contract(input_file, output_file)
