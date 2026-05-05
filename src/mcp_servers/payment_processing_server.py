from mcp.server.fastmcp import FastMCP
import pandas as pd
import uuid
from datetime import datetime
from src.config import INSURANCE_CLAIMS_EXCEL, PAYMENT_RECORDS_EXCEL

mcp = FastMCP("PaymentProcessing", host="0.0.0.0", port=8506)

@mcp.tool()
def process_payment(claim_id: int) -> dict:
    USER_TABLE = pd.read_excel(INSURANCE_CLAIMS_EXCEL)
    PAYMENTS_FILE = PAYMENT_RECORDS_EXCEL
    try:
        payments_df = pd.read_excel(PAYMENTS_FILE)
    except Exception:
        payments_df = pd.DataFrame()

    row = USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id]
    if row.empty:
        return {"httpStatusCode": 404, "message": "Claim not found", "claim_id": claim_id, "payment_status": "failure"}

    claim = row.iloc[0].to_dict()
    validation_result = str(claim.get("validation_status", "result missing"))
    policy_verification = str(claim.get("policy_verification", "result missing"))
    underwriter_review = str(claim.get("UnderwriterReview", "result missing"))
    print(validation_result, policy_verification, underwriter_review)

    if (validation_result.lower() == "pass" and policy_verification.lower() == "verified" and underwriter_review.lower() == "approved"):
        # Check for existing payment
        print("condition passed")
        if not payments_df.empty and claim_id in payments_df["claim_id"].values:
            existing = payments_df.loc[payments_df["claim_id"] == claim_id].iloc[0]
            return {
                "httpStatusCode": 200,
                "message": "Payment record already exists",
                "claim_id": claim_id,
                "payment_id": existing["payment_id"],
                "transaction_id": existing["transaction_id"],
                "payment_status": "success"
            }
        # Create new payment
        transaction_id = str(uuid.uuid4())
        payment_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        payment_record = {
            "payment_id": payment_id,
            "transaction_id": transaction_id,
            "claim_id": claim_id,
            "cost": claim.get("cost"),
            "email": claim.get("email"),
            "policy_number": claim.get("policy_number"),
            "timestamp": timestamp
        }
        print(payment_record)
        #payments_df = payments_df.append(payment_record, ignore_index=True)
        payments_df.loc[0] = list(payment_record.values())
        payments_df.to_excel(PAYMENTS_FILE, index=False)
        USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "payment_status"] = "success"
        USER_TABLE.to_excel(INSURANCE_CLAIMS_EXCEL, index=False)
        return {
            "httpStatusCode": 200,
            "message": "Payment record created",
            "claim_id": claim_id,
            "payment_id": payment_id,
            "transaction_id": transaction_id,
            "payment_status": "success"
        }
    else:
        USER_TABLE.loc[USER_TABLE["claim_id"] == claim_id, "payment_status"] = "failure"
        USER_TABLE.to_excel(INSURANCE_CLAIMS_EXCEL, index=False)
        return {
            "httpStatusCode": 403,
            "message": "Claim failed",
            "claim_id": claim_id,
            "validation_result": validation_result,
            "policy_verification": policy_verification,
            "UnderwriterReview": underwriter_review,
            "payment_status": "failure"
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")
    #print(process_payment(1))