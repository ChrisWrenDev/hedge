from app.modules.pricing.engine import calculate_greeks, black_scholes_price


def run_price_shock(
    spot: float, shock: float, iv: float, strike: float,
    rate: float, time_to_expiry: float, option_type: str, quantity: int,
) -> dict:
    original_price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
    original_greeks = calculate_greeks(spot, strike, rate, time_to_expiry, iv, option_type)

    shocked_spot = spot * (1 + shock)
    new_price = black_scholes_price(shocked_spot, strike, rate, time_to_expiry, iv, option_type)
    new_greeks = calculate_greeks(shocked_spot, strike, rate, time_to_expiry, iv, option_type)

    pnl = (new_price - original_price) * quantity * 100

    return {
        "shock": shock,
        "original_spot": spot,
        "shocked_spot": shocked_spot,
        "original_price": original_price,
        "new_price": new_price,
        "pnl": pnl,
        "original_greeks": {
            "delta": original_greeks.delta, "gamma": original_greeks.gamma,
            "theta": original_greeks.theta, "vega": original_greeks.vega,
        },
        "new_greeks": {
            "delta": new_greeks.delta, "gamma": new_greeks.gamma,
            "theta": new_greeks.theta, "vega": new_greeks.vega,
        },
    }


def run_vol_shock(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float, vol_shock: float,
    option_type: str, quantity: int,
) -> dict:
    original_price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
    original_greeks = calculate_greeks(spot, strike, rate, time_to_expiry, iv, option_type)

    shocked_iv = iv + vol_shock
    new_price = black_scholes_price(spot, strike, rate, time_to_expiry, shocked_iv, option_type)
    new_greeks = calculate_greeks(spot, strike, rate, time_to_expiry, shocked_iv, option_type)

    pnl = (new_price - original_price) * quantity * 100

    return {
        "vol_shock": vol_shock,
        "original_iv": iv,
        "shocked_iv": shocked_iv,
        "original_price": original_price,
        "new_price": new_price,
        "pnl": pnl,
        "original_greeks": {
            "delta": original_greeks.delta, "gamma": original_greeks.gamma,
            "theta": original_greeks.theta, "vega": original_greeks.vega,
        },
        "new_greeks": {
            "delta": new_greeks.delta, "gamma": new_greeks.gamma,
            "theta": new_greeks.theta, "vega": new_greeks.vega,
        },
    }


def run_time_decay(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float,
    decay_days: int, option_type: str, quantity: int,
) -> dict:
    original_price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
    original_greeks = calculate_greeks(spot, strike, rate, time_to_expiry, iv, option_type)

    new_tte = time_to_expiry - (decay_days / 365.0)
    new_tte = max(new_tte, 0.001)
    new_price = black_scholes_price(spot, strike, rate, new_tte, iv, option_type)
    new_greeks = calculate_greeks(spot, strike, rate, new_tte, iv, option_type)

    pnl = (new_price - original_price) * quantity * 100

    return {
        "days_decayed": decay_days,
        "original_time_to_expiry": time_to_expiry,
        "new_time_to_expiry": new_tte,
        "original_price": original_price,
        "new_price": new_price,
        "pnl": pnl,
        "original_greeks": {
            "delta": original_greeks.delta, "gamma": original_greeks.gamma,
            "theta": original_greeks.theta, "vega": original_greeks.vega,
        },
        "new_greeks": {
            "delta": new_greeks.delta, "gamma": new_greeks.gamma,
            "theta": new_greeks.theta, "vega": new_greeks.vega,
        },
    }


def run_combined(
    spot: float, strike: float, rate: float,
    time_to_expiry: float, iv: float,
    price_shock: float, vol_shock: float, decay_days: int,
    option_type: str, quantity: int,
) -> dict:
    original_price = black_scholes_price(spot, strike, rate, time_to_expiry, iv, option_type)
    original_greeks = calculate_greeks(spot, strike, rate, time_to_expiry, iv, option_type)

    shocked_spot = spot * (1 + price_shock)
    shocked_iv = iv + vol_shock
    new_tte = max(time_to_expiry - (decay_days / 365.0), 0.001)

    new_price = black_scholes_price(shocked_spot, strike, rate, new_tte, shocked_iv, option_type)
    new_greeks = calculate_greeks(shocked_spot, strike, rate, new_tte, shocked_iv, option_type)

    pnl = (new_price - original_price) * quantity * 100

    return {
        "shocked_spot": shocked_spot,
        "shocked_iv": shocked_iv,
        "new_time_to_expiry": new_tte,
        "original_price": original_price,
        "new_price": new_price,
        "pnl": pnl,
        "original_greeks": {
            "delta": original_greeks.delta, "gamma": original_greeks.gamma,
            "theta": original_greeks.theta, "vega": original_greeks.vega,
        },
        "new_greeks": {
            "delta": new_greeks.delta, "gamma": new_greeks.gamma,
            "theta": new_greeks.theta, "vega": new_greeks.vega,
        },
    }
