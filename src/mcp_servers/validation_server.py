from mcp.server.fastmcp import FastMCP
import pandas as pd
from src.config import EXTRACTED_CLAIMS_EXCEL, INSURANCE_CLAIMS_EXCEL

mcp = FastMCP("Validation", host="0.0.0.0", port=8503)

FIELD_MAPPING = {
    "name": "name",
    # "dob": "dob",
    #"aadhar": "aadhar",
    "licence": "license_number",
    # "rc_no": "registration_number",
    # "vehicle_make": "make",
    # "vehicle_model": "model",
}

def normalize_dob(user_dob, extracted_dob):
    if user_dob and extracted_dob:
        try:
            d, m, y = extracted_dob.split('/')
            extracted_value_normalized = f"{y}-{m}-{d}"
            return user_dob == extracted_value_normalized
        except Exception:
            return user_dob == extracted_dob
    return False

@mcp.tool()
def validate(claim_id: int)-> str :
    EXTRACTED_TABLE = pd.read_excel(EXTRACTED_CLAIMS_EXCEL)
    USER_TABLE = pd.read_excel(INSURANCE_CLAIMS_EXCEL)
    
    try:
        if claim_id is None:
            raise ValueError("Missing claim_id in request")

        extracted_table = EXTRACTED_TABLE.loc[EXTRACTED_TABLE["claim_id"]==claim_id].to_dict(orient="records")
        extracted_data = extracted_table[0] if extracted_table else {}

        user_table = USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id].to_dict(orient="records")
        user_data = user_table[0] if user_table else {}

        result = {"claim_id": claim_id, "validation": []}
        all_fields_present = True

        for extracted_field, user_field in FIELD_MAPPING.items():
            user_value = user_data.get(user_field)
            extracted_value = extracted_data.get(extracted_field)
            
            if extracted_field == "dob":
                match = normalize_dob(user_value, extracted_value)
            elif extracted_field == "name" and user_value and extracted_value:
                match = (user_value.strip().lower() == extracted_value.strip().lower())
            else:
                match = (user_value == extracted_value) and user_value is not None
            # If ANY user field is missing, set flag and force match False
            if user_value is None or user_value == "":
                all_fields_present = False
                match = False

            result["validation"].append({
                "field": extracted_field,
                "user_value": user_value,
                "extracted_value": extracted_value,
                "match": match
            })

        # Validation is only "pass" if all fields are present AND all matches are True
        all_match = all(item["match"] for item in result["validation"])
        validation_status = "pass" if all_fields_present and all_match else "fail"

        USER_TABLE.loc[USER_TABLE["claim_id"]==claim_id, "validation_status"] = validation_status
        USER_TABLE.to_excel(INSURANCE_CLAIMS_EXCEL, index=False)
        print(result)
                
        return validation_status
    except Exception as e:
        return f"Error during validation: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server using the stdio transport
    mcp.run(transport="stdio")
    