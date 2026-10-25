import duckdb
import os
from typing import Optional, List, Dict, Any

from contract_assistant.config import DB_PATH


def get_connection():
    """Get a DuckDB connection to the database."""
    return duckdb.connect(database=DB_PATH, read_only=False)


def initialize_database():
    """Initialize the database with contracts and parties tables."""
    conn = get_connection()
    
    # Create contracts table with proper ID
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY,
            file_name TEXT NOT NULL,
            contract_type TEXT,
            governing_law TEXT,
            effective_date DATE,
            termination_date DATE,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add governing_law column if it doesn't exist (for backward compatibility)
    try:
        conn.execute("ALTER TABLE contracts ADD COLUMN governing_law TEXT")
    except Exception:
        pass
    
    # Create parties table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER,
            contract_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            role TEXT
        )
    """)
    
    conn.close()


def _infer_contract_type(file_name: str) -> str:
    """Infer contract type from filename."""
    file_name_lower = file_name.lower()
    if 'license' in file_name_lower:
        return 'license'
    elif 'nda' in file_name_lower:
        return 'nda'
    elif 'sales' in file_name_lower:
        return 'sales'
    return 'other'


def insert_contract(contract_data: Dict[str, Any], raw_text: str, file_name: str) -> int:
    """Insert a contract and its parties into the database."""
    conn = get_connection()
    
    try:
        # Start a transaction explicitly
        conn.execute("BEGIN TRANSACTION")
        
        # Ensure contract_data is a dictionary
        if not isinstance(contract_data, dict):
            contract_data = {}
        
        # Use extracted contract_type if available, otherwise fall back to filename inference
        contract_type = contract_data.get('contract_type')
        if not contract_type:
            contract_type = _infer_contract_type(file_name)
        
        # Get the next ID (max existing ID + 1)
        max_id_result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM contracts").fetchone()
        contract_id = max_id_result[0] + 1 if max_id_result and max_id_result[0] is not None else 1
        
        # Insert contract with explicit ID
        conn.execute("""
            INSERT INTO contracts (id, file_name, contract_type, governing_law, effective_date, termination_date, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_id,
            file_name,
            contract_type,
            contract_data.get('governing_law'),
            contract_data.get('effective_date'),
            contract_data.get('termination_date'),
            raw_text
        ))
        
        # Insert parties - ensure parties is a list
        parties = contract_data.get('parties', [])
        if not isinstance(parties, list):
            parties = []
        
        # Get the next party ID
        max_party_id_result = conn.execute("SELECT COALESCE(MAX(id), 0) FROM parties").fetchone()
        next_party_id = max_party_id_result[0] + 1 if max_party_id_result and max_party_id_result[0] is not None else 1
        
        for party in parties:
            # Handle case where party is a string (not a dict)
            if isinstance(party, str):
                conn.execute("""
                    INSERT INTO parties (id, contract_id, name, address, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (next_party_id, contract_id, party, None, None))
            elif isinstance(party, dict):
                # Party is a dict, extract fields safely
                conn.execute("""
                    INSERT INTO parties (id, contract_id, name, address, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    next_party_id,
                    contract_id,
                    party.get('name'),
                    party.get('address'),
                    party.get('role')
                ))
            
            # Increment party ID for next iteration
            next_party_id += 1
        
        conn.commit()
        return contract_id
        
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            # Ignore rollback errors if transaction wasn't started
            pass
        raise e
    finally:
        conn.close()


def get_contract(contract_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a contract with its parties."""
    conn = get_connection()
    
    try:
        contract = conn.execute("""
            SELECT id, file_name, contract_type, governing_law, effective_date, termination_date, raw_text, created_at
            FROM contracts WHERE id = ?
        """, (contract_id,)).fetchone()
        
        if not contract:
            return None
        
        parties = conn.execute("""
            SELECT id, contract_id, name, address, role FROM parties WHERE contract_id = ?
        """, (contract_id,)).fetchall()
        
        return {
            'contract': dict(zip(['contract_id', 'file_name', 'contract_type', 'governing_law', 'effective_date', 'termination_date', 'raw_text', 'created_at'], contract)),
            'parties': [dict(zip(['party_id', 'contract_id', 'name', 'address', 'role'], p)) for p in parties]
        }
    finally:
        conn.close()


def list_contracts() -> List[Dict[str, Any]]:
    """List all contracts."""
    conn = get_connection()
    
    try:
        contracts = conn.execute("""
            SELECT id, file_name, contract_type, governing_law, effective_date, termination_date, raw_text, created_at 
            FROM contracts 
            ORDER BY created_at DESC
        """).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'governing_law', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
    finally:
        conn.close()


def get_contracts_by_party(party_name: str) -> List[Dict[str, Any]]:
    """Find all contracts involving a specific party.
    
    Args:
        party_name: Name or partial name of the party to search for
        
    Returns:
        List of contract dictionaries matching the party
    """
    conn = get_connection()
    
    try:
        contracts = conn.execute("""
            SELECT DISTINCT c.id, c.file_name, c.contract_type, c.governing_law, c.effective_date, c.termination_date, c.raw_text, c.created_at
            FROM contracts c
            JOIN parties p ON c.id = p.contract_id
            WHERE p.name LIKE ?
            ORDER BY c.created_at DESC
        """, (f"%{party_name}%",)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'governing_law', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
    finally:
        conn.close()


def get_contracts_by_type(contract_type: str) -> List[Dict[str, Any]]:
    """Filter contracts by type (license, nda, sales, other).
    
    Args:
        contract_type: Type of contract to filter by
        
    Returns:
        List of contract dictionaries of the specified type
    """
    conn = get_connection()
    
    try:
        contracts = conn.execute("""
            SELECT id, file_name, contract_type, governing_law, effective_date, termination_date, raw_text, created_at
            FROM contracts
            WHERE LOWER(contract_type) = LOWER(?)
            ORDER BY created_at DESC
        """, (contract_type,)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'governing_law', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
    finally:
        conn.close()


def get_upcoming_expirations(days: int = 30) -> List[Dict[str, Any]]:
    """Find contracts that will expire in the next N days.
    
    Args:
        days: Number of days to look ahead for expirations
        
    Returns:
        List of contract dictionaries with upcoming termination dates
    """
    conn = get_connection()
    
    try:
        contracts = conn.execute("""
            SELECT id, file_name, contract_type, governing_law, effective_date, termination_date, raw_text, created_at
            FROM contracts
            WHERE termination_date IS NOT NULL
            AND termination_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, ?)
            ORDER BY termination_date
        """, (days,)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'governing_law', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
    finally:
        conn.close()
