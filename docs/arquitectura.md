# Arquitectura — Ioteur

---

## Estilo Arquitectónico

Ioteur sigue una arquitectura de **microservicios** desacoplados que se comunican mediante dos mecanismos:

1. **HTTP/REST sincrónico** — para consultas que requieren respuesta inmediata (API Gateway → Auth/Call Services, Call Service → servicios internos).
2. **Mensajería asíncrona vía RabbitMQ** — para operaciones de escritura y eventos que pueden procesarse en background sin bloquear al cliente.

---

## Diagrama de Arquitectura

![Diagrama_Arquitectura](./md_images/diagrama_arquitectura.png)

## Descripción de Servicios

### API Gateway (`:8000`)

**Responsabilidad:** Único punto de entrada para los clientes externos.

- Valida y decodifica tokens JWT RS256.
- Aplica RBAC: diferencia rutas de `user` y `admin`.
- Actúa como proxy inverso hacia `auth-service` y `call-service`.
- No tiene base de datos propia; usa Redis para verificar tokens en la blacklist (logout).

**Dependencias de arranque:** `auth-service` (healthy), `call-service` (healthy).

---

### Auth Service (`:8001`)

**Responsabilidad:** Gestión de identidad y autenticación.

- CRUD de usuarios (sign up, login, update, delete).
- Emite `access_token` (JWT, 15 min) y `refresh_token` (JWT, 7 días) firmados con RS256.
- Almacena tokens revocados en Redis (blacklist para logout).
- Persiste usuarios en PostgreSQL.

**Dependencias de arranque:** `postgres-auth` (healthy), `redis-auth` (healthy).

---

### Call Service (`:8002`)

**Responsabilidad:** Orquestador del dominio de negocio IoT.

- Recibe peticiones del API Gateway y las convierte en eventos o en consultas HTTP a servicios internos.
- **Publica** eventos en RabbitMQ (`device.register`, `device.update`, `register.received`, `device.disconnected`, `telemetry.report`, `system.error`).
- **Consulta** sincrónicamente a `device-service`, `register-service` y `telemetry-service` para operaciones de lectura.
- Mantiene el estado de los dispositivos en Redis y ejecuta un **trabajo periódico** que escanea todos los dispositivos en Redis, detecta cuáles superan su `report_interval`, publica `device.disconnected` y notifica al usuario.

**Dependencias de arranque:** `redis_device` (healthy), `rabbitmq` (healthy).

---

### Device Service (`:8003`)

**Responsabilidad:** Fuente de verdad de los dispositivos registrados.

- Persiste dispositivos en PostgreSQL (con `device_uuid`, `mac_address`, `report_interval`, `status`, etc.).
- Al registrar un dispositivo, lo escribe también en Redis como cache de estado.
- **Suscribe** a los eventos `device.register` y `device.update` desde RabbitMQ.
- Expone endpoints HTTP internos de lectura para que Call Service consulte dispositivos.

**Dependencias de arranque:** `rabbitmq` (healthy), `postgres-device` (healthy), `redis_device` (healthy).

---

### Register Service (`:8005`)

**Responsabilidad:** Almacenamiento de registros de telemetría.

- **Suscribe** al evento `register.received` desde RabbitMQ.
- Persiste cada registro en MongoDB (`register` collection) con valores arbitrarios como documento.
- Expone endpoints HTTP internos de lectura con paginación y filtro por fecha.
- Implementa reintentos (hasta 3 veces) ante fallos de inserción en MongoDB.

**Dependencias de arranque:** `mongo_register` (healthy), `rabbitmq` (healthy).

---

### Telemetry Service (`:8006`)

**Responsabilidad:** Generación de reportes de telemetría.

- **Suscribe** al evento `telemetry.report` desde RabbitMQ.
- Calcula métricas por campo de los registros recibidos: lista de valores, variación porcentual, valor máximo, valor más frecuente.
- Persiste el reporte diario en MongoDB (`daily_reports` collection).
- Publica el evento `report.created` al finalizar.
- Expone endpoints HTTP internos de lectura con paginación y filtro por fecha.

**Dependencias de arranque:** `mongo_telemetry` (healthy), `rabbitmq` (healthy).

---

### Notification Service (`:8004`)

**Responsabilidad:** Envío de notificaciones y registro de errores del sistema.

- **Suscribe** a los eventos `device.disconnected` y `system.error` desde RabbitMQ.
- Al recibir `device.disconnected`: persiste un `EmailNotification` en MongoDB (status=`unsent`) y envía el correo vía EmailJS. Si el envío es exitoso, actualiza el status a `sent`.
- Al recibir `system.error`: persiste un `SystemNotification` en MongoDB para auditoría.

**Dependencias de arranque:** `mongo_notifications` (healthy), `rabbitmq` (healthy).

---

## Infraestructura de Datos

| Base de datos | Instancia Docker | Utilizada por | Propósito |
|---|---|---|---|
| PostgreSQL 16 | `postgres-auth` | auth-service | Tabla `users` |
| PostgreSQL 16 | `postgres-device` | device-service | Tabla `devices` |
| Redis 7 | `redis-auth` | auth-service | Blacklist de refresh tokens |
| Redis 7 | `redis_device` | call-service, device-service | Estado de dispositivos (heartbeat) |
| MongoDB 8 | `mongo_register` | register-service | Colección `register` (telemetría) |
| MongoDB 8 | `mongo_notifications` | notification-service | Colecciones `email_notifications`, `system_notifications` |
| MongoDB 8 | `mongo_telemetry` | telemetry-service | Colección `daily_reports` |

---

## Bus de Mensajes

**Exchange:** `ioteur` — tipo `direct`, durable.

Todos los mensajes son persistentes (`delivery_mode=2`). Los consumidores usan `basic_ack` al procesar correctamente y `basic_nack` (sin requeue) ante errores irrecuperables.

| Routing Key | Queue | Publicador | Consumidor |
|---|---|---|---|
| `device.register` | `device.register.queue` | Call Service | Device Service |
| `device.update` | `device.update.queue` | Call Service | Device Service |
| `register.received` | `register.device.register` | Call Service | Register Service |
| `device.disconnected` | `notification.device.disconnected` | Call Service | Notification Service |
| `system.error` | `notification.system.error` | Cualquier servicio | Notification Service |
| `telemetry.report` | `telemetry.reports.create` | Call Service | Telemetry Service |
| `report.created` | — | Telemetry Service | (sin consumidor definido actualmente) |

---

## Flujos Principales

### Flujo: Registro de Usuario

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant GW as API Gateway
    participant AS as Auth Service
    participant PG as PostgreSQL

    U->>FE: completa formulario de registro
    FE->>GW: POST /auth/signup
    GW->>AS: POST /auth/signup (proxy)
    AS->>PG: SELECT usuario por email (verifica duplicado)
    PG-->>AS: sin resultado
    AS->>PG: INSERT nuevo usuario (id, nombre, email, password_hash, rol)
    PG-->>AS: 201 Created
    AS-->>GW: 201 Created
    GW-->>FE: 201 Created
    FE-->>U: "Registro exitoso"
```

### Flujo: Registro de Dispositivo

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant GW as API Gateway
    participant CS as Call Service
    participant MQ as RabbitMQ
    participant DS as Device Service
    participant PG as PostgreSQL
    participant RD as Redis

    U->>FE: registra nuevo dispositivo
    FE->>GW: POST /devices/register (Bearer token)
    GW->>GW: valida JWT RS256 + extrae user_id
    GW->>CS: POST /devices/register (user_id añadido al payload)
    CS->>MQ: publish device.register
    MQ->>DS: consume device.register
    DS->>PG: INSERT device
    DS->>RD: HSET device state (device_uuid, status, report_interval, ...)
    DS-->>MQ: basic_ack
```

### Flujo: Envío de Telemetría

```mermaid
sequenceDiagram
    actor D as Dispositivo IoT
    participant GW as API Gateway
    participant CS as Call Service
    participant RD as Redis
    participant MQ as RabbitMQ
    participant DS as Device Service
    participant RS as Register Service
    participant MDB as MongoDB

    D->>GW: POST /registers/received (Bearer token)
    GW->>GW: valida JWT RS256
    GW->>CS: POST /registers/received (proxy)
    CS->>RD: EXISTS device:{id} (verifica registro)
    RD-->>CS: device encontrado
    CS->>RD: HGET status
    alt dispositivo estaba inactive (reconexión)
        CS->>RD: HSET status=active
        CS->>MQ: publish device.update (status=active)
        MQ->>DS: consume device.update → UPDATE PostgreSQL
    end
    CS->>RD: HSET ultima_vez_log = now()
    CS->>MQ: publish register.received
    MQ->>RS: consume register.received
    RS->>MDB: INSERT registro telemetría
    RS-->>MQ: basic_ack
```

### Flujo: Generación de Reporte

```mermaid
sequenceDiagram
    actor U as Usuario
    participant FE as Frontend
    participant GW as API Gateway
    participant CS as Call Service
    participant RS as Register Service
    participant MQ as RabbitMQ
    participant TS as Telemetry Service
    participant MDB as MongoDB

    U->>FE: solicita generar reporte del dispositivo
    FE->>GW: POST /reports/{device_id}/generate (Bearer token)
    GW->>GW: valida JWT RS256
    GW->>CS: POST /reports/{device_id}/generate (proxy)
    CS->>RS: HTTP GET /registers/{device_id}?limit=1000
    RS-->>CS: lista de registros de telemetría
    CS->>MQ: publish telemetry.report (device_id + records)
    MQ->>TS: consume telemetry.report
    TS->>TS: calcula métricas (máximo, más frecuente, variación %)
    TS->>MDB: INSERT reporte diario (daily_reports)
    TS->>MQ: publish report.created
    TS-->>MQ: basic_ack
```

### Flujo: Notificación de Desconexión

```mermaid
sequenceDiagram
    participant SCH as Scheduler (Call Service)
    participant RD as Redis
    participant AS as Auth Service
    participant MQ as RabbitMQ
    participant DS as Device Service
    participant NS as Notification Service
    participant MDB as MongoDB
    participant EJS as EmailJS API

    loop cada ciclo del scheduler
        SCH->>RD: SCAN device:* (todos los activos)
        RD-->>SCH: campos del dispositivo (ultima_vez_log, report_interval, ...)
        SCH->>SCH: elapsed > report_interval × 3?
    end
    SCH->>RD: HSET status=inactive
    SCH->>MQ: publish device.update (status=inactive)
    MQ->>DS: consume device.update → UPDATE PostgreSQL
    SCH->>AS: HTTP GET /auth/user/{user_uuid} (obtiene email)
    AS-->>SCH: email del usuario
    SCH->>MQ: publish device.disconnected (device_id, user_uuid, email, mensaje)
    MQ->>NS: consume device.disconnected
    NS->>MDB: INSERT EmailNotification (status=unsent)
    NS->>EJS: POST envío de correo
    EJS-->>NS: 200 OK
    NS->>MDB: UPDATE EmailNotification (status=sent)
    NS-->>MQ: basic_ack
```

### Flujo: Error de Sistema

```mermaid
sequenceDiagram
    participant SVC as Cualquier Servicio
    participant GW as API Gateway
    participant CS as Call Service
    participant MQ as RabbitMQ
    participant NS as Notification Service
    participant MDB as MongoDB

    SVC->>GW: POST /system/error (X-Internal-Key)
    GW->>GW: verifica INTERNAL_API_KEY
    GW->>CS: POST /system/error (proxy)
    CS->>MQ: publish system.error
    MQ->>NS: consume system.error
    NS->>MDB: INSERT SystemNotification (auditoría)
    NS-->>MQ: basic_ack
```
