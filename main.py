import yfinance as yf
import pandas as pd
import numpy as np
import functions as f
from functools import lru_cache
import streamlit as st

@lru_cache(maxsize=32)
def get_stock_data(ticker_symbol: str = "SPY", period: str = "1y"):
    """
    Fetch stock historical data and current spot price.
    Cached to prevent repeated API calls.
    """
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period)

    if hist.empty:
        raise ValueError(f"No data available for ticker {ticker_symbol}.")

    close_df = hist["Close"].to_frame()
    try:
        spot_price = stock.history(period="1d")["Close"].iloc[-1]
    except Exception:
        spot_price = close_df["Close"].iloc[-1]

    return ticker_symbol, close_df, float(spot_price)


@st.cache_data(show_spinner=False)
def get_options_data(ticker_symbol: str):
    """Fetch all call options and available expiration dates."""
    stock = yf.Ticker(ticker_symbol)
    expiration_dates = stock.options
    calls = []
    for date in expiration_dates:
        df = stock.option_chain(date).calls.copy()
        df["expiration"] = date
        calls.append(df)
    return pd.concat(calls, ignore_index=True), expiration_dates


@st.cache_data(show_spinner=False)
def filter_calls_data(calls_df: pd.DataFrame, spot_price: float,
                      min_strike: float, max_strike: float) -> pd.DataFrame:
    """Filter calls based on strike and time to expiration."""
    mask = (calls_df["strike"].between(min_strike, max_strike))
    calls_df = calls_df.loc[mask].copy()
    calls_df["time_to_expiry"] = calls_df["expiration"].apply(f.calculate_time_to_expiration)
    return calls_df[calls_df["time_to_expiry"] > 0.07].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def calculate_implied_volatility(filtered_df: pd.DataFrame, spot_price: float,
                                 r: float, q: float) -> pd.DataFrame:
    """
    Calculate implied volatilities for call options.
    Uses Streamlit caching for performance (handles DataFrames safely).
    """
    records = []
    for _, row in filtered_df.iterrows():
        iv = f.call_iv(
            S=spot_price,
            X=row["strike"],
            r=r,
            T=row["time_to_expiry"],
            call_price=row["lastPrice"],
            q=q
        )
        if not np.isnan(iv):
            records.append({
                "ContractSymbol": row["contractSymbol"],
                "StrikePrice": row["strike"],
                "TimeToExpiry": row["time_to_expiry"],
                "ImpliedVolatility": iv,
                "ExpirationDate": row["expiration"]
            })

    return pd.DataFrame.from_records(records)


def prepare_surface_data(df: pd.DataFrame, spot_price: float, by_moneyness: bool):
    """Return X, Y, Z arrays for surface plotting."""
    if by_moneyness:
        df["Y"] = df["StrikePrice"] / spot_price
    else:
        df["Y"] = df["StrikePrice"]

    return (
        df["TimeToExpiry"].values,
        df["Y"].values,
        df["ImpliedVolatility"].values * 100
    )
