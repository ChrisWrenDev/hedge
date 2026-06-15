from fastapi import APIRouter

from app.modules.data_sources.base import BaseDataAdapter
from app.modules.data_sources.polygon import PolygonAdapter
from app.modules.data_sources.ibkr import IBKRAdapter
from app.modules.data_sources.yahoo import YahooAdapter
from app.modules.data_sources.cboe import CBOEAdapter

router = APIRouter(prefix="/data-sources", tags=["data-sources"])

_adapters: dict[str, BaseDataAdapter] = {
    "polygon": PolygonAdapter(),
    "ibkr": IBKRAdapter(),
    "yahoo": YahooAdapter(),
    "cboe": CBOEAdapter(),
}


@router.get("/")
async def list_sources():
    """List all registered data sources and their status."""
    results = []
    for name, adapter in _adapters.items():
        try:
            healthy = await adapter.health_check()
        except Exception:
            healthy = False
        results.append({"name": name, "healthy": healthy})
    return results


@router.get("/{source_name}/health")
async def source_health(source_name: str):
    """Check health of a specific data source."""
    adapter = _adapters.get(source_name)
    if not adapter:
        return {"error": f"Unknown source: {source_name}"}
    healthy = await adapter.health_check()
    return {"name": source_name, "healthy": healthy}
