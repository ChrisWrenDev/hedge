def compute_score(
    gamma_per_theta: float,
    vega_normalized: float,
    iv_rank: float,
    volume_oi_ratio: float,
    dte: float,
) -> float:
    """Compute composite convexity score (0-100).

    Weights:
        gamma_per_theta   0.30  — Higher = cheaper convexity
        vega_normalized   0.25  — Vol exposure per $ of premium
        iv_rank_inverse   0.20  — Lower IV rank = better value
        volume_oi_ratio   0.15  — Liquidity factor
        dte_factor        0.10  — Optimal DTE window (30-60 days)
    """
    # Normalize gamma_per_theta: 0->0, 5+->1.0
    gpt_norm = min(max(gamma_per_theta / 5.0, 0.0), 1.0)

    # Normalize vega_normalized: 0->0, 0.05+->1.0
    vega_norm = min(max(vega_normalized / 0.05, 0.0), 1.0)

    # IV rank inverse: 0 rank -> 1.0 score, 100 rank -> 0.0 score
    iv_inv = max(1.0 - (iv_rank / 100.0), 0.0)

    # Volume/OI ratio: 0->0, 0.5+->1.0
    liq_norm = min(max(volume_oi_ratio / 0.5, 0.0), 1.0)

    # DTE factor: peak at 45 days, decays towards 0 and 180+
    if dte <= 0:
        dte_factor = 0.0
    elif dte <= 45:
        dte_factor = dte / 45.0
    elif dte <= 90:
        dte_factor = 1.0 - (dte - 45) / 180.0  # Slow decay
    else:
        dte_factor = max(0.3, 1.0 - dte / 365.0)

    score = (
        0.30 * gpt_norm
        + 0.25 * vega_norm
        + 0.20 * iv_inv
        + 0.15 * liq_norm
        + 0.10 * dte_factor
    ) * 100.0

    return round(min(max(score, 0.0), 100.0), 2)


def rank_by_convexity(options: list[dict]) -> list[dict]:
    """Rank options by convexity score (descending).

    Each option dict must have 'occ_symbol' and 'score' keys.
    Adds a 'rank' field to each option.
    """
    sorted_opts = sorted(options, key=lambda o: o.get("score", 0), reverse=True)
    for i, opt in enumerate(sorted_opts, start=1):
        opt["rank"] = i
    return sorted_opts
