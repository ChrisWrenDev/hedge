from datetime import datetime, timezone

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scenarios.engine import run_price_shock, run_vol_shock, run_time_decay, run_combined
from app.modules.scenarios.models import ScenarioRun, ScenarioTemplate


async def run_scenario(
    db: AsyncSession, template_id: uuid.UUID
) -> ScenarioRun | None:
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        return None

    run = ScenarioRun(
        template_id=template_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    params = template.parameters or {}
    scenario_type = params.get("type", "price_shock")

    try:
        if scenario_type == "price_shock":
            shocks = params.get("shocks", [])
            results_list = []
            for s in shocks:
                r = run_price_shock(
                    spot=params["spot"], shock=s, iv=params["iv"],
                    strike=params["strike"], rate=params["rate"],
                    time_to_expiry=params["time_to_expiry"],
                    option_type=params["option_type"],
                    quantity=params.get("quantity", 1),
                )
                results_list.append(r)
            run.results = {"type": scenario_type, "scenarios": results_list}

        elif scenario_type == "vol_shock":
            shocks = params.get("vol_shocks", [])
            results_list = []
            for s in shocks:
                r = run_vol_shock(
                    spot=params["spot"], strike=params["strike"],
                    rate=params["rate"], time_to_expiry=params["time_to_expiry"],
                    iv=params["iv"], vol_shock=s,
                    option_type=params["option_type"],
                    quantity=params.get("quantity", 1),
                )
                results_list.append(r)
            run.results = {"type": scenario_type, "scenarios": results_list}

        elif scenario_type == "time_decay":
            days = params.get("time_decay_days", [])
            results_list = []
            for d in days:
                r = run_time_decay(
                    spot=params["spot"], strike=params["strike"],
                    rate=params["rate"], time_to_expiry=params["time_to_expiry"],
                    iv=params["iv"], decay_days=d,
                    option_type=params["option_type"],
                    quantity=params.get("quantity", 1),
                )
                results_list.append(r)
            run.results = {"type": scenario_type, "scenarios": results_list}

        elif scenario_type == "combined":
            r = run_combined(
                spot=params["spot"], strike=params["strike"],
                rate=params["rate"], time_to_expiry=params["time_to_expiry"],
                iv=params["iv"],
                price_shock=params.get("price_shock", 0),
                vol_shock=params.get("vol_shock", 0),
                decay_days=params.get("decay_days", 0),
                option_type=params["option_type"],
                quantity=params.get("quantity", 1),
            )
            run.results = {"type": scenario_type, "scenarios": [r]}

        run.status = "complete"
    except Exception as e:
        run.status = "failed"
        run.results = {"error": str(e)}

    run.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(run)
    return run
