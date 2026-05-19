# Modelo de Datos — Ioteur

---

## PostgreSQL — Auth Service

### Tabla `users`

Almacena los usuarios del sistema, gestionada por `auth-service`.

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | UUID del usuario (generado en app) |
| `name` | `VARCHAR(255)` | NOT NULL | Nombre del usuario |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE | Correo electrónico |
| `password_hash` | `VARCHAR(60)` | NOT NULL | Hash bcrypt de la contraseña |
| `role` | `ENUM('user','admin')` | NOT NULL | Rol del usuario |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, DEFAULT NOW() | Fecha de creación |

**Índices:** PK en `id`, UNIQUE en `email`.

---

## PostgreSQL — Device Service

### Tabla `devices`

Almacena los dispositivos IoT registrados, gestionada por `device-service`.

| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `device_uuid` | `VARCHAR(36)` | PK | UUID del dispositivo (generado en app) |
| `user_uuid` | `VARCHAR(36)` | NOT NULL | UUID del usuario propietario |
| `device_name` | `VARCHAR(255)` | NOT NULL | Nombre del dispositivo |
| `mac_address` | `VARCHAR(17)` | NOT NULL, UNIQUE | Dirección MAC |
| `report_interval` | `INTEGER` | NOT NULL, CHECK > 0 | Intervalo de reporte en segundos |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'active' | Estado: `active` / `inactive` |
| `last_seen` | `INTERVAL` | NULLABLE | Tiempo desde el último heartbeat |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT NOW() | Fecha de registro |

**Restricciones:** PK en `device_uuid`, UNIQUE en `mac_address`, CHECK `report_interval > 0`.

---

## Redis — Auth Service (`redis-auth`)

Almacena la **blacklist de tokens revocados** (logout).

```
Key pattern : token:<jti>
Value       : "revoked"
TTL         : coincide con la expiración del token
```

---

## Redis — Device Service / Call Service (`redis_device`)

Almacena el **estado en caliente de cada dispositivo** para consultas O(1).

```
Key pattern  : device:<device_uuid>
Type         : Hash
Campos:
  device_uuid    → UUID del dispositivo
  mac_address    → Dirección MAC
  device_name    → Nombre del dispositivo
  user_uuid      → UUID del propietario
  status         → active | inactive
  ultima_vez_log → ISO 8601 timestamp del último heartbeat recibido
```

---

## MongoDB — Register Service (`mongo_register`)

### Colección `register`

Almacena los registros de telemetría enviados por los dispositivos.

```json
{
  "_id": "UUID",
  "device_id": "UUID",
  "created_at": "2026-05-17T10:00:00+00:00",
  "time_procesing": 120,
  "values": {
    "temperature": 23.5,
    "humidity": 60,
    "pressure": 1013
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID (string) | Identificador único del registro |
| `device_id` | UUID (string) | Referencia al dispositivo |
| `created_at` | ISO 8601 string | Marca de tiempo de recepción |
| `time_procesing` | Integer | Tiempo de procesamiento en segundos |
| `values` | Object | Pares clave-valor arbitrarios según el tipo de dispositivo |

---

## MongoDB — Notification Service (`mongo_notifications`)

### Colección `email_notifications`

Registra cada intento de notificación por correo electrónico.

```json
{
  "_id": "UUID",
  "user_id": "UUID",
  "device_id": "UUID",
  "email": "usuario@example.com",
  "reason": "missed_intervals",
  "severity": "warning",
  "message": "3 consecutive heartbeats missed.",
  "status": "sent",
  "created_at": "2026-05-17T10:00:00+00:00"
}
```
| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID (string) | Identificador único |
| `user_id` | UUID (string) o null | Identificador único del usuario |
| `device_id` | UUID (string) | Dispositivo que generó la alerta |
| `email` | string | Destinatario del correo |
| `reason` | string | Razón de la desconexión |
| `severity` | string | `info` / `warning` / `critical` |
| `message` | string | Mensaje descriptivo |
| `status` | string | `unsent` → `sent` (se actualiza tras el envío exitoso) |
| `created_at` | ISO 8601 string | Marca de tiempo |

### Colección `system_notifications`

Registra errores y eventos internos del sistema para auditoría.

```json
{
  "_id": "UUID",
  "request_id": "UUID",
  "service_name": "call-service",
  "reason": "publish_failed",
  "severity": "critical",
  "message": "Failed to publish device.register for user X: ...",
  "created_at": "2026-05-17T10:00:00+00:00"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID (string) | Identificador único |
| `request_id` | UUID (string) | ID de la operación que generó el error |
| `service_name` | string | Servicio origen del error |
| `reason` | string | Código de razón (e.g. `publish_failed`, `mongo_insert_failed`) |
| `severity` | string | `info` / `warning` / `critical` |
| `message` | string | Detalle del error |
| `created_at` | ISO 8601 string | Marca de tiempo |

---

## MongoDB — Telemetry Service (`mongo_telemetry`)

### Colección `daily_reports`

Almacena los reportes de telemetría generados por el sistema.

```json
{
  "_id": "UUID",
  "deviceId": "UUID",
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
```

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID (string) | Identificador único del reporte |
| `deviceId` | UUID (string) | Dispositivo al que pertenece el reporte |
| `createdAt` | ISO 8601 string | Fecha de generación del reporte |
| `metricData` | Array | Lista de estadísticas por métrica |
| `metricData[].device_name` | string | Nombre de la métrica |
| `metricData[].valueList` | string[] | Lista de valores registrados |
| `metricData[].percentajeChange` | float | Variación porcentual (último vs primero) |
| `metricData[].topValue` | string | Valor máximo registrado |
| `metricData[].mostFrequentValue` | string | Valor más frecuente |


---

## Relaciones entre Entidades

```
users (PostgreSQL)
  └── 1:1 ──► devices (PostgreSQL)        [por user_uuid]
                └── 1:N ──► register (MongoDB)    [por device_id]
                └── 1:N ──► daily_reports (MongoDB) [por deviceId]
                └── 1:N ──► email_notifications (MongoDB) [por device_id]
```
