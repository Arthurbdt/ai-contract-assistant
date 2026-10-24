import json
from datetime import datetime

def normalize_parties(parties_data: list):
    """ Extract information from the parties fields """
    normalized_parties = []

    for party in parties_data:
        normalized_party = {
            "name": party.get("name"),
            "address": party.get("address"),
            "role": party.get("role")
        }
        normalized_parties.append(normalized_party)
    
    return normalized_parties

def parse_date(date_str: str):
    """ Convert date strings to YYY-MM-DD format """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str

def normalize_contract_data(raw_json):
    # Parse JSON if input is a string
    if isinstance(raw_json, str):
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")
    else:
        data = raw_json

    # intialize normalized output
    normalized = {
        "parties": normalize_parties(data.get("parties", [])),
        "effective_date": parse_date(data.get("effective_date")),
        "termination_date": parse_date(data.get("termination_date")),
        "raw_json": json.dumps(data)
    }

    print(normalized)
    return normalized

#sample = '{"parties": [{"name": "Helios Software Solutions Ltd.", "address": "Technoparkstrasse 1, 8005 Zurich, Switzerland", "role": "Licensor"}, {"name": "BrightWave Analytics Inc.", "address": "200 Market Street, San Francisco, CA 94105, USA", "role": "Licensee"}], "effective_date": "2026-05-01", "termination_date": null}'
sample2 = {"parties": [{"name": "Helios Software Solutions Ltd.", "address": "Technoparkstrasse 1, 8005 Zurich, Switzerland", "role": "Licensor"}, {"name": "BrightWave Analytics Inc.", "address": "200 Market Street, San Francisco, CA 94105, USA", "role": "Licensee"}], "effective_date": "2026-05-01", "termination_date": None}

# Example usage
if __name__ == "__main__":
    normalize_contract_data(sample2)
