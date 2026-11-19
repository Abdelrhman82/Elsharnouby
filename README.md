# 🏢 El-Sharnouby Group Executive Enterprise Platform

An enterprise-grade executive analytics dashboard and AI-powered business strategy advisor designed for **El-Sharnouby Group (مجموعة الشرنوبي)** — encompassing its textile, fashion, and manufacturing entities (**LEO MODA**, **LEO TEX**, **LEO PRINT**, **LEO PRODUCTION HUB**, and **LEO DESIGN**).

The platform bridges real-time business intelligence across multi-channel retail/wholesale, manufacturing, inventory supply chain, customer segments, and financial health with an integrated generative AI business advisor.

---

## 🌟 Key Features

### 1. 📊 Executive Multi-Workspace Dashboards
- **CEO Command Home**: High-level C-suite overview of Gross & Net Sales, Gross Profit Margins, Order Volumes, and Operational Alerts.
- **Sales Command Center**: Comprehensive financial analytics, channel performance (Retail, Wholesale, Online D2C, Marketplaces), discount vs. margin trade-offs, and geographic breakdowns.
- **Products & Merchandising Mix**: SKU and category-level profitability, top/bottom sellers, product velocity, and size/color distribution.
- **Customer Intelligence (RFM)**: Recency, Frequency, and Monetary (RFM) customer segmentation, lifetime value (CLV), churn risks, and repeat purchase patterns.
- **Channels & Marketplaces**: In-depth comparison of multi-channel margins, return rates, and customer acquisition costs.
- **Operations & Supply Chain Pulse**: Plant production bottlenecks, machine downtime, quality pass/fail rates, scrap costs, and days-of-inventory cover alerts.
- **Interactive Data Explorer**: Instant search, multi-column sorting, filtering, and CSV export capabilities across raw records.

### 2. 🤖 Enterprise AI Business Strategy Advisor
- **Context-Aware Analytics**: Uses Google Gemini to analyze active ledger views, historical trends, supply bottlenecks, and inventory risks.
- **Strict Guardrails & Governance**: Built with corporate guardrails to prevent hallucinations, strictly refuse unrelated/general queries, and maintain focus on corporate financial intelligence.
- **Executive Response Framework**: Delivers responses structured as *Executive Summary*, *Deep-Dive Root Cause Analysis*, and *Prioritized Strategic C-Suite Recommendations* (bilingual support with Arabic business reporting).

### 3. ⚡ High-Performance Architecture
- **Parquet Caching Layer**: Automated conversion of multi-million row CSV transaction tables to columnar Apache Parquet format for sub-second query and filtering response times.
- **Modern Responsive UI**: Clean, responsive frontend built with modern CSS variables, interactive [Chart.js](https://www.chartjs.org/) visualizations, and Markdown rendering.

---

## 🏗️ Architecture & Project Structure

```text
├── app.py                     # FastAPI application entry point, API routes & analytics logic
├── core/
│   ├── chat_engine.py         # Gemini LLM integration, enterprise prompt & context builder
│   ├── data_loader.py         # Multi-dataset loading, Parquet caching & ETL logic
│   └── .cache/                # High-speed Parquet cache directory (auto-generated)
├── data/                      # Enterprise CSV data files
│   ├── Sales_Transactions.csv # Core transaction records
│   ├── Customers.csv          # Customer registry & demographics
│   ├── Production_Orders.csv  # Manufacturing orders
│   ├── Inventory_History.csv  # Stock movements & warehouse data
│   ├── Quality.csv            # Defect logs & inspection records
│   ├── Marketing.csv          # Ad spend & campaign metrics
│   ├── Product_Master.csv     # Product hierarchy & SKUs
│   └── ...                    # Additional business unit files
├── static/                    # Frontend presentation layer
│   ├── index.html             # Single-page dashboard interface
│   ├── style.css              # Custom enterprise design system & styling
│   ├── app.js                 # State management, Chart.js renderers & API client
│   └── logo/                  # Corporate assets & brand emblem
├── ELsharnouby_Analysis.ipynb # Jupyter Notebook with exploratory data analysis (EDA)
├── requirements.txt           # Python dependencies
├── .env.example               # Template for environment configuration
└── .gitignore                 # Standard repository ignore rules
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10+` recommended
- **Git**

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/el-sharnouby-enterprise-platform.git
   cd el-sharnouby-enterprise-platform
   ```

2. **Create and activate a virtual environment**:
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```
   Set your Google Gemini API key inside `.env`:
   ```env
   GEMINI_API_KEY="your-actual-api-key"
   ```

---

## 💻 Running the Application

Launch the application using Uvicorn:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Once running, access the services:
- **Interactive Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Specification**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/), [Uvicorn](https://www.uvicorn.org/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [PyArrow](https://arrow.apache.org/docs/python/)
- **Frontend**: Modern Vanilla JS (ES6+), HTML5, CSS3 Variables & Flexbox/Grid
- **Visualizations**: [Chart.js](https://www.chartjs.org/)
- **AI / LLM Integration**: [Google Gemini API](https://ai.google.dev/) (via REST endpoint with structured enterprise context injection)
- **Data Science / EDA**: Jupyter Notebook

