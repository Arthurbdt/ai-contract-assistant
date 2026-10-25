import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union


def normalize_parties(parties_data: Union[List[Dict[str, Any]], List[str], None]) -> List[Dict[str, Optional[str]]]:
    """
    Normalize parties data to ensure consistent structure.
    
    Args:
        parties_data: List of party dictionaries, list of strings, or None
        
    Returns:
        List of normalized party dictionaries with name, address, and role keys
        
    Handles:
        - Dict items with name/address/role
        - String items (converted to dict with name only)
        - Missing fields (set to None)
        - None or empty input (returns empty list)
    """
    if not parties_data:
        return []
    
    normalized_parties = []
    
    for party in parties_data:
        # Handle string items (e.g., LLM returns ["Acme Corp", "Globex Inc"])
        if isinstance(party, str):
            normalized_parties.append({
                "name": party,
                "address": None,
                "role": None
            })
            continue
        
        # Handle dict items
        if isinstance(party, dict):
            normalized_party = {
                "name": party.get("name"),
                "address": party.get("address"),
                "role": party.get("role")
            }
            normalized_parties.append(normalized_party)
        
        # Skip other types (int, float, etc.)
    
    return normalized_parties


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convert date strings to YYYY-MM-DD format.
    
    Args:
        date_str: Date string in various formats or None
        
    Returns:
        Date string in YYYY-MM-DD format, or None if invalid/unparseable
        
    Supported formats:
        - YYYY-MM-DD (ISO format)
        - Month DD, YYYY (e.g., "January 1, 2023")
        - MM/DD/YYYY
        - DD-MM-YYYY
        - YYYY/MM/DD
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Strip whitespace
    date_str = date_str.strip()
    
    if not date_str:
        return None
    
    # Try various date formats
    date_formats = [
        "%Y-%m-%d",      # ISO format: 2023-01-01
        "%B %d, %Y",     # Full month: January 1, 2023
        "%b %d, %Y",     # Abbreviated month: Jan 1, 2023
        "%m/%d/%Y",      # US format: 01/01/2023
        "%d-%m-%Y",      # European format: 01-01-2023
        "%Y/%m/%d",      # Alternative ISO: 2023/01/01
        "%d %B %Y",      # Day Month Year: 01 January 2023
        "%d %b %Y",      # Day AbbrMonth Year: 01 Jan 2023
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If no format matched, return None (don't return the original string)
    return None


def validate_contract_type(contract_type: Optional[str]) -> Optional[str]:
    """
    Validate and standardize contract type values.
    
    Args:
        contract_type: Contract type string or None
        
    Returns:
        Standardized contract type string or None
        
    Standardization rules:
        - Converts to lowercase for comparison
        - Maps common variations to standard types
        - Returns None for empty/invalid values
        
    Supported types:
        - NDA (Non-Disclosure Agreement, Confidentiality Agreement)
        - MSA (Master Service Agreement, Service Agreement)
        - License (Software License, License Agreement)
        - Lease (Lease Agreement, Rental Agreement)
        - Employment (Employment Contract, Work Agreement)
        - Sales (Sales Agreement, Purchase Agreement)
        - Partnership (Partnership Agreement, Joint Venture)
        - Other (for unrecognized types)
    """
    if not contract_type or not isinstance(contract_type, str):
        return None
    
    # Strip whitespace and convert to lowercase for comparison
    contract_type_lower = contract_type.strip().lower()
    
    if not contract_type_lower:
        return None
    
    # Map variations to standard types
    type_mapping = {
        # NDA variations
        'nda': 'NDA',
        'non-disclosure agreement': 'NDA',
        'confidentiality agreement': 'NDA',
        'non disclosure agreement': 'NDA',
        'confidentiality': 'NDA',
        
        # Service Agreement variations
        'msa': 'MSA',
        'master service agreement': 'MSA',
        'service agreement': 'MSA',
        'services agreement': 'MSA',
        'master services agreement': 'MSA',
        
        # License variations
        'license': 'License',
        'software license': 'License',
        'license agreement': 'License',
        'licence': 'License',  # British spelling
        'software license agreement': 'License',
        
        # Lease variations
        'lease': 'Lease',
        'lease agreement': 'Lease',
        'rental agreement': 'Lease',
        'rental': 'Lease',
        
        # Employment variations
        'employment': 'Employment',
        'employment contract': 'Employment',
        'employment agreement': 'Employment',
        'work agreement': 'Employment',
        
        # Sales variations
        'sales': 'Sales',
        'sales agreement': 'Sales',
        'purchase agreement': 'Sales',
        'sale': 'Sales',
        
        # Partnership variations
        'partnership': 'Partnership',
        'partnership agreement': 'Partnership',
        'joint venture': 'Partnership',
        'joint venture agreement': 'Partnership',
    }
    
    # Return standardized type or 'Other' if not recognized
    return type_mapping.get(contract_type_lower, 'Other')


def normalize_contract_data(raw_json):
    """
    Normalize contract data to ensure consistent structure.
    
    Args:
        raw_json: JSON string or dictionary with contract data
        
    Returns:
        Dictionary with normalized contract data
    """
    # Parse JSON if input is a string
    if isinstance(raw_json, str):
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")
    else:
        data = raw_json

    # Initialize normalized output
    normalized = {
        "parties": normalize_parties(data.get("parties", [])),
        "effective_date": parse_date(data.get("effective_date")),
        "termination_date": parse_date(data.get("termination_date")),
        "contract_type": validate_contract_type(data.get("contract_type")),
        "governing_law": data.get("governing_law"),
        "raw_json": json.dumps(data) if isinstance(raw_json, dict) else raw_json
    }

    return normalized


# Example usage and test cases
if __name__ == "__main__":
    # Test normalize_parties
    print("Testing normalize_parties:")
    print(normalize_parties([
        {"name": "Acme Corp", "address": "123 Main St", "role": "Vendor"},
        {"name": "Globex Inc"}
    ]))
    print(normalize_parties(["Acme Corp", "Globex Inc"]))
    print(normalize_parties([]))
    print()
    
    # Test parse_date
    print("Testing parse_date:")
    print(parse_date("2023-01-01"))
    print(parse_date("January 1, 2023"))
    print(parse_date("01/01/2023"))
    print(parse_date("invalid"))
    print()
    
    # Test normalize_contract_data
    print("Testing normalize_contract_data:")
    print(normalize_contract_data({
        "parties": [{"name": "Acme Corp"}],
        "effective_date": "January 1, 2023",
        "contract_type": "Service Agreement"
    }))
