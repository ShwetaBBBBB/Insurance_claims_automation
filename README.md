# MCP Insurance Claim Processing System

An intelligent, multi-agent insurance claim processing system leveraging **LangGraph**, **Model Context Protocol (MCP)**, and **Azure AI**.

## 🚀 Overview

This project automates the end-to-end lifecycle of an insurance claim, from document extraction to payment processing. It uses a modular architecture where specific tasks are delegated to MCP servers, orchestrated by a central LLM-based agent.

### Key Features
- **Automated Document Extraction**: Uses Azure Document Intelligence to parse Aadhaar, Driving Licenses, and Registration Certificates.
- **Data Validation**: Cross-verifies extracted data with user-provided information.
- **Policy Verification**: Validates policy details against a master database.
- **Fraud Detection**: Rule-based risk assessment to identify suspicious claims.
- **Payment Processing**: Generates secure transaction records for approved claims.
- **Interactive UI**: Streamlit-based dashboard to manage and monitor the workflow.

## 🏗 Architecture

The system follows a micro-tool architecture using MCP:

- **Orchestrator**: Built with LangGraph, it manages the conversation state and tool selection.
- **MCP Servers**: Each server is a standalone process communicating via `stdio` transport.
- **Data Store**: Uses Excel files for demo-ready data persistence.

For a detailed view, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🛠 Setup & Installation

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/) (recommended)
- Azure Document Intelligence instance
- Azure OpenAI instance

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd MCP
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # OR using poetry
   poetry install
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory (see `.env.example` for reference):
   ```env
   OPENAI_API_KEY="your_key"
   AZURE_OPENAI_ENDPOINT="your_endpoint"
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="your_doc_int_endpoint"
   AZURE_DOCUMENT_INTELLIGENCE_KEY="your_doc_int_key"
   ```

## 🏃 Running the Application

### 1. Run the Streamlit Dashboard
```bash
streamlit run src/streamlit.py
```

### 2. Run via CLI (for testing)
```bash
python src/main.py <claim_id>
```

## 📂 Project Structure

- `src/`: Core source code.
  - `agent_graph.py`: LangGraph workflow definition.
  - `mcp_servers/`: Individual MCP server implementations.
  - `config.py`: Centralized configuration management.
  - `streamlit.py`: Frontend application.
- `data/`: Sample data and database files.
- `docs/`: Documentation and architecture diagrams.

## 🛡 Security Note
- Never commit your `.env` file.
- Azure keys are managed through environment variables for security.

## 📄 License
This project is for internal use and demonstration purposes.
