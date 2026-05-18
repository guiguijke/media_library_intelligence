from fastapi import APIRouter
from app.connectors.plex import PlexConnector
from app.connectors.tautulli import TautulliConnector
from app.connectors.tmdb import TMDBConnector
from app.connectors.sonarr import SonarrConnector
from app.connectors.radarr import RadarrConnector

router = APIRouter(prefix="/test", tags=["test"])


async def _test_connector(name, connector, test_method):
    try:
        ok = await getattr(connector, test_method)()
        return {"name": name, "ok": bool(ok), "message": "Connected" if ok else "No response"}
    except Exception as exc:
        return {"name": name, "ok": False, "message": str(exc)}


@router.get("/plex")
async def test_plex():
    return await _test_connector("Plex", PlexConnector(), "test_connection")


@router.get("/tautulli")
async def test_tautulli():
    return await _test_connector("Tautulli", TautulliConnector(), "test_connection")


@router.get("/tautulli/raw")
async def test_tautulli_raw():
    connector = TautulliConnector()
    try:
        raw = await connector._request("get_activity")
        return {"ok": True, "raw": raw}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.get("/tmdb")
async def test_tmdb():
    return await _test_connector("TMDB", TMDBConnector(), "test_connection")


@router.get("/sonarr")
async def test_sonarr():
    return await _test_connector("Sonarr", SonarrConnector(), "test_connection")


@router.get("/radarr")
async def test_radarr():
    return await _test_connector("Radarr", RadarrConnector(), "test_connection")
