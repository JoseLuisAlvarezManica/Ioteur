
### CURL para confirmar que la api de node JS funcionaba
curl -X POST https://api.emailjs.com/api/v1.0/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "YOUR_SERVICE_ID",
    "template_id": "YOUR_TEMPLATE_ID",
    "user_id": "YOUR_PUBLIC_KEY",
    "accessToken": "YOUR_PRIVATE_KEY",
    "template_params": {
      "email": "your@email.com",
      "device_id": "test-device-123",
      "severity": "warning",
      "reason": "missed_intervals",
      "status": "unsent",
      "message": "3 consecutive heartbeats missed.",
      "created_at": "2026-05-13T22:00:00"
    }
  }'


### Evidencia de un correo generado con el CURL anterior

![Logo](./images/Evidence_EmailJS.png)
# Pruebas — Ioteur

---

## Estrategia de Pruebas

El proyecto cuenta con cuatro niveles de pruebas automatizadas ejecutadas a través de **GitHub Actions** sobre el entorno Docker Compose completo, más pruebas manuales realizadas con Postman:

| Nivel | Herramienta | Workflow |
|---|---|---|
| Calidad de código | Ruff (lint + format) | `ruff-check.yml` |
| Integración (curl) | Bash + cURL | `curl_endpoint_testing.yml` |
| Integración (pytest) | pytest + aio-pika + httpx + motor | `pytest_integration.yml` |
| E2E completo | pytest + requests | `pytest_e2e.yml` |
| Notificación EmailJS | pytest | `pytest_mailJS.yml` |
| Manual | Postman | `evidence/postman/` |

Todos los workflows de integración y E2E levantan el stack completo con `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`, inyectan credenciales desde GitHub Secrets y realizan teardown con `docker compose down -v` al finalizar.

---

## Herramientas Utilizadas

- **Ruff** — linter y formateador de código Python, ejecutado en cada push a cualquier rama.
- **cURL + Bash** — scripts de prueba de endpoints con validación de código HTTP.
- **pytest + aio-pika + httpx + motor** — pruebas de integración asíncronas sobre RabbitMQ y MongoDB.
- **pytest + requests** — pruebas E2E sobre el API Gateway en `localhost:8000`.
- **Postman** — colección de 22 requests agrupados en 6 carpetas para pruebas manuales. Ver [`evidence/postman/`](../evidence/postman/).
- **Logs de Docker** — trazabilidad con `docker compose logs -f <servicio>`.

---

## Pruebas Automatizadas — GitHub Actions

### 1. Calidad de Código — `ruff-check.yml`

Se ejecuta en **cada push a cualquier rama** y en pull requests. Corre dos pasos:

- `ruff check . --no-fix` — detecta errores de lint en todos los servicios Python.
- `ruff format . --check --diff` — verifica que el formato sea consistente sin modificar archivos.

Si alguno de los dos falla, el workflow bloquea el merge.

---

### 2. Pruebas de Integración con cURL — `curl_endpoint_testing.yml`

Se ejecuta en pushes y PRs a `main` y `develop`. Levanta el stack completo y ejecuta dos scripts bash:

**`auth_curl_tests.sh`** — prueba directamente `auth-service` en `localhost:8001`:

| Test | Request | Código esperado |
|---|---|---|
| `signup_ok` | `POST /auth/signup` con datos válidos | 201 |
| `signup_conflict` | `POST /auth/signup` con email duplicado | 409 |
| `admin_register_ok` | `POST /auth/admin/register` | 201 |
| `login_ok` | `POST /auth/login` con credenciales correctas | 200 |
| `login_bad_creds` | `POST /auth/login` con contraseña incorrecta | 401 |
| `me_ok` | `GET /auth/me` con token válido | 200 |
| `me_no_token` | `GET /auth/me` sin token | 401 |
| `me_bad_token` | `GET /auth/me` con token malformado | 401 |
| `refresh_ok` | `POST /auth/refresh` con tokens válidos | 200 |

**`gateway_curl_tests.sh`** — prueba el API Gateway en `localhost:8000` con un admin creado directamente en auth-service (bypass del gateway para bootstrap). Verifica los mismos flujos de autenticación pero pasando por el gateway con el header `Authorization: Bearer`.

---

### 3. Pruebas de Integración con Pytest — `pytest_integration.yml`

Se ejecuta en pushes y PRs a `main` y `develop`. Espera que `register-service` (puerto 8005) y `notification-service` (puerto 8004) estén healthy antes de correr.

**`test_register_flow.py`** — prueba el flujo de telemetría completo vía RabbitMQ:

| Test | Descripción |
|---|---|
| `test_health` | Verifica que `/health` retorna `status=healthy` y que mongo y rabbitmq son healthy |
| `test_register_flow` | Publica mensaje `device.register` a exchange `ioteur` vía aio-pika, hace polling a `GET /registers/{device_id}` hasta 15s, verifica que el registro contiene `device_id`, `values`, `time_procesing`, `id` y `created_at` |
| `test_unknown_device_returns_empty` | Verifica que un `device_id` inexistente retorna `[]` |

**`test_notification_flow.py`** — prueba el flujo de notificaciones vía RabbitMQ + MongoDB:

Publica mensajes `system.error` al exchange `ioteur` y verifica que el notification-service los consume e inserta la notificación en la colección `system_notifications` de MongoDB.

---

### 4. Pruebas E2E — `pytest_e2e.yml`

Se ejecuta en pushes a `main` y manualmente (`workflow_dispatch`). Levanta el stack con `--wait` (espera todos los healthchecks) y ejecuta `test_e2e.py` que cubre el flujo completo end-to-end a través del API Gateway en `localhost:8000`:

| Paso | Test | Request |
|---|---|---|
| 1 | `test_01_signup` | `POST /auth/signup` → 201 |
| 2 | `test_02_login` | `POST /auth/login` → 200, extrae `access_token` |
| 3 | `test_03_decode_jwt` | Decodifica el JWT y extrae `user_id` del campo `sub` |
| 4 | `test_04_register_device` | `POST /devices/register` → 202, polling hasta que el dispositivo aparece |
| 5+ | Registros + reports | `POST /registers/received` ×5, polling `GET /registers/{device_id}`, `GET /reports/{device_id}` |

---

### 5. Pruebas de EmailJS — `pytest_mailJS.yml`

Se ejecuta en pushes a `main` y manualmente. Verifica que el notification-service envía correctamente notificaciones por correo mediante la integración con EmailJS cuando se detecta un dispositivo desconectado.

**Evidencia — correo generado:**

![Evidencia EmailJS](../evidence/screenshots/Evidence_EmailJS.png)

---

## Pruebas Manuales — Postman

La colección [`evidence/postman/Ioteur_API_Gateway.postman_collection.json`](../evidence/postman/Ioteur_API_Gateway.postman_collection.json) contiene 22 requests agrupados en 6 carpetas:

| Carpeta | Contenido |
|---|---|
| **Auth** | signup, login (con script que guarda tokens), me, refresh, logout, update user, get by email |
| **Devices** | register, get by user, get by id, update |
| **Registers (Telemetría)** | received, get all, get by date |
| **Reports** | generate, get all, get by date |
| **Bootstrap** | `POST http://localhost:8001/auth/admin/register` directo al auth-service (para crear el primer admin sin pasar por el gateway) |
| **System (Internal)** | `POST /system/error` con header `x-internal-key` |

Los requests de login y refresh tienen **scripts de test** que guardan automáticamente `access_token`, `refresh_token`, `user_id` y `device_uuid` como variables de colección.

La evidencia de ejecución manual se encuentra en [`evidence/postman/Evidencia_Pruebas_Postman.pdf`](../evidence/postman/Evidencia_Pruebas_Postman.pdf).

---

## Evidencias

| Evidencia | Ubicación |
|---|---|
| Correo de notificación EmailJS | [`evidence/screenshots/Evidence_EmailJS.png`](../evidence/screenshots/Evidence_EmailJS.png) |
| Colección Postman (JSON) | [`evidence/postman/Ioteur_API_Gateway.postman_collection.json`](../evidence/postman/Ioteur_API_Gateway.postman_collection.json) |
| PDF de pruebas manuales Postman | [`evidence/postman/Evidencia_Pruebas_Postman.pdf`](../evidence/postman/Evidencia_Pruebas_Postman.pdf) |
| Logs de ejecución Docker | [`evidence/logs/`](../evidence/logs/) |
