# Eventos — Ioteur

---

## Configuración del Bus de Mensajes

- **Broker:** RabbitMQ 4
- **Exchange:** `ioteur`
- **Tipo de exchange:** `direct`
- **Durabilidad:** durable (sobrevive reinicios del broker)
- **Persistencia de mensajes:** `delivery_mode=2` (todos los mensajes son persistentes)

---

## Convención de Mensajes

Todos los mensajes se publican en formato **JSON** con `Content-Type: application/json`.

Los consumidores utilizan:
- `basic_ack` cuando el mensaje fue procesado correctamente.
- `basic_nack` (sin requeue) cuando ocurre un error irrecuperable, para evitar loops infinitos.

---

## Catálogo de Eventos

---

### `device.register`

**Publicado por:** Call Service  
**Consumido por:** Device Service  
**Queue:** `device.register.queue`  
**Descripción:** Se publica cuando un usuario solicita registrar un nuevo dispositivo IoT. El Device Service crea el registro en PostgreSQL y lo cachea en Redis.

**Payload:**
```json
{
  "user_id": "uuid-del-usuario",
  "device_name": "Mi Sensor",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "report_interval": 60
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `user_id` | UUID string | Usuario propietario del dispositivo |
| `device_name` | string | Nombre del dispositivo |
| `mac_address` | string | Dirección MAC (formato `XX:XX:XX:XX:XX:XX`) |
| `report_interval` | integer | Intervalo de reporte en segundos (> 0) |

---

### `device.update`

**Publicado por:** Call Service  
**Consumido por:** Device Service  
**Queue:** `device.update.queue`  
**Descripción:** Se publica cuando se actualiza el estado o el intervalo de reporte de un dispositivo.

**Payload:**
```json
{
  "device_uuid": "uuid-del-dispositivo",
  "report_interval": 120,
  "status": "inactive"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `device_uuid` | UUID string | Dispositivo a actualizar |
| `report_interval` | integer (opcional) | Nuevo intervalo de reporte |
| `status` | string (opcional) | Nuevo estado: `active` / `inactive` |

---

### `register.received`

**Publicado por:** Call Service  
**Consumido por:** Register Service  
**Queue:** `register.device.register`  
**Descripción:** Se publica cuando un dispositivo envía datos de telemetría. El Register Service persiste el registro en MongoDB.

**Payload:**
```json
{
  "device_id": "uuid-del-dispositivo",
  "time_procesing": 120,
  "values": {
    "temperature": 23.5,
    "humidity": 60
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `device_id` | UUID string | Dispositivo que envía el dato |
| `time_procesing` | integer | Tiempo de procesamiento en segundos |
| `values` | object | Pares clave-valor con los datos del sensor |

---

### `device.disconnected`

**Publicado por:** Call Service (scheduler de inactividad)  
**Consumido por:** Notification Service  
**Queue:** `notification.device.disconnected`  
**Descripción:** Se publica cuando el scheduler del Call Service detecta que un dispositivo superó su umbral de inactividad (calculado como `report_interval × 3`) sin enviar telemetría. El Call Service marca el dispositivo como `inactive` en Redis, publica el evento `device.update` para sincronizar el Device Service, y publica `device.disconnected` para que el Notification Service envíe un correo de alerta al usuario y registre la notificación en MongoDB.

**Payload:**
```json
{
  "device_id": "uuid-del-dispositivo",
  "email": "usuario@example.com",
  "reason": "inactivity_timeout",
  "severity": "warning",
  "message": "Device 'ESP32-1' has not sent telemetry for 189s (threshold: 90s). It has been marked as inactive."
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `device_id` | UUID string | Dispositivo desconectado |
| `email` | string | Correo del usuario propietario |
| `reason` | string | Razón de la desconexión (`inactivity_timeout`) |
| `severity` | string | `info` / `warning` / `critical` |
| `message` | string | Mensaje descriptivo con tiempo de inactividad y umbral |

---

### `system.error`

**Publicado por:** Cualquier servicio (via API Gateway o directamente)  
**Consumido por:** Notification Service  
**Queue:** `notification.system.error`  
**Descripción:** Se publica ante errores internos del sistema (fallos de publicación, errores de BD, etc.). El Notification Service persiste el error en MongoDB para auditoría.

**Payload:**
```json
{
  "_id": "uuid-del-error",
  "request_id": "uuid-de-la-operacion",
  "service_name": "call-service",
  "reason": "publish_failed",
  "severity": "critical",
  "message": "Failed to publish device.register for user X: connection refused",
  "created_at": "2026-05-17T10:00:00+00:00"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `_id` | UUID string | Identificador único del error |
| `request_id` | UUID string | ID de la operación que generó el error |
| `service_name` | string | Servicio que publicó el error |
| `reason` | string | Código de razón (`publish_failed`, `mongo_insert_failed`, etc.) |
| `severity` | string | `info` / `warning` / `critical` |
| `message` | string | Detalle del error |
| `created_at` | ISO 8601 string | Marca de tiempo |

---

### `telemetry.report`

**Publicado por:** Call Service  
**Consumido por:** Telemetry Service  
**Queue:** `telemetry.reports.create`  
**Descripción:** Se publica cuando un usuario solicita generar un reporte para un dispositivo. El payload incluye todos los registros de telemetría del dispositivo obtenidos previamente del Register Service.

**Payload:**
```json
{
  "device_id": "uuid-del-dispositivo",
  "records": [
    {
      "id": "uuid-registro",
      "device_id": "uuid-del-dispositivo",
      "created_at": "2026-05-17T09:00:00+00:00",
      "time_procesing": 100,
      "values": { "temperature": 23.5, "humidity": 60 }
    }
  ]
}
```


---

### `report.created`

**Publicado por:** Telemetry Service  
**Consumido por:** *(sin consumidor definido actualmente — disponible para integraciones futuras)*  
**Descripción:** Se publica tras generar exitosamente un reporte diario. Puede ser consumido por otros servicios en el futuro (e.g., notificación al usuario, dashboard en tiempo real).

**Payload:**
```json
{
  "request_id": "uuid-de-la-solicitud",
  "message": "Report created successfully",
  "status": "success"
}
```

---

## Diagrama de Flujo de Eventos

```
Call Service ──► device.register ──────────────► Device Service
Call Service ──► device.update ────────────────► Device Service
Call Service ──► register.received ────────────► Register Service
*(sin publicador)* ──► device.disconnected ─────► Notification Service ──► EmailJS
Call Service ──► telemetry.report ─────────────► Telemetry Service
Telemetry Service ──► report.created ──────────► (futuras integraciones)
Any Service ──► system.error ──────────────────► Notification Service ──► MongoDB
```
