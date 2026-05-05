from mcp.server.fastmcp import FastMCP
import pandas as pd
from src.config import INSURANCE_CLAIMS_EXCEL, POLICY_DATA_EXCEL

mcp = FastMCP("Verification",host="0.0.0.0", port=8504)

def get_policy_dataframe():
    local_path = POLICY_DATA_EXCEL
    df = pd.read_excel(local_path)
    # Normalize column names: strip spaces and lowercase
    df.columns = df.columns.str.strip().str.lower()
    print("Normalized columns:", df.columns.tolist())  # For debugging
    return df

@mcp.tool()   
def verify(claim_id: int) -> str:
    USER_TABLE = pd.read_excel(INSURANCE_CLAIMS_EXCEL)

    user_table = USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id].to_dict(orient="records")
    user_data = user_table[0] if user_table else {}

    user_policy_number = user_data.get("policy_number")
    user_name = user_data.get("name")
    validation_result = user_data.get("validation_status")

    print("Tool result" , validation_result)

    if validation_result != "pass":

        USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id, "policy_verification"] = "not checked"
        USER_TABLE.to_excel('./data/insurance_claims.xlsx', index=False)
        return "Validation failed. Policy verification not performed."

    print(f"Verifying policy number {user_policy_number} for name {user_name}")
    df = get_policy_dataframe()
    match_row = df[
            (df['policy number'].astype(str) == str(user_policy_number)) &
            (df['full name'].str.strip().str.lower() == str(user_name).strip().lower())
        ]

    if not user_policy_number or not user_name:
        verification_status = "not verified"
        USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id, "policy_verification"] = verification_status
    elif len(match_row) > 0:
        verification_status = "verified"
        USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id, "policy_verification"] = verification_status
    else:
        verification_status = "unverified"
        USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id, "policy_verification"] = verification_status

    
    USER_TABLE.to_excel(INSURANCE_CLAIMS_EXCEL, index=False)

    return f"Policy verification for claim {claim_id}: {verification_status}"


if __name__ == "__main__":
    # Run the MCP server using the stdio transport
    mcp.run(transport="stdio")
    #print(verify(1))