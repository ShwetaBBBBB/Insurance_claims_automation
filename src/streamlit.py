import os, asyncio, json, sys, pandas as pd, datetime, streamlit as st, nest_asyncio, atexit
from src.config import DATA_DIR, INSURANCE_CLAIMS_EXCEL, SERVERS_CONFIG_PATH, ensure_dirs

#--------Set Path-----------------------
parent_dir = os.path.dirname(os.path.abspath(__file__))
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)
#------------------------------------------

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from typing import Dict, List
from src.helper_async import on_shutdown, run_async
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.common import get_llm

# Ensure data directories exist
ensure_dirs()

# Load server configuration
if os.path.exists(SERVERS_CONFIG_PATH):
    with open(SERVERS_CONFIG_PATH, 'r') as f:
        SERVER_CONFIG = json.load(f)
else:
    st.error(f"Config file not found: {SERVERS_CONFIG_PATH}")
    SERVER_CONFIG = {"mcpServers": {}}

# Apply nest_asyncio to allow nested asyncio event loops (required by Streamlit)
nest_asyncio.apply()

st.set_page_config(page_title="Insurance Claim Agent", layout="wide")
EXCEL_FILE = INSURANCE_CLAIMS_EXCEL

claim_id = None
def get_next_claim_id():
    """Generate a unique claim_id by checking existing folders."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    existing = [int(name) for name in os.listdir(DATA_DIR) if name.isdigit()]
    return max(existing, default=0) + 1

def save_uploaded_file(uploaded_file, save_dir):
    """Save uploaded file to the specified directory."""
    if uploaded_file is not None:
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def append_to_excel(data_dict, excel_file):
    """Append a row to the Excel file, creating it if needed."""
    df_new = pd.DataFrame([data_dict])
    if not os.path.exists(excel_file):
        df_new.to_excel(excel_file, index=False)
    else:
        df = pd.read_excel(excel_file)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_excel(excel_file, index=False)

async def agent_test():
    model = get_llm()
    agent = create_react_agent(model, st.session_state.tools)

    # Add system message
    system_message = SystemMessage(content=(
            "You have access to multiple tools that can help answer queries. "
            "Use them dynamically and efficiently based on the user's request. "
    ))

    query = "Extract and Validate claim_id 1"
    # Process the query
    agent_response = await agent.ainvoke({"messages": [system_message, HumanMessage(content=query)]})

    print(f"Agent response: {agent_response}")

async def agent_llm(claim_id):

    from src.agent_graph import build_graph

    graph = await build_graph(st.session_state.client)

    user_input = (
        f"Process claim {claim_id}: Perform data extraction, validation, policy verification, "
        f"and fraud detection. If all checks pass, proceed with payment processing and notify the underwriter. "
        f"Provide a summary of the results at each step."
    )
    async for event in graph.astream(
        {"messages": [HumanMessage(content=user_input)]}
    ):
        try:
            for value in event.values():
                for message in value["messages"]:
                    if message.content != "":
                        if message.name == None:
                            with st.expander(f"Assistant", expanded=True):
                                st.markdown(f"<div style='padding:10px;border-radius:8px;'><b>{message.content}</b></div>", unsafe_allow_html=True)
                        else:
                            with st.expander(f"{message.name}", expanded=False):
                                st.markdown(f"<div style='padding:10px;border-radius:8px;'><b>{message.content}</b></div>", unsafe_allow_html=True)
                        
                print("Assistant:", value["messages"][-1].content)
        except Exception as e:
            print(f"Error processing event: {e}")

def main():
    st.title("Insurance Claim Form")
    # --------------- LAYOUT ------------------------
    left_col, right_col = st.columns([2, 1])
    with left_col:

        # Section 1: Personal Details
        with st.expander("Section 1: Personal Details", expanded=True):
            #st.header("Section 1: Personal Details")
            name = st.text_input("Name as per Policy")
            dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
            col1, col2 = st.columns(2)
            with col1:
                period_from = st.date_input("Period of Insurance From", value=None, key="from_date")
            with col2:
                period_to = st.date_input("Period of Insurance To", value=None, key="to_date")
            address = st.text_area("Address")
            contact_number = st.text_input("Contact Number")
            email = st.text_input("Email")
            aadhaar = st.text_input("Aadhaar Number (12-digit numeric)", max_chars=14)
            license_number = st.text_input("License Number")

        # Section 2: Details of Damage/Loss
        with st.expander("Section 2: Details of Damage/Loss", expanded=True):
            
            location_of_accident = st.text_input("Location of Accident")
            description_of_loss = st.text_area("Description of Loss/Image")
            parts_damaged = st.text_area("Parts Damaged")
            cost = st.number_input("Cost", min_value=0.0, format="%f")

        with st.expander("Section 3: Vehicle Details", expanded=True):
            policy_number = st.text_input("Policy Number")
            registration_number = st.text_input("Registration Number")
            make = st.text_input("Make")
            model = st.text_input("Model")

        # Section 4: Document Upload
        with st.expander("Section 4: Document Upload", expanded=True):
    
            aadhaar_file = st.file_uploader("Aadhaar (PDF)", type="pdf")
            license_file = st.file_uploader("License (PDF)", type="pdf")
            registration_certificate = st.file_uploader("Registration Certificate (PDF)", type="pdf")

            if st.button("Submit Claim"):
                if not (aadhaar_file and license_file and registration_certificate):
                    st.warning("Please upload all three files (Aadhaar, License, Registration Certificate)")
                    return

                claim_id = get_next_claim_id()
                st.session_state['last_claim_id'] = claim_id
                claim_folder = os.path.join(DATA_DIR, str(claim_id))
                os.makedirs(claim_folder, exist_ok=True)

                aadhaar_path = save_uploaded_file(aadhaar_file, claim_folder)
                license_path = save_uploaded_file(license_file, claim_folder)
                registration_path = save_uploaded_file(registration_certificate, claim_folder)

                print(aadhaar)
                # Prepare data for Excel
                claim_data = {
                    "claim_id": claim_id,
                    "name": name.strip(),
                    "dob": str(dob),
                    "period_from": str(period_from),
                    "period_to": str(period_to),
                    "address": address,
                    "contact_number": contact_number,
                    "email": email,
                    "aadhaar": aadhaar.strip(),
                    "license_number": license_number.strip(),
                    "location_of_accident": location_of_accident,
                    "description_of_loss": description_of_loss,
                    "parts_damaged": parts_damaged,
                    "cost": float(cost),
                    "policy_number": policy_number.strip(),
                    "registration_number": registration_number.strip(),
                    "make": make,
                    "model": model,
                    "aadhaar_file_path": aadhaar_path,
                    "license_file_path": license_path,
                    "registration_file_path": registration_path
                }

                append_to_excel(claim_data, EXCEL_FILE)
                st.success(f"Claim submitted successfully! Your Claim ID is {claim_id}")

    # ------------- RIGHT: AGENT WORKFLOW -------------
    with right_col:
        st.subheader("🤖 Agent Workflow")
        # Use a session state variable to persist claim_id after submission
        if 'last_claim_id' not in st.session_state:
            st.session_state['last_claim_id'] = None
        if st.button("🚀 Run Multi-Agent Insurance Workflow"):
            if st.session_state['last_claim_id'] is not None:

                # Initialize session state for event loop
                if "loop" not in st.session_state:
                    st.session_state.loop = asyncio.ProactorEventLoop()
                    asyncio.set_event_loop(st.session_state.loop)


                # Register cleanup logic on program exit
                atexit.register(on_shutdown)

                async def setup_mcp_client(server_config: Dict[str, Dict]) -> MultiServerMCPClient:
                    """Initialize a MultiServerMCPClient with the provided server configuration."""
                    client = MultiServerMCPClient(server_config)
                    return await client.__aenter__()

                async def get_tools_from_client(client: MultiServerMCPClient) -> List[BaseTool]:
                    """Get tools from the MCP client."""
                    return client.get_tools()

                st.session_state.servers = SERVER_CONFIG['mcpServers']
                # Setup new MCP client
                st.session_state.client = run_async(setup_mcp_client(st.session_state.servers))

                # Fetch available tools from MCP servers
                st.session_state.tools = run_async(get_tools_from_client(st.session_state.client))

                # print(f"{st.session_state.tools}")

                run_async(agent_llm(st.session_state['last_claim_id']))
            else:
                st.warning("Please submit a claim first.")

if __name__ == "__main__":
    main()