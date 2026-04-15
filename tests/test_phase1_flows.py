from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/auth/apple", json={"identity_token": "driver@example.com"})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["driver"]["driver_id"].startswith("drv_")
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "driver_id": payload["driver"]["driver_id"],
    }


@pytest.mark.asyncio
async def test_auth_exchange_and_me(client: AsyncClient) -> None:
    session = await _login(client)
    response = await client.get(
        "/me",
        headers={"Authorization": f"Bearer {session['access_token']}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["driver_id"] == session["driver_id"]

    refresh = await client.post("/auth/refresh", json={"refresh_token": session["refresh_token"]})
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["access_token"]


@pytest.mark.asyncio
async def test_trip_start_points_and_end(client: AsyncClient) -> None:
    session = await _login(client)
    auth = {"Authorization": f"Bearer {session['access_token']}"}
    started_at = datetime(2026, 4, 11, 18, 30, tzinfo=UTC)

    start = await client.post(
        "/trips/start",
        headers=auth,
        json={
            "started_at": started_at.isoformat(),
            "device": {"platform": "ios", "app_version": "1.0.0", "os_version": "18.4"},
            "start_location": {
                "latitude": 49.2827,
                "longitude": -123.1207,
                "horizontal_accuracy": 8.0,
            },
        },
    )
    assert start.status_code == 200, start.text
    trip_id = start.json()["trip_id"]
    assert start.json()["status"] == "active"

    points = await client.post(
        f"/trips/{trip_id}/points",
        headers=auth,
        json={
            "batch_id": "batch-1",
            "points": [
                {
                    "timestamp": (started_at + timedelta(seconds=30)).isoformat(),
                    "latitude": 49.283,
                    "longitude": -123.121,
                    "horizontal_accuracy": 7.5,
                    "speed_mps": 11.2,
                    "course_degrees": 181.0,
                    "altitude_meters": 15.0,
                }
            ],
        },
    )
    assert points.status_code == 200, points.text
    assert points.json()["accepted_count"] == 1

    duplicate = await client.post(
        f"/trips/{trip_id}/points",
        headers=auth,
        json={
            "batch_id": "batch-1",
            "points": [
                {
                    "timestamp": (started_at + timedelta(seconds=30)).isoformat(),
                    "latitude": 49.283,
                    "longitude": -123.121,
                    "horizontal_accuracy": 7.5,
                }
            ],
        },
    )
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json()["accepted_count"] == 1

    end = await client.post(
        f"/trips/{trip_id}/end",
        headers=auth,
        json={
            "ended_at": (started_at + timedelta(minutes=30)).isoformat(),
            "device_distance_meters": 5230.2,
        },
    )
    assert end.status_code == 200, end.text
    assert end.json()["status"] == "completed"
    assert end.json()["summary"]["point_count"] == 1


@pytest.mark.asyncio
async def test_media_and_submission_flows(client: AsyncClient) -> None:
    session = await _login(client)
    auth = {"Authorization": f"Bearer {session['access_token']}"}

    upload = await client.post(
        "/media/upload-url",
        headers=auth,
        json={"kind": "sticker_photo", "content_type": "image/jpeg", "file_name": "photo.jpg"},
    )
    assert upload.status_code == 200, upload.text
    storage_key = upload.json()["storage_key"]
    assert storage_key.startswith(f"driver_uploads/{session['driver_id']}/sticker_photo/")

    taken_at = datetime(2026, 4, 11, 19, 0, tzinfo=UTC).isoformat()
    sticker = await client.post(
        "/sticker-verifications",
        headers=auth,
        json={
            "storage_key": storage_key,
            "taken_at": taken_at,
            "latitude": 49.0,
            "longitude": -123.0,
        },
    )
    assert sticker.status_code == 200, sticker.text
    assert sticker.json()["id"].startswith("stkr_")

    odometer_upload = await client.post(
        "/v1/media/upload-url",
        headers=auth,
        json={"kind": "odometer_photo", "content_type": "image/jpeg", "file_name": "odo.jpg"},
    )
    odometer = await client.post(
        "/v1/submissions/odometer",
        headers=auth,
        json={"storage_key": odometer_upload.json()["storage_key"], "taken_at": taken_at},
    )
    assert odometer.status_code == 200, odometer.text
    assert odometer.json()["id"].startswith("odo_")

