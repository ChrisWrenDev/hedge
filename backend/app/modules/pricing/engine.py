import math
from dataclasses import dataclass


@dataclass
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


def _normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes_price(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float, option_type: str,
) -> float:
    """Calculate Black-Scholes theoretical option price."""
    if option_type not in ("call", "put"):
        raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'.")

    if time_to_expiry <= 0:
        if option_type == "call":
            return max(spot - strike, 0.0)
        else:
            return max(strike - spot, 0.0)

    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * time_to_expiry) / (iv * sqrt_t)
    d2 = d1 - iv * sqrt_t

    if option_type == "call":
        return spot * _normal_cdf(d1) - strike * math.exp(-rate * time_to_expiry) * _normal_cdf(d2)
    else:
        return strike * math.exp(-rate * time_to_expiry) * _normal_cdf(-d2) - spot * _normal_cdf(-d1)


def calculate_greeks(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float, option_type: str,
) -> Greeks:
    """Calculate Black-Scholes Greeks."""
    if option_type not in ("call", "put"):
        raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'.")

    if time_to_expiry <= 0:
        return Greeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)

    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * time_to_expiry) / (iv * sqrt_t)
    d2 = d1 - iv * sqrt_t
    n_d1 = _normal_pdf(d1)
    N_d1 = _normal_cdf(d1)
    N_d2 = _normal_cdf(d2)
    discount = math.exp(-rate * time_to_expiry)

    # Delta
    if option_type == "call":
        delta = N_d1
    else:
        delta = N_d1 - 1.0

    # Gamma (same for calls and puts)
    gamma = n_d1 / (spot * iv * sqrt_t)

    # Theta
    theta_common = -(spot * n_d1 * iv) / (2.0 * sqrt_t)
    if option_type == "call":
        theta = theta_common - rate * strike * discount * N_d2
    else:
        theta = theta_common + rate * strike * discount * _normal_cdf(-d2)
    # Convert to per-day
    theta = theta / 365.0

    # Vega (same for calls and puts, per 1% change in IV)
    vega = spot * n_d1 * sqrt_t / 100.0

    # Rho
    if option_type == "call":
        rho = strike * time_to_expiry * discount * N_d2 / 100.0
    else:
        rho = -strike * time_to_expiry * discount * _normal_cdf(-d2) / 100.0

    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


def calculate_iv(
    market_price: float, spot: float, strike: float,
    rate: float, time_to_expiry: float, option_type: str,
) -> float:
    """Calculate implied volatility via Newton-Raphson iteration."""
    if market_price <= 0:
        raise ValueError("market_price must be positive")
    if time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be positive")
    if option_type not in ("call", "put"):
        raise ValueError(f"Invalid option_type: {option_type}")

    # Initial guess
    iv = 0.30
    for _ in range(100):
        price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
        diff = price - market_price

        if abs(diff) < 1e-8:
            return iv

        # Vega for Newton-Raphson (need raw vega, not per-1%)
        sqrt_t = math.sqrt(time_to_expiry)
        d1 = (math.log(spot / strike) + (rate + 0.5 * iv * iv) * time_to_expiry) / (iv * sqrt_t)
        vega_raw = spot * _normal_pdf(d1) * sqrt_t

        if vega_raw < 1e-12:
            break

        iv = iv - diff / vega_raw
        iv = max(iv, 0.001)  # Floor to avoid negative IV

    return iv
