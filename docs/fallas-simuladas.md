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

**Logs filtrados**: [`evidence/logs/auth-redis-restart-errors.log`](../evidence/logs/auth-redis-restart-errors.log)

### 5. Cómo se recupera o controla el error
Al restaurar el contenedor ioteur-redis-auth-1, los servicios recuperaron la conectividad automáticamente sin necesidad de reiniciarlos. Gracias a la persistencia habilitada en Redis, todos los tokens y listas negras se mantuvieron intactos, por lo que las sesiones activas no se invalidaron y el usuario no necesitó volver a autenticarse. Los tokens se limpian solos al vencer mediante TTL, sin intervención manual.

Durante la caída, el sistema no falló silenciosamente: devolvió errores controlados al cliente, registró eventos críticos en MongoDB y reportó el estado degradado en /health, permitiendo correlacionar la falla con precisión.

En producción, configurar restart: always en el docker-compose.yml haría que Docker levantara Redis automáticamente ante cualquier caída. Durante estas pruebas se omitió intencionalmente para poder observar el comportamiento del sistema ante la falla.