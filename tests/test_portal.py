from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core.config import get_settings


async def _login_driver(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/auth/apple", json={"identity_token": "portal-driver@example.com"})
    assert response.status_code == 200, response.text
    payload = response.json()
    return {
        "access_token": payload["access_token"],
        "driver_id": payload["driver"]["driver_id"],
    }


@pytest.mark.asyncio
async def test_portal_dashboard_trip_detail_and_media(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setenv("PORTAL_ADMIN_PASSWORD", "portal-pass")
    get_settings.cache_clear()

    session = await _login_driver(client)
    auth = {"Authorization": f"Bearer {session['access_token']}"}
    started_at = datetime(2026, 4, 22, 9, 15, tzinfo=UTC)

    start_trip = await client.post(
        "/trips/start",
        headers=auth,
        json={
            "started_at": started_at.isoformat(),
            "start_location": {
                "latitude": 49.2827,
                "longitude": -123.1207,
                "horizontal_accuracy": 7.0,
            },
        },
    )
    assert start_trip.status_code == 200, start_trip.text
    trip_id = start_trip.json()["trip_id"]

    points = await client.post(
        f"/trips/{trip_id}/points",
        headers=auth,
        json={
            "batch_id": "portal-batch-1",
            "points": [
                {
                    "timestamp": (started_at + timedelta(minutes=2)).isoformat(),
                    "latitude": 49.2830,
                    "longitude": -123.1210,
                    "horizontal_accuracy": 6.5,
                    "speed_mps": 12.2,
                },
                {
                    "timestamp": (started_at + timedelta(minutes=5)).isoformat(),
                    "latitude": 49.2841,
                    "longitude": -123.1224,
                    "horizontal_accuracy": 6.0,
                    "speed_mps": 10.8,
                },
            ],
        },
    )
    assert points.status_code == 200, points.text

    upload = await client.post(
        "/media/upload-url",
        headers=auth,
        json={"kind": "sticker_photo", "content_type": "image/jpeg", "file_name": "sticker.jpg"},
    )
    assert upload.status_code == 200, upload.text
    storage_key = upload.json()["storage_key"]

    raw_image = b"\xff\xd8\xffdbfake-jpeg"
    upload_blob = await client.put(f"/v1/media/dev-upload/{storage_key}", content=raw_image)
    assert upload_blob.status_code == 204, upload_blob.text

    submission = await client.post(
        "/submissions/sticker",
        headers=auth,
        json={
            "storage_key": storage_key,
            "taken_at": (started_at + timedelta(minutes=8)).isoformat(),
            "trip_id": trip_id,
        },
    )
    assert submission.status_code == 200, submission.text
    submission_id = submission.json()["id"]

    unauthorized = await client.get("/portal/api/dashboard")
    assert unauthorized.status_code == 401

    login = await client.post("/portal/login", json={"password": "portal-pass"})
    assert login.status_code == 200, login.text
    assert login.json()["authenticated"] is True

    dashboard = await client.get("/portal/api/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    dashboard_payload = dashboard.json()
    assert dashboard_payload["trips"][0]["trip_id"] == trip_id
    assert dashboard_payload["recent_photos"][0]["submission_id"] == submission_id
    assert dashboard_payload["recent_photos"][0]["image_url"] == f"/portal/media/sticker/{submission_id}"

    detail = await client.get(f"/portal/api/trips/{trip_id}")
    assert detail.status_code == 200, detail.text
    detail_payload = detail.json()
    assert detail_payload["trip"]["sticker_submission_count"] == 1
    assert len(detail_payload["points"]) == 2
    assert detail_payload["photos"][0]["submission_id"] == submission_id

    media = await client.get(f"/portal/media/sticker/{submission_id}")
    assert media.status_code == 200, media.text
    assert media.content == raw_image

    logout = await client.post("/portal/logout")
    assert logout.status_code == 204, logout.text
    assert (await client.get("/portal/api/dashboard")).status_code == 401

    get_settings.cache_clear()
