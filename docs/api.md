# Documentación de API — Ioteur

Todos los endpoints externos son accedidos a través del **API Gateway** (`http://localhost:8000` en desarrollo).

Cualquier mención del uuid del usuario se refiere a la versión encriptada que se encuentra en el JWT, la cual desencripta en api-gateway"

## Autenticación

Los endpoints protegidos requieren un `Authorization: Bearer <access_token>` en el header.  
Los endpoints de administrador requieren adicionalmente que el token tenga `role: admin`.

---

## Autenticación y Usuarios (`/auth`)

### `POST /auth/signup`

Registra un nuevo usuario con rol `user`.

**Auth:** Público

**Request Body:**
```json
{
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "password": "mi_contraseña_segura"
}
```

**Response `201 Created`:** (sin body)

**Errores:**
- `409 Conflict` — El correo ya está registrado.

---

### `POST /auth/login`

Inicia sesión y retorna tokens JWT.

**Auth:** Público

**Request Body:**
```json
{
  "email": "juan@example.com",
  "password": "mi_contraseña_segura"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errores:**
- `401 Unauthorized` — Credenciales inválidas.

---

### `POST /auth/refresh`

Renueva el `access_token` usando el `refresh_token`.

**Auth:** Bearer (access token vigente o expirado) + Header `x-refresh-token: <refresh_token>`

**Response `200 OK`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errores:**
- `401 Unauthorized` — Refresh token inválido o expirado.

---

### `POST /auth/logout`

Invalida los tokens del usuario actual.

**Auth:** Bearer + Header `x-refresh-token: <refresh_token>`

**Response `200 OK`:**
```json
{ "detail": "Logged out successfully" }
```

---

### `GET /auth/me`

Retorna los datos del usuario autenticado.

**Auth:** Bearer

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "role": "user"
}
```

---

### `POST /auth/admin/register`

Registra un nuevo usuario con rol `admin`.

**Auth:** Admin

**Request Body:** mismo que `/auth/signup`

**Response `201 Created`:** (sin body)

---

### `GET /auth/user/by-email/{email}`

Obtiene los datos de un usuario por su correo electrónico.

**Auth:** Admin

**Path Params:**
- `email` — Correo del usuario.

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "role": "user"
}
```

**Errores:**
- `404 Not Found` — Usuario no encontrado.

---

### `PUT /auth/user/{user_id}`

Actualiza nombre, correo, contraseña o rol de un usuario.

**Auth:** Admin

**Path Params:**
- `user_id` — UUID del usuario.

**Request Body (campos opcionales):**
```json
{
  "name": "Nuevo Nombre",
  "email": "nuevo@example.com",
  "password": "nueva_contraseña",
  "role": "admin"
}
```

**Response `200 OK`:** datos actualizados del usuario.

---

### `DELETE /auth/user/{user_id}`

Elimina un usuario del sistema.

**Auth:** Admin

**Path Params:**
- `user_id` — UUID del usuario.

**Response `200 OK`:**
```json
{ "detail": "User deleted successfully" }
```

---

## Dispositivos (`/devices`)

### `POST /devices/register`

Registra un nuevo dispositivo IoT de forma asíncrona.

**Auth:** Bearer

**Request Body:**
```json
{
  "user_id": "uuid-del-usuario",
  "device_name": "Sensor Sala",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "report_interval": 60
}
```

**Response `202 Accepted`:**
```json
{ "message": "device.register event queued" }
```

**Errores:**
- `500 Internal Server Error` — Fallo al publicar en RabbitMQ.

---

### `PUT /devices/update`

Actualiza el estado o el intervalo de reporte de un dispositivo.

**Auth:** Bearer

**Request Body (campos opcionales):**
```json
{
  "device_uuid": "uuid-del-dispositivo",
  "report_interval": 120,
  "status": "inactive"
}
```

**Response `202 Accepted`:**
```json
{ "message": "device.update event queued" }
```

---

### `GET /devices/`

Lista todos los dispositivos registrados.

**Auth:** Admin

**Response `200 OK`:**
```json
[
  {
    "device_uuid": "uuid",
    "user_id": "uuid",
    "device_name": "Sensor Sala",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "report_interval": 60,
    "status": "active"
  }
]
```

---

### `GET /devices/{user_id}`

Obtiene el dispositivo asociado a un usuario.

**Auth:** Bearer

**Path Params:**
- `user_id` — UUID del usuario.

**Response `200 OK`:**
```json
{
  "device_uuid": "uuid",
  "user_id": "uuid",
  "device_name": "Sensor Sala",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "report_interval": 60,
  "status": "active"
}
```

**Errores:**
- `404 Not Found` — No existe dispositivo para ese usuario.

---

## Registros de Telemetría (`/registers`)

### `POST /registers/received`

Recibe datos de telemetría de un dispositivo.

**Auth:** Bearer

**Request Body:**
```json
{
  "device_id": "uuid-del-dispositivo",
  "time_procesing": 100,
  "values": {
    "temperature": 23.5,
    "humidity": 60,
    "pressure": 1013
  }
}
```

**Response `202 Accepted`:**
```json
{ "message": "register.received event queued" }
```

**Comportamiento de reconexión automática:** Si el dispositivo estaba marcado como `inactive` en Redis (por inactividad previa detectada por el scheduler), el Call Service detecta el nuevo heartbeat, actualiza el estado a `active`, publica `device.update` para sincronizar el Device Service y luego procesa el registro normalmente.

**Errores:**
- `404 Not Found` — Dispositivo no registrado (no existe en Redis).
- `500 Internal Server Error` — Fallo al publicar en RabbitMQ.

---

### `GET /registers/{device_id}`

Obtiene los registros de telemetría de un dispositivo, ordenados por fecha descendente.

**Auth:** Bearer

**Path Params:**
- `device_id` — UUID del dispositivo.

**Query Params:**
- `limit` (int, default=100, max=1000) — Número máximo de registros.
- `skip` (int, default=0) — Desplazamiento para paginación.

**Response `200 OK`:**
```json
[
  {
    "id": "uuid",
    "device_id": "uuid",
    "created_at": "2026-05-17T10:00:00+00:00",
    "time_procesing": 100,
    "values": { "temperature": 23.5 }
  }
]
```

---

### `GET /registers/{device_id}/by-date`

Filtra registros de telemetría por rango de fechas.

**Auth:** Bearer

**Path Params:**
- `device_id` — UUID del dispositivo.

**Query Params:**
- `from` (datetime ISO 8601) — Fecha de inicio.
- `to` (datetime ISO 8601) — Fecha de fin.
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)

**Response `200 OK`:** igual que `GET /registers/{device_id}`.

---

## Reportes (`/reports`)

### `POST /reports/{device_id}/generate`

Solicita la generación asíncrona de un reporte de telemetría para un dispositivo.

**Auth:** Bearer

**Path Params:**
- `device_id` — UUID del dispositivo.

**Response `202 Accepted`:**
```json
{ "message": "telemetry.report event queued" }
```

**Errores:**
- `404 Not Found` — No hay registros para ese dispositivo.
- `500 Internal Server Error` — Fallo al publicar en RabbitMQ.

---

### `GET /reports/{device_id}`

Obtiene los reportes generados para un dispositivo, ordenados por fecha descendente.

**Auth:** Bearer

**Path Params:**
- `device_id` — UUID del dispositivo.

**Query Params:**
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)

**Response `200 OK`:**
```json
[
  {
    "deviceId": "uuid",
    "createdAt": "2026-05-17T10:00:00+00:00",
    "metricData": [
      {
        "device_name": "temperature",
        "valueList": ["23.5", "24.0", "22.8"],
        "percentajeChange": -3.0,
        "topValue": "24.0",
        "mostFrequentValue": "23.5"
      }
    ]
  }
]
```

---

### `GET /reports/{device_id}/by-date`

Filtra reportes por rango de fechas.

**Auth:** Bearer

**Path Params:**
- `device_id` — UUID del dispositivo.

**Query Params:**
- `from` (datetime ISO 8601) — Fecha de inicio.
- `to` (datetime ISO 8601) — Fecha de fin.
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)

**Response `200 OK`:** igual que `GET /reports/{device_id}`.

---

## Sistema (Interno) — `POST /system/error`

Relay interno para propagar errores al bus de mensajes.

**Auth:** Header `x-internal-key: <INTERNAL_API_KEY>`

**Request Body:**
```json
{
  "reason": "service_timeout",
  "message": "El servicio X no respondió en tiempo",
  "severity": "warning",
  "request_id": "uuid",
  "service_name": "mi-servicio"
}
```

**Response `202 Accepted`:**
```json
{ "message": "system.error event queued" }
```

---

## Notificaciones (`/notifications`)
 
### `GET /notifications/device/{device_id}`
 
Obtiene las notificaciones asociadas a un dispositivo específico.
 
**Auth:** Bearer — usuario autenticado  
**Path Params:**
- `device_id` — UUID del dispositivo.
**Query Params:**
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)
**Response `200 OK`:**
```json
[
  {
    "device_id": "uuid",
    "message": "Temperatura fuera de rango",
    "created_at": "2026-05-17T10:00:00+00:00"
  }
]
```
 
---
 
### `GET /notifications/me`
 
Obtiene todas las notificaciones del usuario autenticado, agregando las de todos sus dispositivos.
 
**Auth:** Bearer — usuario autenticado  
**Query Params:**
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)
**Response `200 OK`:** igual que `GET /notifications/device/{device_id}`.
 
---
 
### `GET /notifications/user/{user_id}`
 
Obtiene las notificaciones de cualquier usuario por su ID. Exclusivo para administradores.
 
**Auth:** Bearer — requiere rol `admin`  
**Path Params:**
- `user_id` — UUID del usuario.
**Query Params:**
- `limit` (int, default=100, max=1000)
- `skip` (int, default=0)
**Response `200 OK`:** igual que `GET /notifications/device/{device_id}`.
 
**Errores:**
- `401 Unauthorized` — Token ausente o inválido.
- `403 Forbidden` — El usuario no tiene rol `admin`.
---


## Health Checks

Cada servicio expone un endpoint `GET /health` que verifica la conectividad con sus dependencias.

| Servicio | URL | Dependencias verificadas |
|---|---|---|
| API Gateway | `GET http://localhost:8000/health` | Redis |
| Auth Service | `GET http://localhost:8001/health` | PostgreSQL, Redis |
| Call Service | `GET http://localhost:8002/health` | Redis, RabbitMQ |
| Device Service | `GET http://localhost:8003/health` | (sin checks externos) |
| Notification Service | `GET http://localhost:8004/health` | MongoDB, RabbitMQ |
| Register Service | `GET http://localhost:8005/health` | MongoDB, RabbitMQ |
| Telemetry Service | `GET http://localhost:8006/health` | MongoDB, RabbitMQ |

**Response `200 OK` (healthy):**
```json
{ "status": "healthy", "checks": { "mongo": "healthy", "rabbitmq": "healthy" } }
```

**Response `503 Service Unavailable` (degraded):**
```json
{ "status": "unhealthy", "checks": { "mongo": "healthy", "rabbitmq": "unhealthy" } }
```
