# Fallas simuladas — Ioteur

## El redis de auth se reinicia.

### Proceso de prueba
Debido a que el reinicio de redis era muy rapido, lo suficiente para no poder realizar el proceso de pruebas con endpoints, se decidio simular un reinicio tardado primero para probar el control de seguridad de los decoradores en los endpoints. Se siguieron los siguientes pasos:

1. Se levantó el entorno completo y se limitaron los logs con `PS D:\Distribuidos\Ioteur> docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build |Select-String -NotMatch "mongo|rabbit|Mongo|RABBIT|Rmq|RMQ" | Tee-Object -FilePath auth-redis-restart-errors.log`.
2. Se realizó el flujo inicial: registro de usuario (`POST /auth/signup`) y login (`POST /auth/login`) para obtener tokens válidos.
3. Se detuvo el contenedor de Redis de autenticación y se esperó 2 minutos para simular un reinicio tardado:
   ```sh
   docker stop ioteur-redis-auth-1; sleep 120; docker start ioteur-redis-auth-1
   ```
4. Con Redis caído, se ejecutaron peticiones autenticadas (`GET /auth/me`, `POST /auth/logout`) para observar la respuesta del sistema.
5. Una vez restaurado Redis, se repitieron las mismas peticiones para verificar la recuperación automática.
6. Se reinicio directamente el contenedor para comprobar la persistencia de los datos:
   ```sh
   docker restart ioteur-redis-auth-1
   ```
7. Se comprobo a traves de comandos la persistencia de los valores en redis y el registro de logs de errores en la BD de notificaciones.

---

### 1. Qué falla ocurrió
Se simuló un reinicio prolongado (2 minutos) del contenedor `ioteur-redis-auth-1`. Durante ese tiempo, los servicios que dependen de Redis para validar tokens (`api-gateway`, `auth-service`) no pudieron realizar operaciones autenticadas.

### 2. Cómo se detectó
Los microservicios detectaron la falla al intentar conectarse a `redis-auth:6379` y recibir un error de resolución de nombre. El fallo se manifestó de varias formas:

**a) Respuestas de error en los endpoints autenticados**

Tanto `POST /auth/logout` como `GET /auth/me` fallaron con el mismo mensaje mientras Redis estuvo caído:
```
Servicio temporalmente no disponible. Intente más tarde.
```

**b) Eventos críticos registrados en MongoDB (notification-service)**

El sistema registró automáticamente múltiples notificaciones con el siguiente formato:
```json
{
  "request_id": "b241a278-4576-4efb-80a7-c90fc02ad571",
  "service_name": "api-gateway",
  "reason": "redis_connection_failed",
  "severity": "critical",
  "message": "Redis no disponible en api-gateway (must_be_logged_in): Error -2 connecting to redis-auth:6379. Name or service not known.",
  "created_at": "2026-05-17T22:31:35.452071+00:00"
}
```
```json
{
  "request_id": "3bd00e9a-2d70-4131-ba69-2f3d75c38d1e",
  "service_name": "api-gateway",
  "reason": "redis_connection_failed",
  "severity": "critical",
  "message": "Redis no disponible en api-gateway (must_be_logged_in): Error -2 connecting to redis-auth:6379. Name or service not known.",
  "created_at": "2026-05-17T22:31:43.742863+00:00"
}
```

Cada petición autenticada fallida generó un registro independiente, lo que permite correlacionar el momento exacto de la caída con los `request_id` de las peticiones afectadas.

**c) Healthcheck del api-gateway**

El api-gateway expone un endpoint `GET /health` que verifica activamente la conectividad con Redis. Con Redis caído, este endpoint retorna `HTTP 503` con el siguiente cuerpo:
```json
{
  "status": "degraded",
  "checks": {
    "redis": "error: Error -2 connecting to redis-auth:6379. Name or service not known."
  }
}
```

### 3. Qué hizo el sistema
- Los endpoints autenticados devolvieron una respuesta de error controlada:
  ```json
  { "detail": "Servicio temporalmente no disponible. Intente más tarde." }
  ```
- El servicio de notificaciones persistió automáticamente eventos críticos en MongoDB con la razón `redis_connection_failed` y severidad `critical`.

### 4. Qué evidencia existe

**Capturas de pantalla** (en [`evidence/screenshots/Redis_auth_restart/`](../evidence/screenshots/Redis_auth_restart/)):

| Archivo | Descripción |
|---|---|
| [1.Inicio_loggeo.png](../evidence/screenshots/Redis_auth_restart/1.Inicio_loggeo.png) | Inicio de los servicios con logs reducidos. |
| [2.Fase1_curl.png](../evidence/screenshots/Redis_auth_restart/2.Fase1_curl.png) | Creación y login de un usuario.
| [3.Reinicio_tardado.png](../evidence/screenshots/Redis_auth_restart/3.Reinicio_tardado.png) | Comando de detención del contenedor redis-auth |
| [4.Fase2_curl.png](../evidence/screenshots/Redis_auth_restart/4.Fase2_curl.png) | Peticiones mientras Redis está caído (errores esperados) |
| [5.Finalizacion_reinicio.png](../evidence/screenshots/Redis_auth_restart/5.Finalizacion_reinicio.png) | Contenedor redis-auth levantado nuevamente |
| [6.Fase3_curl.png](../evidence/screenshots/Redis_auth_restart/4.Fase3_curl.png) | Peticiones tras la recuperación (funcionalidad restaurada) |
| [7.Reinicio.png](../evidence/screenshots/Redis_auth_restart/7.Reinicio.png) | Reinicio manual del contenedor para confirmar recuperación |
| [8.Comprobacion_persistencia.png](../evidence/screenshots/Redis_auth_restart/8.Comprobacion_persistencia.png) | Verificación de tokens en Redis y registros en MongoDB |

**Logs**: [`evidence/logs/auth-redis-restart-errors.log`](../evidence/logs/auth-redis-restart-errors.log)

### 5. Cómo se recupera o controla el error
Al restaurar el contenedor ioteur-redis-auth-1, los servicios recuperaron la conectividad automáticamente sin necesidad de reiniciarlos. Gracias a la persistencia habilitada en Redis, todos los tokens y listas negras se mantuvieron intactos, por lo que las sesiones activas no se invalidaron y el usuario no necesitó volver a autenticarse. Los tokens se limpian solos al vencer mediante TTL, sin intervención manual.

Durante la caída, el sistema no falló silenciosamente: devolvió errores controlados al cliente, registró eventos críticos en MongoDB y reportó el estado degradado en /health, permitiendo correlacionar la falla con precisión.

En producción, configurar restart: always en el docker-compose.yml haría que Docker levantara Redis automáticamente ante cualquier caída. Durante estas pruebas se omitió intencionalmente para poder observar el comportamiento del sistema ante la falla.

## El servicio de dispositivos se cae temporalmente.

### Proceso de prueba

Se siguieron los siguientes pasos:

1. Se levantó el entorno completo y se limitaron los logs con `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build |Select-String -NotMatch "mongo|Mongo" | Tee-Object -FilePath device-service-down-errors.log`.
2. Se realizó el flujo inicial: registro de usuario, login, registro de un dispositivo (`sensor-e2e`) y obtención de su `device_uuid`.
3. Se detuvo manualmente el contenedor del device-service:
   ```sh
   docker stop ioteur-device-service-1
   ```
4. Con el servicio caído, se intentó registrar un segundo dispositivo (`sensor-e2e_2`) y consultar los dispositivos del usuario para observar la respuesta del sistema.
5. También se enviaron 5 registros de telemetría, se consultaron registros y se generó un reporte —operaciones que **no dependen directamente del device-service**— para verificar que el resto del sistema continuaba funcionando.
6. Se reinició el contenedor:
   ```sh
   docker start ioteur-device-service-1
   ```
7. Se comprobó que la consulta de dispositivos se recuperó automáticamente y que el segundo dispositivo (registrado mientras el servicio estaba caído vía RabbitMQ) fue procesado correctamente al volver a levantar el servicio.

---

### 1. Qué falla ocurrió
Se detuvo manualmente el contenedor `ioteur-device-service-1`. Durante ese tiempo, los endpoints que realizan consultas HTTP directas al device-service (`GET /devices/me`) dejaron de funcionar. Sin embargo, los endpoints que operan mediante RabbitMQ (`POST /devices/register`, `POST /registers/received`) continuaron aceptando peticiones sin degradación visible.

### 2. Cómo se detectó
La falla se manifestó de varias formas:

**a) `GET /devices/me` falló con error controlado**

Mientras el device-service estuvo caído, la consulta de dispositivos devolvió:
```json
{
  "detail": {
    "detail": "Unexpected error"
  }
}
```
El call-service detectó el fallo HTTP al intentar contactar al device-service y publicó un evento `system.error` a RabbitMQ con `reason: upstream_error`.

**b) `POST /devices/register` siguió funcionando**

El registro de un nuevo dispositivo (`sensor-e2e_2`) durante la caída fue **aceptado correctamente** porque va a través de RabbitMQ, no directamente al device-service:
```json
{ "message": "device.register event queued" }
```
El evento quedó encolado y fue procesado por el device-service al recuperarse.

**c) Telemetría y reportes no se vieron afectados**

Los 5 registros de telemetría y la generación del reporte se procesaron sin error, ya que estas operaciones dependen del call-service y MongoDB, no del device-service directamente:
```json
{ "message": "register.received event queued" }
{ "message": "telemetry.report event queued" }
```

**d) Eventos críticos registrados en MongoDB (notification-service)**

El call-service publicó automáticamente notificaciones de error por cada intento fallido de contactar al device-service:
```json
{
  "service_name": "call-service",
  "reason": "upstream_error",
  "severity": "critical",
  "message": "device-service returned 500 on GET /devices/<user_id>"
}
```

**e) Líneas del log de contenedores que evidencian la caída y el error**

En el log general del stack (`device-service-down-errors.log`) se pueden observar las siguientes líneas clave:

```
device-service-1 exited with code 0
```
Esto marca el momento exacto en que el contenedor del device-service fue detenido.

Inmediatamente después, los intentos de `GET /devices/me` generaron errores `500` visibles tanto en el call-service como en el api-gateway:
```
call-service-1   | INFO: 172.18.0.16:50490 - "GET /devices/8bcdce67-eab8-4a38-805f-e9987e8df0f7 HTTP/1.1" 500 Internal Server Error
api-gateway-1    | INFO: 172.18.0.1:42120 - "GET /devices/me HTTP/1.1" 500 Internal Server Error
```

En contraste, los endpoints asíncronos no mostraron ningún error en el log:
```
call-service-1   | INFO: 172.18.0.16:50474 - "POST /devices/register HTTP/1.1" 202 Accepted
api-gateway-1    | INFO: 172.18.0.1:42114 - "POST /devices/register HTTP/1.1" 202 Accepted
```

### 3. Qué hizo el sistema
- `GET /devices/me` devolvió un error controlado propagado desde el call-service.
- `POST /devices/register` siguió funcionando: el evento fue encolado en RabbitMQ y procesado al recuperarse el servicio, lo que demuestra el desacoplamiento asíncrono.
- La telemetría y los reportes continuaron operando con normalidad.
- El notification-service persistió automáticamente los errores de upstream en MongoDB.

### 4. Qué evidencia existe

**Capturas de pantalla** (en [`evidence/screenshots/device_service_down/`](../evidence/screenshots/device_service_down/)):

| Archivo | Descripción |
|---|---|
| [1.Inicio_servicios.png](../evidence/screenshots/device_service_down/1.Inicio_servicios.png) | Inicio del entorno con logs filtrados. |
| [2.Parar_Servicio.png](../evidence/screenshots/device_service_down/2.Parar_Servicio.png) | Detención manual del contenedor `ioteur-device-service-1`. |
| [3.Reiniciar_Servicio.png](../evidence/screenshots/device_service_down/3.Reiniciar_Servicio.png) | Inicio del contenedor nuevamente. |
| [4.1_Fase1.png](../evidence/screenshots/device_service_down/4.1_Fase1.png) | Fase 1: registro de usuario, login, registro de dispositivo y obtención de `device_uuid`. |
| [4.2_Fase2.png](../evidence/screenshots/device_service_down/4.2_Fase2.png) | Fase 2: intento de registro de segundo dispositivo (encolado) y fallo en `GET /devices/me`. |
| [4.3_Fase2.png](../evidence/screenshots/device_service_down/4.3_Fase2.png) | Fase 2: envío de 5 registros de telemetría con éxito (servicio caído). |
| [4.4_Fase2.png](../evidence/screenshots/device_service_down/4.4_Fase2.png) | Fase 2: consulta de registros persistidos correctamente. |
| [4.5_Fase2.png](../evidence/screenshots/device_service_down/4.5_Fase2.png) | Fase 2: generación y consulta de reporte exitosa. |
| [4.6_Fase3.png](../evidence/screenshots/device_service_down/4.6_Fase3.png) | Fase 3: `GET /devices/me` recuperado, ambos dispositivos visibles. |
| [5.Error_en_DB.png](../evidence/screenshots/device_service_down/5.Error_en_DB.png) | Registro del error de upstream en MongoDB (notification-service). |

**Logs**: [`evidence/logs/device-service-down-errors.log`](../evidence/logs/device-service-down-errors.log)

**Bash de prueba**: [`evidence/logs/device-service-bash`](../evidence/logs/device-service-bash)

### 5. Cómo se recupera o controla el error
Al reiniciar `ioteur-device-service-1`, el servicio recuperó la conectividad automáticamente. El evento de registro del segundo dispositivo (`sensor-e2e_2`) que quedó encolado en RabbitMQ durante la caída fue procesado correctamente al volver a levantar el servicio, y ambos dispositivos aparecieron disponibles en `GET /devices/me`.

Durante la caída, el sistema no falló silenciosamente: los endpoints que dependían directamente del device-service devolvieron errores controlados, el notification-service registró los eventos de upstream error en MongoDB, y los endpoints desacoplados (telemetría, reportes, registro de dispositivo) continuaron operando con normalidad gracias a RabbitMQ.

En producción, configurar `restart: always` en el `docker-compose.yml` haría que Docker levantara el device-service automáticamente ante cualquier caída. Durante estas pruebas se omitió intencionalmente para observar el comportamiento del sistema ante la falla.