from mcp.server.fastmcp import FastMCP
import pandas as pd
import re
from src.config import INSURANCE_CLAIMS_EXCEL, POLICY_DATA_EXCEL

mcp = FastMCP("FraudDetection",host="0.0.0.0", port=8505)

def clean_phone(num):
    return re.sub(r'\D', '', str(num)).strip()

def safe_compare(a, b):
    return str(a).strip().casefold() == str(b).strip().casefold()

def get_policy_dataframe():
    df = pd.read_excel(POLICY_DATA_EXCEL)
    df.columns = [str(c).strip().lower().replace("_", " ") for c in df.columns]
    return df

def find_policy_record(df, policy_number):
    policy_number = str(policy_number)
    record = df[df['policy number'].astype(str) == policy_number]
    if not record.empty:
        return record.iloc[0].to_dict()
    return None

def fraud_rule(claim, policy_record):
    flags = []
    print(claim.get("model", "") , policy_record.get("model", ""))
    if claim.get("policy_verification", "").strip().casefold() != "verified":
        flags.append("Policy not verified")
        return flags, "High"
    if claim.get("validation_status", "").strip().casefold() != "pass":
        flags.append("Validation failed")
        return flags, "High"
    if not policy_record:
        flags.append("Policy number does not exist in master database")
        return flags, "High"
    if not safe_compare(claim.get("name", ""), policy_record.get("full name", "")):
        flags.append("Name does not match policy record")
    # if not safe_compare(claim.get("email", ""), policy_record.get("email address", "")):
    #     flags.append("Email address does not match policy record")
    # if clean_phone(claim.get("contact_number", "")) != clean_phone(policy_record.get("phone number", "")):
    #     flags.append("Contact number does not match policy record")
    # if not safe_compare(claim.get("address", ""), policy_record.get("address", "")):
    #     flags.append("Address does not match policy record")
    if not safe_compare(claim.get("make", ""), policy_record.get("make", "")):
        flags.append("Vehicle make does not match policy record")
    if not safe_compare(claim.get("model", ""), policy_record.get("model", "")):
        flags.append("Vehicle model does not match policy record")
    if not safe_compare(claim.get("registration_number", "").replace(" ", ""), str(policy_record.get("registration number", "")).replace(" ", "")):
        flags.append("Registration number does not match policy record")
    cost = claim.get("cost")
    try:
        idv = float(policy_record.get("idv (in inr)", 0))
    except:
        idv = 0
    try:
        age_of_vehicle = int(policy_record.get("age of vehicle", 0))
    except:
        age_of_vehicle = 0
    if cost is not None and idv > 0:
        if cost > idv:
            flags.append("Claim cost exceeds insured declared value (IDV)")
        if age_of_vehicle > 3 and cost > 0.9 * idv:
            flags.append("High claim cost for older vehicle")
    if not claim.get("aadhaar_file_path"):
        flags.append("Aadhaar document not uploaded")
    if not claim.get("license_file_path"):
        flags.append("License document not uploaded")
    if not claim.get("registration_file_path"):
        flags.append("Registration certificate not uploaded")
    high_flags = [
        "Policy not verified", "Validation failed", "Policy number does not exist in master database",
        "Claim cost exceeds insured declared value (IDV)"
    ]
    if any(flag in flags for flag in high_flags):
        risk_score = "High"
    elif len(flags) >= 3:
        risk_score = "Medium"
    elif len(flags) in [1, 2]:
        risk_score = "Low"
    else:
        risk_score = "Low"
    return flags, risk_score

@mcp.tool()
def detect_fraud(claim_id: int) -> dict:
    USER_TABLE = pd.read_excel(INSURANCE_CLAIMS_EXCEL)
    row = USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id]
    if row.empty:
        return {"claim_id": claim_id, "Fraud Detected": "Error", "Risk Score": "N/A", "Fraud Flag": "Claim not found"}
    claim = row.iloc[0].to_dict()
    df = get_policy_dataframe()
    policy_record = find_policy_record(df, claim.get("policy_number"))
    flags, risk_score = fraud_rule(claim, policy_record)
    fraud_detected = "Yes" if flags else "No"
    fraud_flag = ", ".join(flags) if flags else "None"

    USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "risk_score"] = risk_score
    USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "fraud_detected"] = fraud_detected

    
    if fraud_detected == "Yes":
        USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "UnderwriterReview"] = "Reject"
    else:
        USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "UnderwriterReview"] = "Approved"

    USER_TABLE.to_excel(INSURANCE_CLAIMS_EXCEL, index=False)

    return {
        "claim_id": claim_id,
        "Fraud Detected": fraud_detected,
        "Risk Score": risk_score,
        "Fraud Flag": fraud_flag
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
    #print(detect_fraud_for_claim(1))