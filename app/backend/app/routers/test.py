from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_admin
from app.connectors.plex import PlexConnector
from app.connectors.tautulli import TautulliConnector
from app.connectors.tmdb import TMDBConnector
from app.connectors.sonarr import SonarrConnector
from app.connectors.radarr import RadarrConnector

router = APIRouter(
    prefix="/test",
    tags=["test"],
    dependencies=[Depends(get_current_admin)],
)


async def _test_connector(name, connector, test_method):
    try:
        ok = await getattr(connector, test_method)()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{name} connection failed: {exc}",
        ) from exc

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{name} did not respond or returned an invalid status.",
        )

    return {"name": name, "ok": True, "message": "Connected"}


@router.get("/plex")
async def test_plex():
    return await _test_connector("Plex", PlexConnector(), "test_connection")


@router.get("/tautulli")
async def test_tautulli():
    return await _test_connector("Tautulli", TautulliConnector(), "test_connection")


@router.get("/tmdb")
async def test_tmdb():
    return await _test_connector("TMDB", TMDBConnector(), "test_connection")


@router.get("/sonarr")
async def test_sonarr():
    return await _test_connector("Sonarr", SonarrConnector(), "test_connection")


@router.get("/radarr")
async def test_radarr():
    return await _test_connector("Radarr", RadarrConnector(), "test_connection")
