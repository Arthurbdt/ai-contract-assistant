#!/usr/bin/env python3
"""
Test suite for contract_assistant.normalization module
Tests the contract data normalization functionality
"""

import os
import sys
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from contract_assistant.normalization import normalize_contract_data, parse_date


class TestNormalizeOutput(unittest.TestCase):
    """Test cases for contract data normalization functions"""
    
    def test_parse_date_valid_iso_format(self):
        """Test parsing a date in ISO format (YYYY-MM-DD)"""
        result = parse_date("2026-05-01")
        self.assertEqual(result, "2026-05-01")

    def test_parse_date_valid_month_day_year_format(self):
        """Test parsing a date in Month Day, Year format"""
        result = parse_date("May 01, 2026")
        self.assertEqual(result, "2026-05-01")

    def test_parse_date_invalid_format(self):
        """Test that invalid date formats are returned as-is"""
        result = parse_date("invalid-date")
        self.assertEqual(result, "invalid-date")

    def test_parse_date_empty_string(self):
        """Test that empty strings return None"""
        result = parse_date("")
        self.assertIsNone(result)

    def test_parse_date_none_input(self):
        """Test that None input returns None"""
        result = parse_date(None)
        self.assertIsNone(result)

    def test_normalize_contract_data_with_dict_input(self):
        """Test normalization with dictionary input"""
        input_data = {
            "parties": [
                {"name": "Helios Software Solutions Ltd.", "address": "Technoparkstrasse 1, 8005 Zurich, Switzerland", "role": "Licensor"},
                {"name": "BrightWave Analytics Inc.", "address": "200 Market Street, San Francisco, CA 94105, USA", "role": "Licensee"}
            ],
            "effective_date": "2026-05-01",
            "termination_date": None
        }

        result = normalize_contract_data(input_data)

        # Check that the result has the expected structure
        self.assertIn("parties", result)
        self.assertIn("effective_date", result)
        self.assertIn("termination_date", result)
        self.assertIn("raw_json", result)

        # Check specific values
        self.assertEqual(result["effective_date"], "2026-05-01")
        self.assertIsNone(result["termination_date"])

        # Check that raw_json contains the original data
        parsed_raw = json.loads(result["raw_json"])
        self.assertEqual(parsed_raw["effective_date"], "2026-05-01")

    def test_normalize_contract_data_with_string_input(self):
        """Test normalization with JSON string input"""
        input_json = json.dumps({
            "parties": [
                {"name": "Helios Software Solutions Ltd.", "address": "Technoparkstrasse 1, 8005 Zurich, Switzerland", "role": "Licensor"},
                {"name": "BrightWave Analytics Inc.", "address": "200 Market Street, San Francisco, CA 94105, USA", "role": "Licensee"}
            ],
            "effective_date": "May 01, 2026",
            "termination_date": None
        })

        result = normalize_contract_data(input_json)

        # Check that the date was properly parsed
        self.assertEqual(result["effective_date"], "2026-05-01")

    def test_normalize_contract_data_invalid_json(self):
        """Test that invalid JSON strings raise ValueError"""
        with self.assertRaises(ValueError):
            normalize_contract_data("invalid json string")

    def test_normalize_contract_data_missing_fields(self):
        """Test normalization with missing optional fields"""
        input_data = {
            "parties": []
            # Missing effective_date and termination_date
        }

        result = normalize_contract_data(input_data)

        # Should handle missing fields gracefully
        self.assertIsNone(result["effective_date"])
        self.assertIsNone(result["termination_date"])


if __name__ == "__main__":
    unittest.main()