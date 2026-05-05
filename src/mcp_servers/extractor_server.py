import os, re, glob, sys
parent_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(parent_dir)
grand_grandparent_dir = os.path.dirname(grandparent_dir)
sys.path.append(grand_grandparent_dir)
from mcp.server.fastmcp import FastMCP
from typing import List, Dict
import pandas as pd
from src.config import AZURE_DOC_INT_ENDPOINT, AZURE_DOC_INT_KEY, DATA_DIR, EXTRACTED_CLAIMS_EXCEL
from src.utils import Utils
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult

mcp = FastMCP("Extractor", host="0.0.0.0", port=8502)

extract_doc = Utils()
endpoint = AZURE_DOC_INT_ENDPOINT
key = AZURE_DOC_INT_KEY
document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def get_pdf_text(path: str) -> str:
    with open(path, "rb") as file:
        document_bytes = file.read()

    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-read",
        body=document_bytes,
        output=[AnalyzeOutputOption.PDF],
    )
    paras = extract_doc.extract_para(poller.result())
    return "\n".join(list(paras.values()))

def extract_aadhar(text):
    name = re.search(r'Name[:\-]?\s*([A-Za-z ]+)', text)
    dob = re.search(r'Date of Birth[:\-]?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
    aadhar = re.search(r'([0-9]{4} [0-9]{4} [0-9]{4})', text)
    return {
        "name": name.group(1).strip() if name else None,
        "dob": dob.group(1).strip() if dob else None,
        "aadhar": aadhar.group(1).strip().replace(" ","") if aadhar else None
    }

def extract_licence(text):
    licence = re.search(r'(DL-[0-9]{12,15})', text)
    name = re.search(r'Name[:\-]?\s*([A-Za-z ]+)', text)
    dob = re.search(r'DOB[:\-]?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
    valid_till = re.search(r'Valid till[:\-]?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
    return {
        "licence": licence.group(1).strip() if licence else None,
        "name": name.group(1).strip() if name else None,
        "dob": dob.group(1).strip() if dob else None,
        "valid_till": valid_till.group(1).strip() if valid_till else None
    }

def extract_rc(text):
    rc_no = re.search(r'Registration Number[:\-]?\s*([A-Z0-9 ]+)', text)
    vehicle_make = re.search(r'Make[:\-]?\s*([A-Za-z0-9 ]+)', text)
    vehicle_model = re.search(r'Model[:\-]?\s*([A-Za-z0-9 ]+)', text)
    vehicle_color = re.search(r'Color[:\-]?\s*([A-Za-z0-9 ]+)', text)
    return {
        "rc_no": rc_no.group(1).strip() if rc_no else None,
        "vehicle_make": vehicle_make.group(1).strip() if vehicle_make else None,
        "vehicle_model": vehicle_model.group(1).strip() if vehicle_model else None,
        "vehicle_color": vehicle_color.group(1).strip() if vehicle_color else None,
    }

@mcp.tool()
def extract(claim_id: int) -> List[Dict]:
    claim_folder = os.path.join(DATA_DIR, str(claim_id))
    files = glob.glob(os.path.join(claim_folder, "*"))
    print(f"Processing files in {claim_folder}: {files}")
    final_data = {"claim_id": claim_id}
    if len(files) != 0:
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension == ".pdf":
                text = get_pdf_text(file_path)
                if text == "":
                    final_data['error'] = 'No text extracted from the document'
                else:
                    fields = {}
                    if "aadhaar" in file_name.lower():
                        fields = extract_aadhar(text)
                    elif "licence" in file_name.lower():
                        fields = extract_licence(text)
                    elif "registration" in file_name.lower() or "rc" in file_name.lower():
                        fields = extract_rc(text)
                    for k, v in fields.items():
                        if v is not None:
                            final_data[k] = v

        df = pd.DataFrame([final_data])
        df.to_excel(EXTRACTED_CLAIMS_EXCEL, index=False)
        print(f"Extracted data saved to {EXTRACTED_CLAIMS_EXCEL}")

        return [final_data]  # Always return a list of dictionaries
    else:
        return [{"claim_id": claim_id, "error": "No files found in the specified folder."}]

if __name__ == "__main__":
    # Run the MCP server using the stdio transport
    print("Starting Extractor Service MCP server on port 8001...")
    print("Connect to this server using http://localhost:8001/stdio")
    mcp.run(transport="stdio")