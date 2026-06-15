import math
import pytest


# ── Black-Scholes Pricing ──────────────────────────────────────

class TestBlackScholesPrice:
    """Test theoretical option pricing via Black-Scholes."""

    def test_call_price_at_the_money(self):
        from app.modules.pricing.engine import black_scholes_price
        price = black_scholes_price(
            spot=100.0, strike=100.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30, option_type="call"
        )
        assert 4.0 < price < 8.0  # ATM call with 30% IV, 3m expiry

    def test_put_price_at_the_money(self):
        from app.modules.pricing.engine import black_scholes_price
        price = black_scholes_price(
            spot=100.0, strike=100.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30, option_type="put"
        )
        assert 2.0 < price < 6.0  # ATM put

    def test_call_deep_in_the_money(self):
        from app.modules.pricing.engine import black_scholes_price
        price = black_scholes_price(
            spot=100.0, strike=80.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30, option_type="call"
        )
        # Deep ITM call ≈ intrinsic + time value
        assert price > 20.0  # At least intrinsic value of 20

    def test_call_deep_out_of_the_money(self):
        from app.modules.pricing.engine import black_scholes_price
        price = black_scholes_price(
            spot=100.0, strike=120.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30, option_type="call"
        )
        assert price < 2.0  # Deep OTM, nearly worthless

    def test_put_call_parity(self):
        """C - P = S - K*e^(-rT)"""
        from app.modules.pricing.engine import black_scholes_price
        S, K, r, T, iv = 100.0, 100.0, 0.05, 0.25, 0.30
        call = black_scholes_price(S, K, r, T, iv, "call")
        put = black_scholes_price(S, K, r, T, iv, "put")
        parity = S - K * math.exp(-r * T)
        assert abs((call - put) - parity) < 0.01

    def test_price_increases_with_volatility(self):
        from app.modules.pricing.engine import black_scholes_price
        low_vol = black_scholes_price(100, 100, 0.05, 0.25, 0.20, "call")
        high_vol = black_scholes_price(100, 100, 0.05, 0.25, 0.40, "call")
        assert high_vol > low_vol

    def test_price_increases_with_time(self):
        from app.modules.pricing.engine import black_scholes_price
        short = black_scholes_price(100, 100, 0.05, 0.10, 0.30, "call")
        long = black_scholes_price(100, 100, 0.05, 0.50, 0.30, "call")
        assert long > short

    def test_zero_time_to_expiry_returns_intrinsic(self):
        from app.modules.pricing.engine import black_scholes_price
        call = black_scholes_price(100, 95, 0.05, 0.0, 0.30, "call")
        assert abs(call - 5.0) < 0.01  # Intrinsic = max(S-K, 0)

    def test_invalid_option_type_raises(self):
        from app.modules.pricing.engine import black_scholes_price
        with pytest.raises(ValueError):
            black_scholes_price(100, 100, 0.05, 0.25, 0.30, "invalid")


# ── Greeks Calculation ──────────────────────────────────────────

class TestCalculateGreeks:
    """Test Black-Scholes Greeks."""

    @pytest.fixture
    def atm_greeks(self):
        from app.modules.pricing.engine import calculate_greeks
        return calculate_greeks(
            spot=100.0, strike=100.0, rate=0.05,
            time_to_expiry=0.25, iv=0.30, option_type="call"
        )

    def test_atm_call_delta_near_half(self, atm_greeks):
        assert 0.45 < atm_greeks.delta < 0.60

    def test_gamma_positive(self, atm_greeks):
        assert atm_greeks.gamma > 0

    def test_theta_negative_for_long(self, atm_greeks):
        assert atm_greeks.theta < 0

    def testvega_positive(self, atm_greeks):
        assert atm_greeks.vega > 0

    def test_rho_call_positive(self, atm_greeks):
        assert atm_greeks.rho >= 0

    def test_put_delta_negative(self):
        from app.modules.pricing.engine import calculate_greeks
        greeks = calculate_greeks(100, 100, 0.05, 0.25, 0.30, "put")
        assert -0.60 < greeks.delta < -0.40

    def test_deep_itm_call_delta_near_one(self):
        from app.modules.pricing.engine import calculate_greeks
        greeks = calculate_greeks(100, 80, 0.05, 0.25, 0.30, "call")
        assert greeks.delta > 0.90

    def test_deep_otm_call_delta_near_zero(self):
        from app.modules.pricing.engine import calculate_greeks
        greeks = calculate_greeks(100, 120, 0.05, 0.25, 0.30, "call")
        assert greeks.delta < 0.20

    def test_gamma_highest_at_the_money(self):
        from app.modules.pricing.engine import calculate_greeks
        atm = calculate_greeks(100, 100, 0.05, 0.25, 0.30, "call")
        otm = calculate_greeks(100, 120, 0.05, 0.25, 0.30, "call")
        assert atm.gamma > otm.gamma

    def test_theta_increases_with_shorter_expiry(self):
        from app.modules.pricing.engine import calculate_greeks
        long = calculate_greeks(100, 100, 0.05, 0.50, 0.30, "call")
        short = calculate_greeks(100, 100, 0.05, 0.05, 0.30, "call")
        # Shorter expiry = more negative theta (per day)
        assert short.theta < long.theta

    def test_greeks_invalid_type_raises(self):
        from app.modules.pricing.engine import calculate_greeks
        with pytest.raises(ValueError):
            calculate_greeks(100, 100, 0.05, 0.25, 0.30, "invalid")

    def test_greeks_returns_dataclass(self, atm_greeks):
        assert hasattr(atm_greeks, "delta")
        assert hasattr(atm_greeks, "gamma")
        assert hasattr(atm_greeks, "theta")
        assert hasattr(atm_greeks, "vega")
        assert hasattr(atm_greeks, "rho")


# ── Implied Volatility ──────────────────────────────────────────

class TestCalculateIV:
    """Test IV calculation via Newton-Raphson."""

    def test_roundtrip_call(self):
        from app.modules.pricing.engine import black_scholes_price, calculate_iv
        price = black_scholes_price(100, 100, 0.05, 0.25, 0.30, "call")
        iv = calculate_iv(price, 100, 100, 0.05, 0.25, "call")
        assert abs(iv - 0.30) < 0.001

    def test_roundtrip_put(self):
        from app.modules.pricing.engine import black_scholes_price, calculate_iv
        price = black_scholes_price(100, 100, 0.05, 0.25, 0.30, "put")
        iv = calculate_iv(price, 100, 100, 0.05, 0.25, "put")
        assert abs(iv - 0.30) < 0.001

    def test_roundtrip_deep_itm(self):
        from app.modules.pricing.engine import black_scholes_price, calculate_iv
        price = black_scholes_price(100, 80, 0.05, 0.25, 0.30, "call")
        iv = calculate_iv(price, 100, 80, 0.05, 0.25, "call")
        assert abs(iv - 0.30) < 0.005

    def test_roundtrip_otm(self):
        from app.modules.pricing.engine import black_scholes_price, calculate_iv
        price = black_scholes_price(100, 110, 0.05, 0.25, 0.25, "call")
        iv = calculate_iv(price, 100, 110, 0.05, 0.25, "call")
        assert abs(iv - 0.25) < 0.005

    def test_invalid_price_raises(self):
        from app.modules.pricing.engine import calculate_iv
        with pytest.raises(ValueError):
            calculate_iv(-1.0, 100, 100, 0.05, 0.25, "call")

    def test_zero_time_to_expiry_raises(self):
        from app.modules.pricing.engine import calculate_iv
        with pytest.raises(ValueError):
            calculate_iv(5.0, 100, 100, 0.05, 0.0, "call")


# ── Greeks Snapshot Model ───────────────────────────────────────

class TestGreeksSnapshotModel:
    """Test the GreeksSnapshot DB model."""

    @pytest.mark.asyncio
    async def test_create_greeks_snapshot(self, db_session):
        from app.modules.options_data.models import Ticker, OptionsContract
        from app.modules.pricing.models import GreeksSnapshot
        from datetime import date, datetime, timezone
        import uuid

        ticker = Ticker(symbol="TEST", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        contract = OptionsContract(
            ticker_id=ticker.id, occ_symbol="TEST250321C100",
            expiration_date=date(2025, 3, 21), strike=100, option_type="call",
        )
        db_session.add(contract)
        await db_session.flush()

        snap = GreeksSnapshot(
            contract_id=contract.id,
            timestamp=datetime.now(timezone.utc),
            source="calculated",
            spot_price=100.0,
            time_to_expiry=0.25,
            delta=0.54, gamma=0.03, theta=-0.05, vega=0.15, rho=0.02,
            theoretical_price=5.20,
        )
        db_session.add(snap)
        await db_session.flush()

        assert snap.id is not None
        assert snap.source == "calculated"
