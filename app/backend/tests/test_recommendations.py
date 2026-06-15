import pytest

from app.models import ExternalClassics, CategoryEnum


@pytest.mark.asyncio
async def test_recommendations_requires_auth(client):
    response = await client.get("/api/recommendations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_recommendations_authorized(client, admin_token):
    response = await client.get(
        "/api/recommendations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_recommendations_post_authorized(client, admin_token):
    response = await client.post(
        "/api/recommendations",
        json={"limit": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_recommendations_pagination_offset(client, admin_token, async_session):
    for i in range(5):
        async_session.add(
            ExternalClassics(
                title=f"Movie {i}",
                year=2020,
                category=CategoryEnum.movie,
                tmdb_id=1000 + i,
                source_api="tmdb",
                popularity=1000.0,
                is_recommended=True,
            )
        )
    await async_session.commit()

    response = await client.get(
        "/api/recommendations?limit=2&offset=0",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["offset"] == 0

    response = await client.get(
        "/api/recommendations?limit=2&offset=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["offset"] == 2
    assert data["items"][0]["title"] == "Movie 2"
