import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = "mistral-small"

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_CONTRACTS_DIR = os.path.join(DATA_DIR, "raw_contracts")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted")
