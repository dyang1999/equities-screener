import streamlit as st
import main as m
import pandas as pd
import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

# =============================
# Page Config
# =============================
st.set_page_config(page_title="Market Volatility Explorer", layout="wide")

# =============================
# Sidebar Controls
# =============================
st.sidebar.header("General Settings")
ticker = st.sidebar.text_input("Ticker", "SPY")
tab = st.sidebar.radio(
    "Select View",
    ["Price History", "Volatility Surface", "Volatility Smile Explorer", "News Headlines", "Analyst Ratings", "Insider Trading"]
)

# =============================
# Core Market Data (Cached in main.py)
# =============================
try:
    stock, spot_prices, spot_price = m.get_stock_data(ticker, "10y")
except Exception as e:
    st.warning(
        f"⚠️ Could not fetch market data for **{ticker}**. "
        "You may be rate limited or the ticker is invalid.\n\n"
        f"Error: {e}"
    )
    stock, spot_prices, spot_price = None, pd.DataFrame(), np.nan

# =============================
# Helper: Cached volatility computations
# =============================
@st.cache_data(show_spinner=False)
def get_volatility_data(stock: str, spot_price, r, q, pct):
    calls, expiries = m.get_options_data(stock)
    filt = m.filter_calls_data(
        calls,
        spot_price,
        spot_price * pct[0] / 100,
        spot_price * pct[1] / 100,
    )
    iv_data = m.calculate_implied_volatility(filt, spot_price, r, q)
    return iv_data, expiries


# ======================================================
# TAB 1 — PRICE HISTORY
# ======================================================
if tab == "Price History":
    st.subheader(f"📉 {ticker} Historical Price Data")
    period = st.sidebar.selectbox("Select Period", ["YTD", "1Y", "5Y", "MAX"])

    # Handle timezone-safe filtering
    if isinstance(spot_prices.index, pd.DatetimeIndex):
        if spot_prices.index.tz is not None:
            spot_prices.index = spot_prices.index.tz_convert(None)

        end = spot_prices.index.max()
        now = datetime.now()

        if period == "YTD":
            start = datetime(now.year, 1, 1)
        elif period == "1Y":
            start = end - timedelta(days=365)
        elif period == "5Y":
            start = end - timedelta(days=5 * 365)
        else:
            start = spot_prices.index.min()

        # Safe comparison now that both are timezone-naive
        spot_prices = spot_prices[spot_prices.index >= start]

    # Moving averages
    spot_prices["MA20"] = spot_prices["Close"].rolling(20).mean()
    spot_prices["MA50"] = spot_prices["Close"].rolling(50).mean()

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spot_prices.index, y=spot_prices["Close"], name="Close"))
    fig.add_trace(go.Scatter(x=spot_prices.index, y=spot_prices["MA20"], name="20-Day MA", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=spot_prices.index, y=spot_prices["MA50"], name="50-Day MA", line=dict(dash="dot")))
    fig.update_layout(height=600, template="plotly_white", xaxis_title="Date", yaxis_title="Price ($)")
    st.plotly_chart(fig, use_container_width=True)


# ======================================================
# TAB 2 — VOLATILITY SURFACE
# ======================================================
elif tab == "Volatility Surface":
    st.subheader(f"🌀 Implied Volatility Surface — {ticker}")

    # Sidebar inputs
    r = st.sidebar.number_input("Risk-Free Rate", 0.0, 1.0, 0.01, format="%.4f")
    q = st.sidebar.number_input("Dividend Yield", 0.0, 1.0, 0.001, format="%.4f")
    mode = st.sidebar.selectbox("Plot By", ["Strike Price", "Moneyness"])
    pct = st.sidebar.slider("Strike Range (% of Spot)", 20, 200, (70, 130))

    # Cached volatility data
    iv_data, expiries = get_volatility_data(stock, spot_price, r, q, pct)

    if iv_data.empty:
        st.error("No implied volatility data available for selected parameters.")
    else:
        X, Y, Z = m.prepare_surface_data(iv_data, spot_price, mode == "Moneyness")

        # Interpolation grid
        xi, yi = np.meshgrid(
            np.linspace(min(X), max(X), 30),
            np.linspace(min(Y), max(Y), 30)
        )
        zi = griddata((X, Y), Z, (xi, yi), method="linear", fill_value=np.nan)
        zi = np.where(np.isnan(zi), griddata((X, Y), Z, (xi, yi), method="nearest"), zi)

        # Plot 3D surface
        fig = go.Figure(data=[go.Surface(x=xi, y=yi, z=zi, colorscale="Viridis")])
        fig.update_layout(
            scene=dict(
                xaxis_title="Time to Expiry (yrs)",
                yaxis_title="Moneyness" if mode == "Moneyness" else "Strike ($)",
                zaxis_title="Implied Vol (%)"
            ),
            height=700
        )
        st.plotly_chart(fig, use_container_width=True)


# ======================================================
# TAB 3 — VOLATILITY SMILE EXPLORER
# ======================================================
elif tab == "Volatility Smile Explorer":
    st.subheader("📈 Volatility Smile Explorer")

    # Sidebar inputs
    r = st.sidebar.number_input("Risk-Free Rate", 0.0, 1.0, 0.01, format="%.4f")
    q = st.sidebar.number_input("Dividend Yield", 0.0, 1.0, 0.001, format="%.4f")
    mode = st.sidebar.selectbox("Plot By", ["Strike Price", "Moneyness"])
    pct = st.sidebar.slider("Strike Range (% of Spot)", 20, 200, (70, 130))

    # Cached volatility data
    iv_data, expiries = get_volatility_data(stock, spot_price, r, q, pct)

    if iv_data.empty:
        st.warning("No data available for the selected parameters.")
    else:
        if mode == "Moneyness":
            iv_data["Moneyness"] = iv_data["StrikePrice"] / spot_price

        expiry = st.selectbox("Select Expiration Date", iv_data["ExpirationDate"].unique())
        smile = iv_data[iv_data["ExpirationDate"] == expiry]

        if smile.empty:
            st.warning("No data available for this expiry.")
        else:
            xcol = "Moneyness" if mode == "Moneyness" else "StrikePrice"
            atm = 1.0 if mode == "Moneyness" else spot_price

            fig = px.line(
                smile.sort_values(xcol),
                x=xcol,
                y="ImpliedVolatility",
                title=f"Volatility Smile — Expiration: {expiry}"
            )
            fig.add_vline(x=atm, line_dash="dash", line_color="red")
            fig.update_layout(height=600, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)


# ======================================================
# TAB 4 — NEWS HEADLINES
# ======================================================
elif tab == "News Headlines":
    st.subheader("📰 Recent News")
    st.write(f"Fetching latest headlines for **{ticker}**...")

    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
        req = Request(url, headers={"user-agent": "Mozilla/5.0"})
        html = BeautifulSoup(urlopen(req), "lxml")
        news_table = html.find(id="news-table")
        rows = []
        current_date_label = None

        for tr in news_table.find_all("tr"):
            try:
                headline = tr.a.get_text(strip=True)
                source = tr.span.get_text(strip=True)
                href = tr.a["href"].strip()
                date_text = tr.td.text.strip()
                link = "https://finviz.com" + href if href.startswith("/") else href

                # Restore original Finviz date parsing logic
                if " " in date_text and ":" in date_text:
                    parts = date_text.split()
                    current_date_label = parts[0] if len(parts) == 2 else current_date_label
                    time_str = parts[-1]
                    full_label = f"{current_date_label} {time_str}"
                else:
                    full_label = f"{current_date_label} {date_text}"

                if full_label.startswith("Today"):
                    full_label = full_label.replace("Today", datetime.now().strftime("%b-%d-%y"))

                rows.append({
                    "Headline": headline,
                    "Source": source,
                    "Date": full_label.strip(),
                    "Link": f'<a href="{link}" target="_blank">link</a>'
                })
            except Exception:
                pass

        if rows:
            df = pd.DataFrame(rows)
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No news found for this ticker.")
    except Exception as e:
        st.error(f"Failed to fetch news for {ticker}: {e}")

# ======================================================
# TAB 5 — ANALYST RATINGS
# ======================================================
elif tab == "Analyst Ratings":
    st.subheader("📊 Analyst Ratings and Price Targets")
    st.write(f"Fetching analyst ratings for **{ticker}**...")

    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
        req = Request(url, headers={"user-agent": "Mozilla/5.0"})
        html = BeautifulSoup(urlopen(req), "lxml")

        # ✅ Mimic News find style
        ratings_table = html.find("table", class_="js-table-ratings")
        rows = []

        if ratings_table:
            for tr in ratings_table.find_all("tr"):
                try:
                    tds = tr.find_all("td")
                    if len(tds) == 5:
                        date = tds[0].get_text(strip=True)
                        action = tds[1].get_text(strip=True)
                        analyst = tds[2].get_text(strip=True)
                        rating_change = tds[3].get_text(strip=True)
                        price_target_change = tds[4].get_text(strip=True)

                        rows.append({
                            "Date": date,
                            "Action": action,
                            "Analyst": analyst,
                            "Rating Change": rating_change,
                            "Price Target Change": price_target_change
                        })
                except Exception:
                    pass

        if rows:
            df = pd.DataFrame(rows)
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No analyst ratings found for this ticker.")

    except Exception as e:
        st.error(f"Failed to fetch analyst ratings for {ticker}: {e}")


# ======================================================
# TAB 6 — INSIDER TRADING
# ======================================================
elif tab == "Insider Trading":
    st.subheader("🕵️ Insider Trading Activity")
    st.write(f"Fetching insider trading data for **{ticker}**...")

    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
        req = Request(url, headers={"user-agent": "Mozilla/5.0"})
        html = BeautifulSoup(urlopen(req), "lxml")

        # ✅ Target the insider trading table (like News tab does with id="news-table")
        insider_table = html.find("table", class_="body-table styled-table-new is-rounded p-0 mt-2")
        rows = []

        if insider_table:
            for tr in insider_table.find_all("tr"):
                try:
                    tds = tr.find_all("td")
                    # Expect exactly 9 columns per row
                    if len(tds) == 9:
                        insider = tds[0].get_text(strip=True)
                        relationship = tds[1].get_text(strip=True)
                        date = tds[2].get_text(strip=True)
                        transaction = tds[3].get_text(strip=True)
                        cost = tds[4].get_text(strip=True)
                        shares = tds[5].get_text(strip=True)
                        value = tds[6].get_text(strip=True)
                        shares_total = tds[7].get_text(strip=True)
                        # SEC link (clickable)
                        form4_link_tag = tds[8].find("a")
                        form4_link = form4_link_tag["href"].strip() if form4_link_tag else ""
                        form4_text = form4_link_tag.get_text(strip=True) if form4_link_tag else ""
                        form4_html = (
                            f'<a href="{form4_link}" target="_blank">{form4_text}</a>'
                            if form4_link
                            else form4_text
                        )

                        rows.append({
                            "Insider Trading": insider,
                            "Relationship": relationship,
                            "Date": date,
                            "Transaction": transaction,
                            "Cost": cost,
                            "#Shares": shares,
                            "Value ($)": value,
                            "#Shares Total": shares_total,
                            "SEC Form 4": form4_html
                        })
                except Exception:
                    pass

        if rows:
            df = pd.DataFrame(rows)
            # ✅ Render HTML table like News tab
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.info("No insider trading data found for this ticker.")

    except Exception as e:
        st.error(f"Failed to fetch insider trading data for {ticker}: {e}")


