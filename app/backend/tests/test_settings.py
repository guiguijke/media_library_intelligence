import pytest

from app.models import AppSetting
from app.services.settings import SETTING_KEYS


@pytest.mark.asyncio
async def test_get_settings_requires_auth(client):
    response = await client.get("/api/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_settings_with_auth(client, admin_token, async_session):
    for key, meta in SETTING_KEYS.items():
        async_session.add(
            AppSetting(
                key=key,
                value=meta["default"],
                is_secret=meta["secret"],
                description=meta["desc"],
            )
        )
    await async_session.commit()

    response = await client.get(
        "/api/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(SETTING_KEYS)


@pytest.mark.asyncio
async def test_get_settings_masks_secrets(client, admin_token, async_session):
    async_session.add(
        AppSetting(
            key="PLEX_TOKEN",
            value="super-secret-token",
            is_secret=True,
            description="Plex token",
        )
    )
    await async_session.commit()

    response = await client.get(
        "/api/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    by_key = {item["key"]: item["value"] for item in response.json()}
    assert by_key["PLEX_TOKEN"] == "****"


@pytest.mark.asyncio
async def test_put_settings_requires_admin(client):
    response = await client.put("/api/settings", json={"PLEX_TOKEN": "new-token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_settings_unknown_key(client, admin_token):
    response = await client.put(
        "/api/settings",
        json={"UNKNOWN_SETTING_KEY": "value"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_put_settings_updates_value(client, admin_token, async_session):
    async_session.add(
        AppSetting(
            key="PLEX_BASE_URL",
            value="http://old-plex:32400",
            is_secret=False,
            description="Plex server URL",
        )
    )
    await async_session.commit()

    response = await client.put(
        "/api/settings",
        json={"PLEX_BASE_URL": "http://new-plex:32400"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    row = await async_session.get(AppSetting, 1)
    # The first seeded setting gets id=1 on SQLite.
    assert row.value == "http://new-plex:32400"
