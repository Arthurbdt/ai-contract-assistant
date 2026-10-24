
# test prompt
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

# revised prompt that enforces JSON format
def build_contract_prompt(contract_text: str) -> str:
    return f"""
Extract structured information from the contract below.
Return ONLY valid JSON (no explanations, no markdown).

Schema:
{{
  "parties": [
    {{
      "name": "string",
      "address": "string or null",
      "role": "string or null"
    }}
  ],
  "effective_date": "YYYY-MM-DD or null",
  "termination_date": "YYYY-MM-DD or null",
}}

Rules:
- Always return valid JSON
- Do not include any text before or after the JSON
- Do not add extra fields
- Use null when information is missing
- Extract obligations and penalties as close to verbatim as possible
- If multiple parties exist, return all of them

--- CONTRACT START ---
{contract_text}
--- CONTRACT END ---
"""