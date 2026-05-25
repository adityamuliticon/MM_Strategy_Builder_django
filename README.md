# Market Maya Unified Strategy Builder 🚀

An advanced, AI-powered algorithmic trading strategy builder designed specifically for the **Market Maya V3 API**. This system leverages **Model Context Protocol (MCP)** and **Retrieval-Augmented Generation (RAG)** to provide professional traders with a documentation-driven, multi-leg deployment pipeline.

![Market Maya Logo](https://terminal.marketmaya.com/assets/images/logo.png)

## 🌟 Key Features

### **1. Professional Multi-Leg Support**
*   Deploy up to **10 distinct legs** in a single strategy.
*   Support for all **8 BRD Strike Selection models** (ATM%, Premium Range, Delta, Theta, etc.).
*   Independent Leg-level Target, SL, and **Wait & Trade** logic.

### **2. Advanced Risk Management (12-Section Advance Tab)**
*   **Master Profit Locking**: Protect gains at the strategy level with multi-step trailing.
*   **Action Chaining**: Execute, Reenter, or Sqroff specific legs based on Target/SL hits.
*   **Safety Triggers**: "Sqroff All Legs" and "Sqroff on Rejection" enabled by default.

### **3. Intelligence Layer (RAG & MCP)**
*   **Documentation-Driven**: The system retrieves real-time validation rules from the official BRD using a FAISS vector store.
*   **Hallucination Prevention**: Strict JSON schema enforcement ensures every parameter maps 1:1 to the production API.

### **4. Premium Trading Experience**
*   **Glassmorphic UI**: High-end, responsive dashboard with real-time markdown strategy previews.
*   **Two-Step Deployment**: Visualize your strategy in detailed UI-matched tables before committing to the market.

---

## 🛠️ Tech Stack

*   **Frontend**: HTML5, Vanilla CSS (Glassmorphism), Javascript (Real-time Markdown).
*   **Backend**: Flask (Python).
*   **AI Orchestration**: Runware / OpenAI API.
*   **Vector DB**: FAISS with HuggingFace Embeddings (`all-MiniLM-L6-v2`).
*   **Protocol**: Model Context Protocol (MCP).

---

## 🚀 Getting Started

### **1. Prerequisites**
*   Python 3.10+
*   Market Maya Production Bearer Token.
*   OpenAI / Runware API Key.

### **2. Installation**
```bash
# Clone the repository
git clone https://github.com/aditya/MM_Unified_Strategy_Builder.git
cd MM_Unified_Strategy_Builder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configuration**
Create a `.env` file in the root directory:
```env
RUNWARE_API_KEY=your_key
MARKET_MAYA_BEARER_TOKEN=your_token
SECRET_KEY=your_secret
```

### **4. Ingest Documentation**
```bash
python3 rag/ingest.py
```

### **5. Run the Application**
```bash
python3 app.py
```
Visit `http://localhost:5000` to start building strategies.

---

## 📖 Architecture & Workflow

1.  **Input**: User describes a strategy in natural language.
2.  **RAG**: System fetches parameter constraints from the `MM - Unified Strategy Builder Plugin.md`.
3.  **Preview**: System generates **Main**, **Legs**, and **12-Section Advance** tables.
4.  **Deployment**: Upon approval, the `generator.py` produces a production-ready V3 payload and deploys it via `market_maya.py`.

---

## ⚖️ License
Internal Use Only. Confidential and Proprietary.

---
*Built for Traders by Aditya & Antigravity AI.*
# MM_Unified_Strategy_Builder
# MM_Strategy_Builder_django
# MM_Strategy_Builder_django
