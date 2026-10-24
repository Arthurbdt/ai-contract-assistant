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
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER,
            file_name TEXT NOT NULL,
            contract_type TEXT,
            effective_date DATE,
            termination_date DATE,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            party_id INTEGER,
            contract_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            role TEXT
        )
    """)
    
    conn.close()


def insert_contract(contract_data: Dict[str, Any], raw_text: str, file_name: str) -> int:
    """Insert a contract and its parties into the database."""
    conn = get_connection()
    
    try:
        # Insert contract
        conn.execute("""
            INSERT INTO contracts (file_name, contract_type, effective_date, termination_date, raw_text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            file_name,
            _infer_contract_type(file_name),
            contract_data.get('effective_date'),
            contract_data.get('termination_date'),
            raw_text
        ))
        
        # Get the rowid of the inserted contract
        contract_id = conn.execute("SELECT MAX(rowid) FROM contracts").fetchone()[0]
        
        # Insert parties
        for party in contract_data.get('parties', []):
            conn.execute("""
                INSERT INTO parties (contract_id, name, address, role)
                VALUES (?, ?, ?, ?)
            """, (
                contract_id,
                party.get('name'),
                party.get('address'),
                party.get('role')
            ))
        
        conn.commit()
        return contract_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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


def get_contract(contract_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a contract with its parties."""
    conn = get_connection()
    
    try:
        contract = conn.execute("""
            SELECT * FROM contracts WHERE rowid = ?
        """, (contract_id,)).fetchone()
        
        if not contract:
            return None
        
        parties = conn.execute("""
            SELECT * FROM parties WHERE contract_id = ?
        """, (contract_id,)).fetchall()
        
        return {
            'contract': dict(zip(['contract_id', 'file_name', 'contract_type', 'effective_date', 'termination_date', 'raw_text', 'created_at'], contract)),
            'parties': [dict(zip(['party_id', 'contract_id', 'name', 'address', 'role'], p)) for p in parties]
        }
    finally:
        conn.close()


def list_contracts() -> List[Dict[str, Any]]:
    """List all contracts."""
    conn = get_connection()
    
    try:
        contracts = conn.execute("""
            SELECT rowid, file_name, contract_type, effective_date, termination_date, raw_text, created_at 
            FROM contracts 
            ORDER BY created_at DESC
        """).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
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
            SELECT DISTINCT c.rowid, c.file_name, c.contract_type, c.effective_date, c.termination_date, c.raw_text, c.created_at
            FROM contracts c
            JOIN parties p ON c.rowid = p.contract_id
            WHERE p.name LIKE ?
            ORDER BY c.created_at DESC
        """, (f"%{party_name}%",)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
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
            SELECT rowid, file_name, contract_type, effective_date, termination_date, raw_text, created_at
            FROM contracts
            WHERE contract_type = ?
            ORDER BY created_at DESC
        """, (contract_type.lower(),)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
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
            SELECT rowid, file_name, contract_type, effective_date, termination_date, raw_text, created_at
            FROM contracts
            WHERE termination_date IS NOT NULL
            AND termination_date BETWEEN CURRENT_DATE AND DATE_ADD(CURRENT_DATE, ?)
            ORDER BY termination_date
        """, (days,)).fetchall()
        return [dict(zip(['contract_id', 'file_name', 'contract_type', 'effective_date', 'termination_date', 'raw_text', 'created_at'], c)) for c in contracts]
    finally:
        conn.close()
