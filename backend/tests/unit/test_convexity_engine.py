import pytest
from datetime import date


class TestConvexityScore:
    """Test convexity scoring formula."""

    def test_score_range_zero_to_hundred(self):
        from app.modules.convexity.engine import compute_score
        score = compute_score(
            gamma_per_theta=4.0,
            vega_normalized=0.02,
            iv_rank=35,
            volume_oi_ratio=0.15,
            dte=45,
        )
        assert 0 <= score <= 100

    def test_higher_gamma_per_theta_increases_score(self):
        from app.modules.convexity.engine import compute_score
        low = compute_score(gamma_per_theta=1.0, vega_normalized=0.01, iv_rank=50, volume_oi_ratio=0.1, dte=30)
        high = compute_score(gamma_per_theta=5.0, vega_normalized=0.01, iv_rank=50, volume_oi_ratio=0.1, dte=30)
        assert high > low

    def test_lower_iv_rank_increases_score(self):
        from app.modules.convexity.engine import compute_score
        high_iv = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=80, volume_oi_ratio=0.1, dte=30)
        low_iv = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=20, volume_oi_ratio=0.1, dte=30)
        assert low_iv > high_iv

    def test_higher_volume_oi_increases_score(self):
        from app.modules.convexity.engine import compute_score
        low_liq = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=50, volume_oi_ratio=0.05, dte=30)
        high_liq = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=50, volume_oi_ratio=0.3, dte=30)
        assert high_liq > low_liq

    def test_optimal_dte_window(self):
        """Options with 30-60 DTE should score higher than very short or very long."""
        from app.modules.convexity.engine import compute_score
        short_dte = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=50, volume_oi_ratio=0.1, dte=7)
        optimal_dte = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=50, volume_oi_ratio=0.1, dte=45)
        long_dte = compute_score(gamma_per_theta=3.0, vega_normalized=0.02, iv_rank=50, volume_oi_ratio=0.1, dte=180)
        assert optimal_dte >= short_dte
        assert optimal_dte >= long_dte

    def test_score_with_zero_gamma_per_theta(self):
        from app.modules.convexity.engine import compute_score
        score = compute_score(gamma_per_theta=0.0, vega_normalized=0.01, iv_rank=50, volume_oi_ratio=0.1, dte=30)
        assert score >= 0  # Should not crash, just score low


class TestConvexityRanking:
    """Test ranking of options by convexity score."""

    def test_ranking_orders_by_score_desc(self):
        from app.modules.convexity.engine import rank_by_convexity
        options = [
            {"occ_symbol": "A", "score": 50},
            {"occ_symbol": "B", "score": 80},
            {"occ_symbol": "C", "score": 30},
        ]
        ranked = rank_by_convexity(options)
        assert ranked[0]["occ_symbol"] == "B"
        assert ranked[1]["occ_symbol"] == "A"
        assert ranked[2]["occ_symbol"] == "C"

    def test_ranking_empty_list(self):
        from app.modules.convexity.engine import rank_by_convexity
        assert rank_by_convexity([]) == []

    def test_ranking_adds_rank_field(self):
        from app.modules.convexity.engine import rank_by_convexity
        options = [{"occ_symbol": "A", "score": 50}, {"occ_symbol": "B", "score": 80}]
        ranked = rank_by_convexity(options)
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2


class TestConvexityScoreModel:
    """Test the ConvexityScore DB model."""

    @pytest.mark.asyncio
    async def test_create_convexity_score(self, db_session):
        from app.modules.options_data.models import Ticker, OptionsContract
        from app.modules.convexity.models import ConvexityScore
        from datetime import date

        ticker = Ticker(symbol="TEST", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        contract = OptionsContract(
            ticker_id=ticker.id, occ_symbol="TEST250321C100",
            expiration_date=date(2025, 3, 21), strike=100, option_type="call",
        )
        db_session.add(contract)
        await db_session.flush()

        score = ConvexityScore(
            contract_id=contract.id,
            score_date=date.today(),
            score=75.5,
            gamma_per_theta=4.2,
            vega_normalized=0.02,
            iv_rank=35.0,
            iv_percentile=40.0,
        )
        db_session.add(score)
        await db_session.flush()

        assert score.id is not None
        assert score.score == 75.5

    @pytest.mark.asyncio
    async def test_get_top_scores(self, db_session):
        from app.modules.options_data.models import Ticker, OptionsContract
        from app.modules.convexity.models import ConvexityScore
        from app.modules.convexity.service import get_top_convexity_scores
        from datetime import date

        ticker = Ticker(symbol="TEST", type="equity")
        db_session.add(ticker)
        await db_session.flush()

        for i, (occ, sc) in enumerate([
            ("TEST250321C90", 40.0), ("TEST250321C100", 80.0), ("TEST250321C110", 60.0)
        ]):
            contract = OptionsContract(
                ticker_id=ticker.id, occ_symbol=occ,
                expiration_date=date(2025, 3, 21), strike=90 + i * 10, option_type="call",
            )
            db_session.add(contract)
            await db_session.flush()

            score = ConvexityScore(
                contract_id=contract.id,
                score_date=date.today(),
                score=sc,
                gamma_per_theta=3.0,
                vega_normalized=0.02,
                iv_rank=40.0,
                iv_percentile=45.0,
            )
            db_session.add(score)
        await db_session.commit()

        top = await get_top_convexity_scores(db_session, date.today(), limit=2)
        assert len(top) == 2
        assert top[0].score == 80.0
        assert top[1].score == 60.0
