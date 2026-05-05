from mcp.server.fastmcp import FastMCP
import pandas as pd
from src.config import UNDERWRITER_LIST_EXCEL

mcp = FastMCP("Notification", host="0.0.0.0", port=8507)

def send_mail():
    pass

@mcp.tool()
def notify(claim_id: int, message :str ) -> str:
    UNDERWRITER_DATA = pd.read_excel(UNDERWRITER_LIST_EXCEL)

    underwriter_data = UNDERWRITER_DATA.loc[UNDERWRITER_DATA["Availability"]=="available"].to_dict(orient="records")
    available_underwriter_data = underwriter_data[0] if underwriter_data else {}

    

    Name = available_underwriter_data.get("Name")
    Email = available_underwriter_data.get("Email")

    print("Available underwriter:", Name, Email, message)
    

    # UNDERWRITER_DATA.loc[UNDERWRITER_DATA["Name"]==Name, "Availability"] = "busy"
    # UNDERWRITER_DATA.to_excel('./data/underwriter_list.xlsx', index=False)


    return f"Notification send to available underwriter {Email} for {claim_id}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
    #notification(1, "succfull")