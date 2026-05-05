import os
from dotenv import load_dotenv

load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data")
INSURANCE_CLAIMS_EXCEL = os.path.join(DATA_DIR, "insurance_claims.xlsx")
EXTRACTED_CLAIMS_EXCEL = os.path.join(DATA_DIR, "extracted_claims.xlsx")
POLICY_DATA_EXCEL = os.path.join(DATA_DIR, "final_sample_insurance_data.xlsx")
PAYMENT_RECORDS_EXCEL = os.path.join(DATA_DIR, "PaymentRecords.xlsx")
UNDERWRITER_LIST_EXCEL = os.path.join(DATA_DIR, "underwriter_list.xlsx")

# Azure Document Intelligence
AZURE_DOC_INT_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DOC_INT_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

# OpenAI / Azure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# MCP Server Config
SERVERS_CONFIG_PATH = os.path.join(BASE_DIR, "servers_config.json")

def ensure_dirs():
    """Ensure necessary directories exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
