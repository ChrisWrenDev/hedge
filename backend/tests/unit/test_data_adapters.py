import pytest
from datetime import date, datetime, timezone

from app.modules.data_sources.base import NormalizedContract, NormalizedSnapshot, NormalizedUnderlyingBar, OptionType
from app.modules.data_sources.cboe import _parse_occ, _safe_float, _safe_int
from app.modules.data_sources.polygon import PolygonAdapter
from app.modules.data_sources.yahoo import YahooAdapter, _safe_float as yf_safe_float, _safe_int as yf_safe_int


# ── CBOE OCC Parser ──────────────────────────────────────────

class TestCBOEOccParser:
    def test_parse_call(self):
        result = _parse_occ("SPY 2025-03-21 580.00 C")
        assert result is not None
        exp_date, strike, opt_type = result
        assert exp_date == date(2025, 3, 21)
        assert strike == 580.0
        assert opt_type == OptionType.CALL

    def test_parse_put(self):
        result = _parse_occ("AAPL 2025-06-20 190.50 P")
        assert result is not None
        exp_date, strike, opt_type = result
        assert exp_date == date(2025, 6, 20)
        assert strike == 190.5
        assert opt_type == OptionType.PUT

    def test_parse_invalid_format(self):
        assert _parse_occ("invalid") is None
        assert _parse_occ("") is None
        assert _parse_occ("SPY 2025-13-01 100 C") is None  # invalid month


# ── Safe Float/Int Helpers ────────────────────────────────────

class TestSafeFloatConversion:
    def test_normal_float(self):
        assert _safe_float(3.14) == 3.14

    def test_none(self):
        assert _safe_float(None) is None

    def test_string_number(self):
        assert _safe_float("2.5") == 2.5

    def test_nan_returns_none(self):
        import math
        assert _safe_float(float("nan")) is None

    def test_invalid_string(self):
        assert _safe_float("abc") is None


class TestSafeIntConversion:
    def test_normal_int(self):
        assert _safe_int(42) == 42

    def test_none(self):
        assert _safe_int(None) is None

    def test_float_truncated(self):
        assert _safe_int(3.9) == 3

    def test_invalid_string(self):
        assert _safe_int("abc") is None


# ── Normalized Dataclass Construction ─────────────────────────

class TestNormalizedDataclasses:
    def test_normalized_contract_defaults(self):
        c = NormalizedContract(
            occ_symbol="TEST250321C100",
            underlying_symbol="TEST",
            expiration_date=date(2025, 3, 21),
            strike=100.0,
            option_type=OptionType.CALL,
        )
        assert c.multiplier == 100
        assert c.active is True

    def test_normalized_snapshot_defaults(self):
        s = NormalizedSnapshot(
            occ_symbol="TEST250321C100",
            underlying_symbol="TEST",
            timestamp=datetime.now(timezone.utc),
        )
        assert s.bid is None
        assert s.delta is None
        assert s.volume is None

    def test_normalized_underlying_bar(self):
        b = NormalizedUnderlyingBar(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            interval="1d",
            open=185.0, high=187.0, low=184.0, close=186.5,
            volume=50_000_000,
        )
        assert b.close == 186.5
        assert b.volume == 50_000_000


# ── Polygon Adapter (unit, mocked HTTP) ────────────────────────

class TestPolygonAdapter:
    def test_no_api_key_returns_empty(self):
        adapter = PolygonAdapter()
        adapter.api_key = ""
        import asyncio
        assert asyncio.get_event_loop().run_until_complete(
            adapter.fetch_options_chain("AAPL")
        ) == []

    def test_health_check_no_key(self):
        adapter = PolygonAdapter()
        adapter.api_key = ""
        import asyncio
        assert asyncio.get_event_loop().run_until_complete(
            adapter.health_check()
        ) is False


# ── Yahoo Adapter (unit, mocked) ───────────────────────────────

class TestYahooAdapter:
    def test_safe_float_yf(self):
        assert yf_safe_float(None) is None
        assert yf_safe_float(1.5) == 1.5
        assert yf_safe_float("abc") is None

    def test_safe_int_yf(self):
        assert yf_safe_int(None) is None
        assert yf_safe_int(42) == 42
        assert yf_safe_int("abc") is None
