# Decisiones Técnicas — Ioteur

---

## DT-01 — Arquitectura de Microservicios

**Decisión:** Dividir el sistema en 7 microservicios independientes en lugar de una aplicación monolítica.

**Contexto:** El sistema debe gestionar múltiples dominios bien diferenciados: autenticación, gestión de dispositivos, recepción de telemetría, generación de reportes y notificaciones.

**Razones:**
- Permite escalar cada componente de forma independiente según su carga (e.g., el Register Service recibe mucho más tráfico que el Telemetry Service).
- Facilita el despliegue y la actualización de un servicio sin afectar a los demás.
- Aísla los fallos: si el Notification Service falla, la ingesta de datos continúa funcionando.

**Consecuencias:**
- Mayor complejidad operativa (múltiples bases de datos, múltiples contenedores).
- Necesidad de un API Gateway para el exterior y contratos de comunicación claros entre servicios.

---

## DT-02 — API Gateway como Único Punto de Entrada

**Decisión:** Exponer al exterior únicamente el API Gateway. Los servicios internos no son accesibles desde fuera de la red Docker.

**Contexto:** Los clientes no deben conocer la topología interna de los servicios.

**Razones:**
- Centraliza la autenticación y autorización (JWT RS256, RBAC).
- Simplifica la configuración de CORS, TLS y rate limiting en un solo lugar.
- Los servicios internos pueden evolucionar sin afectar la interfaz pública.

**Consecuencias:**
- El API Gateway es un punto único de fallo potencial (mitigado con `restart: always` y healthchecks en producción).
- Agrega una capa de latencia adicional a cada petición.

---

## DT-03 — RabbitMQ como Bus de Mensajes Asíncrono

**Decisión:** Usar RabbitMQ con un exchange `direct` durable para comunicar eventos entre servicios.

**Contexto:** Las operaciones de escritura (registro de dispositivos, ingesta de telemetría, notificaciones) no requieren respuesta inmediata y son costosas.

**Razones:**
- Desacopla temporalmente productores y consumidores.
- Los mensajes persistentes (`delivery_mode=2`) garantizan que no se pierdan ante reinicios del broker.
- El modelo de acknowledgements (`basic_ack` / `basic_nack`) garantiza procesamiento at-least-once.
- RabbitMQ es ligero y bien soportado en Python via `pika`.

**Alternativas consideradas:**
- **Kafka:** más adecuado para streaming de alta escala; considerado excesivo para este proyecto.
- **HTTP directo:** introduce acoplamiento temporal y penaliza el tiempo de respuesta al cliente.

**Consecuencias:**
- Los consumidores deben ser idempotentes (aunque en este proyecto no se implementó deduplicación explícita).
- Se requiere gestión de errores y dead-letter queues para producción.

---

## DT-04 — Integración Sync/Async de Pika con FastAPI

**Decisión:** Ejecutar los consumidores de RabbitMQ en hilos separados usando `threading.Thread` y despachar el trabajo al event loop de asyncio mediante `asyncio.run_coroutine_threadsafe`.

**Contexto:** `pika` es una biblioteca síncrona y bloqueante. FastAPI usa un event loop asyncio. Combinarlos directamente bloquearía el servidor.

**Razones:**
- Permite que los consumidores RabbitMQ corran de forma concurrente con el servidor HTTP sin bloquear el event loop.
- Es el patrón oficial recomendado para integrar pika con asyncio.

**Consecuencias:**
- El código de los consumidores debe usar `asyncio.run_coroutine_threadsafe` explícitamente.
- Los timeouts en `future.result(timeout=30)` previenen que un mensaje lento bloquee el hilo consumidor indefinidamente.

---

## DT-05 — JWT RS256 con Claves Asimétricas

**Decisión:** Usar el algoritmo RS256 (RSA + SHA-256) para firmar y verificar tokens JWT.

**Contexto:** Se necesita autenticación stateless con soporte para verificación en múltiples servicios sin compartir secretos.

**Razones:**
- La clave privada solo reside en `auth-service` (firma). Los demás servicios solo necesitan la clave pública (verificación).
- RS256 es más seguro que HS256 (simétrico) en arquitecturas multi-servicio donde no todos los servicios deben poder firmar tokens.
- Estándar ampliamente soportado por bibliotecas como `python-jose`.

**Consecuencias:**
- Las claves PEM deben gestionarse con cuidado como variables de entorno, requiriendo un `field_validator` para normalizar saltos de línea.
- La rotación de claves requiere actualizar la variable de entorno y reiniciar los servicios.

---

## DT-06 — Redis para Estado de Dispositivos

**Decisión:** Almacenar el estado en caliente de cada dispositivo (último heartbeat) en Redis, además de PostgreSQL.

**Contexto:** El Call Service necesita verificar en tiempo real si un dispositivo está registrado antes de aceptar telemetría.

**Razones:**
- Redis provee acceso O(1) a los datos de dispositivo, sin necesidad de consultar PostgreSQL en cada telemetría.
- El hash de Redis por `device:<uuid>` almacena los campos relevantes del dispositivo (estado, `ultima_vez_log`).
- Permite detectar desconexiones comparando el timestamp del último heartbeat con el `report_interval`.

**Consecuencias:**
- Redis es el cache del estado de PostgreSQL. Si Redis pierde un dispositivo (flush), el sistema lo rechazará hasta que el estado sea re-sincronizado.
- Se asume consistencia eventual entre PostgreSQL y Redis.

---

## DT-07 — MongoDB para Datos Semi-Estructurados

**Decisión:** Usar MongoDB para los datos de telemetría, notificaciones y reportes.

**Contexto:** Los registros de telemetría tienen un campo `values` con estructura variable según el tipo de dispositivo (temperatura, humedad, presión, etc.).

**Razones:**
- MongoDB permite almacenar documentos con esquema flexible sin migraciones de tabla.
- El modelo de documentos se adapta naturalmente a los reportes JSON con arrays de métricas.
- Motor (async) se integra bien con el event loop de FastAPI/asyncio.

**Alternativas consideradas:**
- **PostgreSQL con columna JSONB:** viable, pero más complejo de consultar y agregar para datos heterogéneos.
- **TimescaleDB:** adecuado para series temporales; considerado excesivo para el scope actual.

**Consecuencias:**
- Sin esquema forzado en MongoDB, la validación de datos recae completamente en Pydantic antes de la inserción.

---

## DT-08 — Tres Instancias Separadas de MongoDB

**Decisión:** Usar tres contenedores MongoDB independientes: uno para register, uno para notifications y uno para telemetry.

**Contexto:** Cada servicio gestiona datos de dominio muy diferentes y con patrones de acceso distintos.

**Razones:**
- Aislamiento de datos: un fallo o corrupción en una base no afecta a las otras.
- Cada servicio tiene su propia URL de conexión y credenciales, sin acoplamiento.
- Facilita escalar o mover cada base de forma independiente.

**Consecuencias:**
- Mayor uso de recursos en entornos de desarrollo (tres procesos MongoDB).
- En producción se podría consolidar en un único cluster MongoDB con bases de datos separadas.

---

## DT-09 — Notificaciones vía EmailJS REST API

**Decisión:** Usar la API REST de EmailJS para enviar correos electrónicos de notificación, en lugar de un servidor SMTP propio.

**Contexto:** Se necesita enviar correos de alerta cuando un dispositivo se desconecta.

**Razones:**
- EmailJS elimina la necesidad de configurar y mantener un servidor SMTP.
- La integración es simple: una petición HTTP POST con el payload del template.
- Permite diseñar el template de correo de forma visual sin tocar código.

**Consecuencias:**
- Dependencia de un servicio externo de terceros.
- Las credenciales (service ID, template ID, public/private key) deben gestionarse como variables de entorno.
- Límites de envío según el plan de EmailJS.

---

## DT-11 — Scheduler de Inactividad Colocado en el Call Service

**Decisión:** Implementar el scheduler de detección de inactividad de dispositivos dentro del Call Service, en lugar de crear un servicio independiente dedicado.

**Contexto:** El sistema necesita detectar periódicamente qué dispositivos han dejado de enviar telemetría (superaron su `report_interval × 3` sin heartbeat) y publicar el evento `device.disconnected` para que el Notification Service envíe la alerta al usuario.

**Razones:**
- El Call Service ya es el único propietario del estado en caliente de los dispositivos en Redis (`device:<uuid>`). Colocar el scheduler allí elimina la necesidad de exponer ese estado a otro servicio vía HTTP o mensajería.
- El scheduler necesita leer y escribir los campos `status` y `ultima_vez_log` de cada dispositivo, operaciones que el Call Service ya realiza en cada heartbeat recibido. Extraer esa lógica a un servicio externo duplicaría el acceso a Redis desde dos procesos distintos, introduciendo potenciales condiciones de carrera.
- El scheduler se inicia dentro del mismo proceso asyncio de FastAPI mediante `asyncio.create_task`, lo que le permite compartir la conexión a Redis y el canal RabbitMQ sin infraestructura adicional.
- Crear un servicio separado solo para ejecutar un loop periódico agrega un contenedor, una imagen Docker, una entrada en `docker-compose.yml`, variables de entorno y un healthcheck, aumentando la complejidad operativa sin ningún beneficio de escalabilidad (el scheduler no necesita más de una réplica).

**Alternativas consideradas:**
- **Servicio `heartbeat-service` independiente:** añadiría aislamiento de fallos, pero requeriría compartir acceso a Redis con el Call Service o introducir un nuevo endpoint interno para consultar el estado de los dispositivos, duplicando la lógica de dominio.
- **Celery + Redis como broker de tareas:** adecuado para tareas distribuidas de alta escala; excesivo para un único loop de 120 segundos.
- **Cron job en el host / contenedor sidecar:** introduce dependencia de infraestructura externa y dificulta el manejo de señales de apagado junto al ciclo de vida del proceso FastAPI.

**Consecuencias:**
- Si el Call Service se reinicia, el scheduler también se reinicia con él; el período máximo de ceguera ante inactividades es el intervalo del loop (120 segundos por defecto).
- En un entorno con múltiples réplicas del Call Service se deberían coordinar los schedulers (e.g., con un lock distribuido en Redis) para evitar notificaciones duplicadas. En el scope actual de una sola réplica esto no representa un problema.

---

## DT-10 — Docker Compose Multi-Archivo por Entorno

**Decisión:** Usar un `docker-compose.yml` base y archivos de override separados por entorno (`dev`, `staging`, `prod`).

**Contexto:** La configuración de puertos, políticas de reinicio y límites de recursos varía según el entorno.

**Razones:**
- Evita duplicar toda la definición de servicios en cada entorno.
- El archivo base define la estructura; los overrides añaden solo las diferencias (puertos, restart policy, resource limits).
- Patrón estándar recomendado por la documentación oficial de Docker Compose.

**Consecuencias:**
- Hay que especificar ambos archivos en el comando de arranque (`-f docker-compose.yml -f docker-compose.dev.yml`).
- Facilita la gestión en CI/CD seleccionando el override según el entorno de despliegue.
