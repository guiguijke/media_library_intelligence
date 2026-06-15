import pytest

from app.models import ExternalClassics, CategoryEnum


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    response = await client.get("/api/search?q=inception")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_authorized_empty(client, admin_token):
    response = await client.get(
        "/api/search?q=inception",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_finds_item(client, admin_token, async_session):
    async_session.add(
        ExternalClassics(
            title="Inception",
            original_title="Inception",
            year=2010,
            category=CategoryEnum.movie,
            tmdb_id=27205,
            source_api="tmdb",
            score_external=8.3,
            popularity=100.0,
        )
    )
    await async_session.commit()

    response = await client.get(
        "/api/search?q=incep",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Inception"
    assert data["items"][0]["category"] == "movie"
    assert data["items"][0]["is_owned"] is False


@pytest.mark.asyncio
async def test_search_filters_by_category(client, admin_token, async_session):
    async_session.add(
        ExternalClassics(
            title="Inception",
            year=2010,
            category=CategoryEnum.movie,
            source_api="tmdb",
        )
    )
    async_session.add(
        ExternalClassics(
            title="Breaking Bad",
            year=2008,
            category=CategoryEnum.series,
            source_api="tmdb",
        )
    )
    await async_session.commit()

    response = await client.get(
        "/api/search?q=&category=series",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "series"
