"""
End-to-end integration test — user flows.

Flow:
  01. POST /auth/signup                     → crear usuario
  02. POST /auth/login                      → obtener JWT
  03. Decode JWT                            → extraer user_id
  04. GET  /auth/me                         → perfil del usuario
  05. PATCH /auth/me (nombre)               → actualizar nombre
  06. PATCH /auth/me (contraseña)           → cambiar contraseña
  07. POST /auth/login (nueva contraseña)   → verificar nueva contraseña
  08. POST /auth/refresh                    → renovar access token
  09. POST /auth/logout                     → cerrar sesión
  10. GET  /auth/me (token revocado)        → espera 401
  11. POST /auth/login (contraseña nueva)   → re-login para continuar
  12. POST /devices/register                → registrar dispositivo
  13. GET  /devices/me                      → esperar que aparezca el dispositivo
  14. PUT  /devices/update                  → actualizar dispositivo
  15. POST /registers/received  ×5          → enviar telemetría
  16. GET  /registers/{device_id}           → esperar registros almacenados
  17. GET  /registers/{device_id}/by-date   → filtrar por fecha
  18. POST /reports/{device_id}/generate   → generar reporte
  19. GET  /reports/{device_id}             → esperar reporte
  20. GET  /reports/{device_id}/by-date     → filtrar reportes por fecha
  21. GET  /notifications/device/{device_id}→ notificaciones del dispositivo
  22. GET  /notifications/me                → mis notificaciones

Prerequisites:
  - All services running via docker compose (api-gateway on localhost:8000)
  - pip install requests pytest
"""

import base64
import json
import time
import uuid
from time import sleep
from datetime import datetime, timezone, timedelta

import pytest
import requests

BASE_URL = "http://localhost:8000"
POLL_TIMEOUT = 20  # seconds
POLL_INTERVAL = 1  # seconds between polls


# ── helpers ───────────────────────────────────────────────────────────────────


def _decode_jwt_payload(token: str) -> dict:
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _auth_refresh_headers(token: str, refresh_token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "X-Refresh-Token": refresh_token,
    }


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def unique_user() -> dict:
    suffix = uuid.uuid4().hex[:8]
    return {
        "name": f"Test User {suffix}",
        "email": f"testuser_{suffix}@ioteur-test.com",
        "password": "TestPass123!",
    }


# ── tests ─────────────────────────────────────────────────────────────────────


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
    assert "refresh_token" in body, f"No refresh_token in response: {body}"
    unique_user["access_token"] = body["access_token"]
    unique_user["refresh_token"] = body["refresh_token"]
    print(f"     access_token (first 40 chars): {body['access_token'][:40]}…")


def test_03_decode_jwt(unique_user):
    token = unique_user.get("access_token")
    assert token, "No access_token from previous test"
    payload = _decode_jwt_payload(token)
    assert "sub" in payload, f"JWT payload missing 'sub': {payload}"
    unique_user["user_id"] = payload["sub"]
    print(f"\n[03] JWT payload: {payload}")
    print(f"     user_id (sub): {payload['sub']}")


def test_04_get_me(unique_user):
    token = unique_user.get("access_token")
    assert token

    print("\n[04] GET /auth/me")
    resp = requests.get(
        f"{BASE_URL}/auth/me",
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"GET /auth/me failed: {resp.status_code} {resp.text}"
    )
    body = resp.json()
    assert "email" in body, f"Response missing email: {body}"
    assert body["email"] == unique_user["email"], f"Email mismatch: {body}"


def test_05_patch_me_name(unique_user):
    token = unique_user.get("access_token")
    assert token

    new_name = unique_user["name"] + " Patched"
    print(f"\n[05] PATCH /auth/me  name={new_name}")
    resp = requests.patch(
        f"{BASE_URL}/auth/me",
        json={"name": new_name},
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, f"PATCH name failed: {resp.status_code} {resp.text}"
    unique_user["name"] = new_name


def test_06_patch_me_password(unique_user):
    token = unique_user.get("access_token")
    assert token

    new_password = "NewTestPass456!"
    print("\n[06] PATCH /auth/me  change password")
    resp = requests.patch(
        f"{BASE_URL}/auth/me",
        json={
            "old_password": unique_user["password"],
            "new_password": new_password,
        },
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"PATCH password failed: {resp.status_code} {resp.text}"
    )
    unique_user["password"] = new_password


def test_07_login_new_password(unique_user):
    print("\n[07] POST /auth/login con nueva contraseña")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": unique_user["email"], "password": unique_user["password"]},
        timeout=10,
    )
    print(f"     → {resp.status_code}")
    assert resp.status_code == 200, (
        f"Login with new password failed: {resp.status_code} {resp.text}"
    )
    body = resp.json()
    unique_user["access_token"] = body["access_token"]
    unique_user["refresh_token"] = body["refresh_token"]


def test_08_refresh_token(unique_user):
    token = unique_user.get("access_token")
    refresh_token = unique_user.get("refresh_token")
    assert token and refresh_token

    print("\n[08] POST /auth/refresh")
    resp = requests.post(
        f"{BASE_URL}/auth/refresh",
        headers=_auth_refresh_headers(token, refresh_token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, f"Refresh failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert "access_token" in body, f"No access_token in refresh response: {body}"
    unique_user["access_token"] = body["access_token"]
    print(f"     new access_token (first 40 chars): {body['access_token'][:40]}…")


def test_09_logout(unique_user):
    token = unique_user.get("access_token")
    refresh_token = unique_user.get("refresh_token")
    assert token and refresh_token

    print("\n[09] POST /auth/logout")
    resp = requests.post(
        f"{BASE_URL}/auth/logout",
        headers=_auth_refresh_headers(token, refresh_token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, f"Logout failed: {resp.status_code} {resp.text}"
    unique_user["revoked_token"] = token


def test_10_me_after_logout(unique_user):
    revoked_token = unique_user.get("revoked_token")
    assert revoked_token, "No revoked token from logout test"

    print("\n[10] GET /auth/me con token revocado (espera 401)")
    resp = requests.get(
        f"{BASE_URL}/auth/me",
        headers=_auth_headers(revoked_token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 401, (
        f"Expected 401 after logout, got: {resp.status_code}"
    )


def test_11_relogin(unique_user):
    print("\n[11] POST /auth/login (re-login para continuar tests)")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": unique_user["email"], "password": unique_user["password"]},
        timeout=10,
    )
    print(f"     → {resp.status_code}")
    assert resp.status_code == 200, f"Re-login failed: {resp.status_code} {resp.text}"
    body = resp.json()
    unique_user["access_token"] = body["access_token"]
    unique_user["refresh_token"] = body["refresh_token"]


def test_12_register_device(unique_user):
    token = unique_user.get("access_token")
    assert token

    body = {
        "device_name": "sensor-e2e",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "report_interval": 60,
    }
    print(f"\n[12] POST /devices/register  body={body}")
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


def test_13_poll_device_appears(unique_user):
    token = unique_user.get("access_token")
    assert token

    print(f"\n[13] Polling GET /devices/me (timeout={POLL_TIMEOUT}s) …")
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
            if isinstance(data, list) and data:
                device_uuid = data[0].get("device_uuid")
            elif isinstance(data, dict) and data.get("device_uuid"):
                device_uuid = data["device_uuid"]
            if device_uuid:
                break
        time.sleep(POLL_INTERVAL)

    print(f"     device_uuid resolved: {device_uuid}")
    assert device_uuid, f"Device did not appear within {POLL_TIMEOUT}s"
    unique_user["device_uuid"] = device_uuid


def test_14_update_device(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    body = {
        "device_uuid": device_uuid,
        "device_name": "sensor-e2e-updated",
        "report_interval": 120,
    }
    print(f"\n[14] PUT /devices/update  body={body}")
    resp = requests.put(
        f"{BASE_URL}/devices/update",
        json=body,
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 202, (
        f"Device update failed: {resp.status_code} {resp.text}"
    )


def test_15_send_registers(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    unique_user["register_time_from"] = datetime.now(timezone.utc)

    print(f"\n[15] Enviando 5 registros de telemetría para device_uuid={device_uuid}")
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


def test_16_poll_registers_stored(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    print(f"\n[16] Polling GET /registers/{device_uuid} (timeout={POLL_TIMEOUT}s) …")
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

    print(f"     total records: {len(records)}")
    assert len(records) >= 5, (
        f"Expected ≥5 records, got {len(records)} after {POLL_TIMEOUT}s"
    )
    first = records[0]
    assert "device_id" in first
    assert "values" in first
    assert "time_procesing" in first


def test_17_get_registers_by_date(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    time_from = unique_user.get("register_time_from")
    assert token and device_uuid and time_from

    time_to = datetime.now(timezone.utc) + timedelta(minutes=1)
    print(
        f"\n[17] GET /registers/{device_uuid}/by-date  from={time_from.isoformat()}  to={time_to.isoformat()}"
    )
    resp = requests.get(
        f"{BASE_URL}/registers/{device_uuid}/by-date",
        headers=_auth_headers(token),
        params={
            "from": time_from.isoformat(),
            "to": time_to.isoformat(),
            "limit": 10,
        },
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"GET registers by-date failed: {resp.status_code} {resp.text}"
    )
    records = resp.json()
    assert isinstance(records, list), f"Expected list, got: {type(records)}"
    print(f"     records in range: {len(records)}")


def test_18_generate_report(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    unique_user["report_time_from"] = datetime.now(timezone.utc)

    print(f"\n[18] POST /reports/{device_uuid}/generate")
    resp = requests.post(
        f"{BASE_URL}/reports/{device_uuid}/generate",
        headers=_auth_headers(token),
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 202, (
        f"Generate report failed: {resp.status_code} {resp.text}"
    )


def test_19_poll_reports_stored(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    print(f"\n[19] Polling GET /reports/{device_uuid} (timeout={POLL_TIMEOUT}s) …")
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
        f"Expected ≥1 report after {POLL_TIMEOUT}s, got {len(reports)}"
    )
    first = reports[0]
    assert first.get("device_id") or first.get("deviceId"), (
        f"Report missing device_id: {first}"
    )
    assert "metric_data" in first or "metricData" in first, (
        f"Report missing metric_data: {first}"
    )


def test_20_get_reports_by_date(unique_user):
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    time_from = unique_user.get("report_time_from")
    assert token and device_uuid and time_from

    time_to = datetime.now(timezone.utc) + timedelta(minutes=1)
    print(
        f"\n[20] GET /reports/{device_uuid}/by-date  from={time_from.isoformat()}  to={time_to.isoformat()}"
    )
    resp = requests.get(
        f"{BASE_URL}/reports/{device_uuid}/by-date",
        headers=_auth_headers(token),
        params={
            "from": time_from.isoformat(),
            "to": time_to.isoformat(),
            "limit": 10,
        },
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"GET reports by-date failed: {resp.status_code} {resp.text}"
    )
    reports = resp.json()
    assert isinstance(reports, list), f"Expected list, got: {type(reports)}"
    print(f"     reports in range: {len(reports)}")


def test_21_get_notifications_by_device(unique_user):
    sleep(120)
    token = unique_user.get("access_token")
    device_uuid = unique_user.get("device_uuid")
    assert token and device_uuid

    print(f"\n[21] GET /notifications/device/{device_uuid}")
    resp = requests.get(
        f"{BASE_URL}/notifications/device/{device_uuid}",
        headers=_auth_headers(token),
        params={"limit": 10},
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"GET notifications by device failed: {resp.status_code} {resp.text}"
    )
    notifications = resp.json()
    assert isinstance(notifications, list), f"Expected list, got: {type(notifications)}"
    print(f"     notifications count: {len(notifications)}")


def test_22_get_my_notifications(unique_user):
    token = unique_user.get("access_token")
    assert token

    print("\n[22] GET /notifications/me")
    resp = requests.get(
        f"{BASE_URL}/notifications/me",
        headers=_auth_headers(token),
        params={"limit": 10},
        timeout=10,
    )
    print(f"     → {resp.status_code} {resp.text}")
    assert resp.status_code == 200, (
        f"GET /notifications/me failed: {resp.status_code} {resp.text}"
    )
    notifications = resp.json()
    assert isinstance(notifications, list), f"Expected list, got: {type(notifications)}"
    print(f"     notifications count: {len(notifications)}")
