from scipy.optimize import brentq
from datetime import datetime
from scipy.stats import norm
import numpy as np
import scipy as sp

def call_bs_value(S: float, X: float, r: float, T: float, v: float, q: float) -> float:
    """
    Black-Scholes value of a call option with dividend yield.

    Parameters:
        S: Current stock price
        X: Strike price
        r: Risk-free rate
        T: Time to expiration in years
        v: Volatility
        q: Dividend yield
    """
    d1 = (np.log(S / X) + (r - q + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    d2 = d1 - v * np.sqrt(T)
    return S * np.exp(-q * T) * norm.cdf(d1) - X * np.exp(-r * T) * norm.cdf(d2)


def put_bs_value(S: float, X: float, r: float, T: float, v: float, q: float) -> float:
    """Black-Scholes value of a put option with dividend yield."""
    d1 = (np.log(S / X) + (r - q + 0.5 * v ** 2) * T) / (v * np.sqrt(T))
    d2 = d1 - v * np.sqrt(T)
    return X * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def call_iv(S: float, X: float, r: float, T: float, call_price: float, q: float,
            a: float = 1e-6, b: float = 5.0, xtol: float = 1e-6) -> float:
    """
    Compute implied volatility of a call option using Brent's method.
    Returns np.nan if solution not found.
    """
    def obj(v):
        return call_price - call_bs_value(S, X, r, T, v, q)

    try:
        return brentq(obj, a, b, xtol=xtol)
    except ValueError:
        return np.nan


def put_iv(S: float, X: float, r: float, T: float, put_price: float, q: float,
           a: float = 1e-6, b: float = 5.0, xtol: float = 1e-6) -> float:
    """Compute implied volatility of a put option using Brent's method."""
    def obj(v):
        return put_price - put_bs_value(S, X, r, T, v, q)

    try:
        return brentq(obj, a, b, xtol=xtol)
    except ValueError:
        return np.nan


def calculate_iv(S: float, X: float, r: float, T: float, price: float,
                 option_type: str, q: float) -> float:
    """Wrapper to compute IV for calls or puts."""
    if option_type.upper() == 'C':
        return call_iv(S, X, r, T, price, q)
    elif option_type.upper() == 'P':
        return put_iv(S, X, r, T, price, q)
    return np.nan


def calculate_time_to_expiration(expiration_date_str: str) -> float:
    """
    Calculate time to expiration (years) from today.

    Returns:
        Time to expiry in years (float)
    """
    expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
    delta_days = (expiration_date - datetime.now()).days
    return max(delta_days / 365.0, 0.0)
