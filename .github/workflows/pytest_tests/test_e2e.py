"""
End-to-end integration test.

Flow:
  1. Create a new user (POST /auth/signup)
  2. Log in (POST /auth/login)        → get JWT
  3. Decode JWT payload               → extract user_id
  4. Register a device (async)        → POST /devices/register
  5. Poll GET /devices/{user_id}      → wait until device appears
  6. Send 5 telemetry registers       → POST /registers/received
  7. Poll GET /registers/{device_id}  → wait until records are stored
  8. Get telemetry reports            → GET /reports/{device_id}  (200, may be empty)

Prerequisites:
  - All services running via docker compose (api-gateway on localhost:8000)
  - pip install requests pytest
"""

import base64
import json
import time
import uuid

import pytest
import requests

BASE_URL = "http://localhost:8000"
POLL_TIMEOUT = 20  # seconds to wait for async ops
POLL_INTERVAL = 1  # seconds between polls


# ── helpers ──────────────────────────────────────────────────────────────────


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification."""
    payload_b64 = token.split(".")[1]
    # restore padding
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def unique_user() -> dict:
    """Return unique credentials for this test run."""
    suffix = uuid.uuid4().hex[:8]
    return {
        "name": f"Test User {suffix}",
        "email": f"testuser_{suffix}@ioteur-test.com",
        "password": "TestPass123!",
    }


# ── test steps ───────────────────────────────────────────────────────────────


def test_01_signup(unique_user):
    print(f"\n[01] POST /auth/signup  email={unique_user['email']}")
    resp = requests.post(f"{BASE_URL}/auth/signup", json=unique_user, timeout=10)
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 201, f"Signup failed: {resp.status_code} {resp.text}"


def test_02_login(unique_user):
    print(f"\n[02] POST /auth/login  email={unique_user['email']}")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": unique_user["email"], "password": unique_user["password"]},
        timeout=10,
    )
    print(f"     → {resp.status_code}")
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert "access_token" in body, f"No access_token in response: {body}"
    unique_user["access_token"] = body["access_token"]
    print(f"     access_token (first 40 chars): {body['access_token'][:40]}…")


def test_03_decode_jwt(unique_user):
    token = unique_user.get("access_token")
    assert token, "No access_token from previous test"
    payload = _decode_jwt_payload(token)
    assert "sub" in payload, f"JWT payload missing 'sub': {payload}"
    unique_user["user_id"] = payload["sub"]
    print(f"\n[03] JWT payload: {payload}")
    print(f"     user_id (sub): {payload['sub']}")


def test_04_register_device(unique_user):
    token = unique_user.get("access_token")
    user_id = unique_user.get("user_id")
    assert token and user_id

    body = {
        "device_name": "sensor-e2e",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "report_interval": 60,
    }
    print(f"\n[04] POST /devices/register  body={body}")
    resp = requests.post(
        f"{BASE_URL}/devices/register",
        json=body,
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 202, (
        f"Device register failed: {resp.status_code} {resp.text}"
    )


def test_05_poll_device_appears(unique_user):
    """Wait until device-service has processed the async registration."""
    token = unique_user.get("access_token")
    assert token

    print(f"\n[05] Polling GET /devices/me (timeout={POLL_TIMEOUT}s) …")
    deadline = time.time() + POLL_TIMEOUT
    attempt = 0
    device_uuid = None
    while time.time() < deadline:
        attempt += 1
        resp = requests.get(
            f"{BASE_URL}/devices/me",
            headers=_auth_headers(token),
            timeout=10,
        )
        print(f"     attempt {attempt}: {resp.status_code} {resp.text}")
        if resp.status_code == 200:
            data = resp.json()
            # endpoint may return a single object or a list
            if isinstance(data, list) and data:
                device_uuid = data[0].get("device_uuid")
            elif isinstance(data, dict) and data.get("device_uuid"):
                device_uuid = data["device_uuid"]
            if device_uuid:
                break
        time.sleep(POLL_INTERVAL)

    print(f"     device_uuid resolved: {device_uuid}")
    assert device_uuid, (
        f"Device did not appear in device-service within {POLL_TIMEOUT}s"
    )
    unique_user["device_uuid"] = device_uuid


def test_06_send_registers(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    print(f"\n[06] Sending 5 telemetry registers for device_uuid={device_uuid}")
    for i in range(5):
        body = {
            "device_id": device_uuid,
            "time_procesing": 10 + i,
            "values": {
                "temperature": str(20.0 + i * 0.5),
                "humidity": str(60 + i),
            },
        }
        resp = requests.post(
            f"{BASE_URL}/registers/received",
            json=body,
            headers=_auth_headers(token),
            timeout=10,
        )
        print(f"     register #{i + 1}: {resp.status_code} {resp.text}")
        assert resp.status_code == 202, (
            f"Register #{i + 1} failed: {resp.status_code} {resp.text}"
        )


def test_07_poll_registers_stored(unique_user):
    """Wait until register-service has stored all 5 records in MongoDB."""
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    print(f"\n[07] Polling GET /registers/{device_uuid} (timeout={POLL_TIMEOUT}s) …")
    deadline = time.time() + POLL_TIMEOUT
    attempt = 0
    records = []
    while time.time() < deadline:
        attempt += 1
        resp = requests.get(
            f"{BASE_URL}/registers/{device_uuid}",
            headers=_auth_headers(token),
            params={"limit": 10},
            timeout=10,
        )
        records = resp.json() if resp.status_code == 200 else []
        count = len(records) if isinstance(records, list) else "n/a"
        print(f"     attempt {attempt}: {resp.status_code}  records={count}")
        assert resp.status_code == 200, (
            f"GET registers failed: {resp.status_code} {resp.text}"
        )
        if isinstance(records, list) and len(records) >= 5:
            break
        time.sleep(POLL_INTERVAL)

    print(f"     final record count: {len(records)}")
    assert len(records) >= 5, (
        f"Expected at least 5 register records, got {len(records)} "
        f"after {POLL_TIMEOUT}s"
    )
    # basic shape check
    first = records[0]
    assert "device_id" in first
    assert "values" in first
    assert "time_procesing" in first


def test_08_get_telemetry_reports(unique_user):
    """Trigger report generation then poll until at least one report appears."""
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    # 1. Trigger report generation
    print(f"\n[08] POST /reports/{device_uuid}/generate")
    resp = requests.post(
        f"{BASE_URL}/reports/{device_uuid}/generate",
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 202, (
        f"Generate report failed: {resp.status_code} {resp.text}"
    )

    # 2. Poll until the report is stored
    print(f"     Polling GET /reports/{device_uuid} (timeout={POLL_TIMEOUT}s) …")
    deadline = time.time() + POLL_TIMEOUT
    attempt = 0
    reports = []
    while time.time() < deadline:
        attempt += 1
        resp = requests.get(
            f"{BASE_URL}/reports/{device_uuid}",
            headers=_auth_headers(token),
            params={"limit": 10},
            timeout=10,
        )
        print(f"     attempt {attempt}: {resp.status_code} {resp.text}")
        assert resp.status_code == 200, (
            f"GET reports failed: {resp.status_code} {resp.text}"
        )
        reports = resp.json()
        if isinstance(reports, list) and reports:
            break
        time.sleep(POLL_INTERVAL)

    print(f"     reports count: {len(reports)}")
    assert len(reports) >= 1, (
        f"Expected at least 1 report after {POLL_TIMEOUT}s, got {len(reports)}"
    )
    first = reports[0]
    # support both Python-name and alias responses
    assert first.get("device_id") or first.get("deviceId"), (
        f"Report missing device_id: {first}"
    )
    assert "metric_data" in first or "metricData" in first, (
        f"Report missing metric_data: {first}"
    )
