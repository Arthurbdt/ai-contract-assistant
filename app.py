import streamlit as st
import os
import sys
import tempfile
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from contract_assistant.database import (
    initialize_database, 
    insert_contract, 
    list_contracts, 
    get_contract
)
from contract_assistant.extraction import extract_and_store_contract

# Initialize database on app start
initialize_database()


def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to a temporary location and return the path."""
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def display_contracts_table(contracts: List[Dict[str, Any]]) -> None:
    """Display contracts in a formatted Streamlit table."""
    if not contracts:
        st.info("No contracts in database yet.")
        return
    
    # Prepare data for display
    table_data = []
    for c in contracts:
        table_data.append({
            'ID': c['contract_id'],
            'File Name': c['file_name'],
            'Type': c['contract_type'],
            'Effective Date': c['effective_date'],
            'Termination Date': c['termination_date']
        })
    
    st.dataframe(
        table_data,
        hide_index=True,
        use_container_width=True
    )


def display_parties_table() -> None:
    """Display all parties from all contracts in a formatted table."""
    contracts = list_contracts()
    if not contracts:
        st.info("No parties in database yet.")
        return
    
    # Collect all parties
    all_parties = []
    for c in contracts:
        contract = get_contract(c['contract_id'])
        if contract and contract['parties']:
            for party in contract['parties']:
                all_parties.append({
                    'Contract ID': party['contract_id'],
                    'Contract File': c['file_name'],
                    'Name': party['name'],
                    'Role': party['role'],
                    'Address': party['address']
                })
    
    if not all_parties:
        st.info("No parties found in contracts.")
        return
    
    st.dataframe(
        all_parties,
        hide_index=True,
        use_container_width=True
    )


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Contract Assistant",
        layout="wide"
    )
    
    st.title("AI Contract Assistant")
    st.markdown("---")
    
    # File Upload Section
    st.header("Upload Contract")
    
    uploaded_file = st.file_uploader(
        "Upload a contract file (txt only)",
        type=['txt'],
        key='contract_uploader'
    )
    
    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
        
        if st.button("Extract Contract", key='extract_button'):
            with st.spinner("Extracting contract data..."):
                try:
                    # Save uploaded file temporarily
                    temp_file_path = save_uploaded_file(uploaded_file)
                    
                    # Extract and store
                    contract_id = extract_and_store_contract(temp_file_path)
                    
                    # Clean up temp file
                    os.remove(temp_file_path)
                    
                    st.success(f"Contract extracted and stored! ID: {contract_id}")
                    
                    # Refresh the page to show new data
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error extracting contract: {e}")
    
    st.markdown("---")
    
    # Contracts Table Section
    st.header("Stored Contracts")
    contracts = list_contracts()
    display_contracts_table(contracts)
    
    st.markdown("---")
    
    # Parties Table Section
    st.header("Parties")
    display_parties_table()


if __name__ == "__main__":
    main()
