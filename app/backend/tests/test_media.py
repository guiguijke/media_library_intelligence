import pytest

from app.models import ExternalClassics, CategoryEnum


@pytest.mark.asyncio
async def test_media_detail_requires_auth(client):
    response = await client.get("/api/media/tmdb-1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_detail_not_found(client, admin_token):
    response = await client.get(
        "/api/media/tmdb-999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_media_detail_finds_by_tmdb(client, admin_token, async_session):
    async_session.add(
        ExternalClassics(
            title="Inception",
            year=2010,
            category=CategoryEnum.movie,
            tmdb_id=27205,
            source_api="tmdb",
        )
    )
    await async_session.commit()

    response = await client.get(
        "/api/media/tmdb-27205",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Inception"
    assert data["category"] == "movie"
    assert data["tmdb_id"] == 27205


@pytest.mark.asyncio
async def test_media_detail_finds_by_anilist(client, admin_token, async_session):
    async_session.add(
        ExternalClassics(
            title="Attack on Titan",
            year=2013,
            category=CategoryEnum.anime,
            anilist_id=16498,
            source_api="anilist",
        )
    )
    await async_session.commit()

    response = await client.get(
        "/api/media/anilist-16498",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Attack on Titan"
    assert data["category"] == "anime"
