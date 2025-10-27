# 📊 Equities Screener

An **interactive Streamlit dashboard** for market analysis and volatility exploration.  
It provides a unified interface to analyze:
- Historical stock data  
- Volatility surfaces and smiles  
- Analyst ratings  
- Insider trading activity  
- News headlines  

All data is fetched live from **Yahoo Finance** and **Finviz**.

---

## ⚙️ Installation and Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/dyang1999/equities-screener.git
cd equities-screener
```

### 2️⃣ (Recommended) Create and activate a Conda environment
```bash
conda create -n equities-screener python=3.10 -y
conda activate equities-screener
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
---

## 🚀 Running the App

Once dependencies are installed, start the Streamlit server:
```bash
streamlit run app.py
```
---

## 🧱 Project Structure

```
📦 market-volatility-explorer
├── app.py               # Main Streamlit app (UI + visualization)
├── main.py              # Data orchestration and calculations
├── functions.py         # Black-Scholes and implied volatility functions
├── requirements.txt     # Dependency list
└── README.md            # Project documentation
```

---

## 🌟 Features

### 🧭 1. Price History
- View 10 years of historical data for any ticker.  
- Plot closing prices with 20- and 50-day moving averages.  
- Select data range: **YTD**, **1Y**, **5Y**, or **MAX**.

### ⚡ 2. Volatility Surface
- Calculates **implied volatility** using the Black–Scholes model.  
- Builds an interactive **3D surface** across strike prices and expirations.  
- Adjustable **risk-free rate**, **dividend yield**, and **strike range**.

### 📈 3. Volatility Smile Explorer
- Visualizes the **volatility smile** for chosen expiration dates.  
- Supports plotting by **Strike Price** or **Moneyness**.  
- Displays **ATM (At-The-Money) implied volatility**.

### 📰 4. News Headlines
- Scrapes real-time news for the selected ticker from **Finviz**.  
- Displays clickable headlines with publication date and source.  
- Handles network errors gracefully.

### 📊 5. Analyst Ratings
- Extracts analyst upgrades/downgrades and price target changes.  
- Displays data directly from **Finviz’s Analyst Ratings** table.  
- Organized by **date, action, analyst, and rating change**.

### 🕵️ 6. Insider Trading
- Scrapes insider trading data from Finviz.  
- Displays **insider name, position, transaction type, shares, value**, and **SEC Form 4 link**.  
- Matches Finviz’s table formatting for clarity.

### 🎯 7. Prediction Market Insights
- Integrates **Polymarket’s Gamma API** to explore active prediction markets.  
- Search for events by **keywords, tickers, or macro themes** (e.g., *Fed*, *Tesla*, *Election*, *Inflation*).  
- Categorizes results into:
  - **🎯 Direct Matches** — keyword appears in the event title or slug.  
  - **🧩 Market-Level Matches** — keyword found in one or more market questions.  
- Displays:
  - **Event title**, **total trading volume**, and **individual market outcomes** (Yes/No probabilities).  
  - Clickable links to view live markets on **Polymarket**.  
- Efficiently cached and sorted by **market volume**, with real-time data fetching and rate-limit handling.

---

## 🧠 Technical Highlights

| Module | Description |
|--------|--------------|
| `functions.py` | Core math utilities: Black–Scholes pricing, implied volatility solvers. |
| `main.py` | Handles stock data retrieval and options data processing. |
| `app.py` | Streamlit UI: tabs, caching, visualization, and error handling. |
| **Caching** | Uses `st.cache_data` to improve responsiveness. |
| **Visualization** | Built with Plotly for 2D/3D interactivity. |
| **External APIs** | Fetches live data from Yahoo Finance, Finviz, and Polymarket Gamma API. |

---

## 💡 Example Usage
```bash
streamlit run app.py
```

Enter a ticker symbol (e.g., `TSLA`, `AAPL`, `NVDA`) in the sidebar to explore:
- Price charts  
- Option volatility metrics  
- News and analyst sentiment  
- Insider trading activity  
—all in one place.
