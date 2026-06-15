import pytest

from app.models import Wishlist, CategoryEnum


@pytest.mark.asyncio
async def test_wishlist_requires_auth(client):
    response = await client.get("/api/queue/wishlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wishlist_list_empty(client, admin_token):
    response = await client.get(
        "/api/queue/wishlist",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_wishlist_send_to_radarr_requires_tmdb_id(client, admin_token, async_session):
    async_session.add(
        Wishlist(
            external_id="missing",
            category=CategoryEnum.movie,
            title="No ID",
            tmdb_id=None,
        )
    )
    await async_session.commit()

    response = await client.post(
        "/api/queue/wishlist/1/radarr",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_wishlist_send_to_sonarr_requires_id(client, admin_token, async_session):
    async_session.add(
        Wishlist(
            external_id="missing",
            category=CategoryEnum.series,
            title="No ID",
            tmdb_id=None,
            tvdb_id=None,
        )
    )
    await async_session.commit()

    response = await client.post(
        "/api/queue/wishlist/1/sonarr",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
