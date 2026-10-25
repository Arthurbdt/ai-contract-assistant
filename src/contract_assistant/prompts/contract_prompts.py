
# Field-specific extraction templates (without contract text)
CONTRACT_TYPE_TEMPLATE = """
Extract the contract type from the document.
Look for:
- Titles or headings (e.g., "Non-Disclosure Agreement", "Service Agreement")
- Phrases like "This [Type] Agreement" or "[Type] Contract"
- Common types: NDA, MSA, Service Agreement, Lease, Employment, License, Sales, Partnership
Return ONLY the contract type as a string or null.
"""

GOVERNING_LAW_TEMPLATE = """
Extract the governing law or jurisdiction from the document.
Look for:
- Phrases like "governed by the laws of", "subject to the laws of", "jurisdiction: "
- State/country names (e.g., "State of California", "England and Wales")
- Court references (e.g., "courts of New York")
Return ONLY the governing law as a string or null.
"""

PARTIES_TEMPLATE = """
Extract all parties mentioned in the contract.
For each party, include:
- name: Full legal name (required)
- address: Full address or null
- role: Role in the contract (e.g., "Vendor", "Client") or null
Return as a list of party objects.
"""

DATES_TEMPLATE = """
Extract the following dates:
- effective_date: When the contract becomes effective (YYYY-MM-DD or null)
- termination_date: When the contract terminates or expires (YYYY-MM-DD or null)
Return dates in ISO format (YYYY-MM-DD) or null if missing.
"""

# Legacy prompt for backward compatibility
CONTRACT_EXTRACTION_PROMPT_INITIAL = """
Extract the following fields from this contract text:
- Parties
- Effective Date
- Termination Date
- Obligations
- Penalties

Return only valid JSON. If a field is missing, use null.

Contract text: {contract_text}
"""

# Field to template mapping
FIELD_TEMPLATES = {
    "contract_type": CONTRACT_TYPE_TEMPLATE,
    "governing_law": GOVERNING_LAW_TEMPLATE,
    "parties": PARTIES_TEMPLATE,
    "dates": DATES_TEMPLATE,
}

# Field to schema mapping
FIELD_SCHEMA = {
    "contract_type": '"contract_type": "string or null"',
    "governing_law": '"governing_law": "string or null"',
    "parties": '"parties": [{"name": "string", "address": "string or null", "role": "string or null"}]',
    "effective_date": '"effective_date": "YYYY-MM-DD or null"',
    "termination_date": '"termination_date": "YYYY-MM-DD or null"',
}


def build_contract_prompt(
    contract_text: str,
    fields: list = None
) -> str:
    """
    Build a prompt to extract specified fields from a contract.
    
    Args:
        contract_text: The full text of the contract
        fields: List of fields to extract. If None, uses default fields.
               Options: "contract_type", "governing_law", "parties", 
                       "effective_date", "termination_date"
    
    Returns:
        A formatted prompt string ready for LLM input
    """
    # Default fields for backward compatibility
    if fields is None:
        fields = ["parties", "effective_date", "termination_date"]
    
    # Collect templates and schema parts for requested fields
    templates = []
    schema_parts = []
    
    for field in fields:
        if field in FIELD_TEMPLATES:
            templates.append(FIELD_TEMPLATES[field].strip())
        
        if field in FIELD_SCHEMA:
            schema_parts.append(FIELD_SCHEMA[field])
    
    # Build the schema section
    schema = "{\n  " + ",\n  ".join(schema_parts) + "\n}"
    
    # Build the instructions section
    instructions = "\n\n".join(templates)
    
    return f"""Extract structured information from the contract below.
Return ONLY valid JSON (no explanations, no markdown).

Schema:
{schema}

Instructions:
{instructions}

Rules:
- Always return valid JSON
- Do not include any text before or after the JSON
- Do not add extra fields beyond those in the schema
- Use null when information is missing
- If multiple parties exist, return all of them

--- CONTRACT START ---
{contract_text}
--- CONTRACT END ---
"""