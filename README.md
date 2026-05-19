# Ioteur

> Plataforma de monitoreo y telemetría IoT basada en microservicios

---

## Startup / Equipo

**Nombre:** Overview

---

## Integrantes y Roles

| Nombre | Rol |
|---|---|
| Jose Luis Alvarez Manica | Backend Developer / QA Engineer / DevOps |
| Jose Espinoza Ordas | Arquitecto de software / Data  |
| Fernando Agustin Hernandez Rivas |FrontEnd Developer |

---

## Descripción del Problema

Construir dispositivos IoT propios implica resolver desafíos de infraestructura —registro, monitoreo y almacenamiento de datos— que nada tienen que ver con el objetivo real: crear y experimentar.
Ioteur elimina esa barrera ofreciendo una base lista para usar, para que el foco esté en construir, no en resolver redes y bases de datos.

---

## Descripción de la Solución

**Ioteur** es una plataforma distribuida de microservicios que provee:

- Autenticación y gestión de usuarios con JWT (RS256) y roles (`user` / `admin`).
- Registro y gestión de dispositivos IoT identificados por `device_uuid` y `mac_address`.
- Ingesta de datos de telemetría en tiempo real, almacenados en MongoDB.
- Detección de desconexión de dispositivos mediante un scheduler interno en el Call Service que monitorea el último heartbeat de cada dispositivo en Redis y publica el evento `device.disconnected` al superar el umbral de inactividad (`report_interval × 3`).
- Generación automática de reportes con métricas por dispositivo (valor máximo, más frecuente, variación porcentual).
- Notificaciones por correo electrónico vía EmailJS cuando un dispositivo se desconecta.
- Registro de errores internos del sistema en MongoDB para auditoría.

Todos los servicios se comunican internamente a través de **RabbitMQ** (mensajería asíncrona) y **HTTP/REST** (consultas síncronas), expuestos al exterior únicamente a través del **API Gateway**.

---

## Arquitectura General

```
[Cliente / Frontend]
        |
        ▼ HTTP :8000
  ┌─────────────────┐
  │   API Gateway   │  ── autentica y redirige
  └────────┬────────┘
     ┌─────┴──────┐
     ▼            ▼  HTTP interno
┌─────────┐  ┌────────────┐
│  Auth   │  │    Call    │  ── orquestador de dominio
│ Service │  │  Service   │
└─────────┘  └──────┬─────┘
                    │ RabbitMQ "ioteur" exchange
        ┌───────────┼───────────────┐─────────────────┐
        ▼           ▼               ▼                 ▼
  [Device Svc] [Register Svc] [Telemetry Svc] [Notification Svc]
                                    
```

Ver diagrama completo en [docs/arquitectura.md](docs/arquitectura.md).

---

## Tecnologías Utilizadas

| Categoría | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Framework web | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 (asyncpg) |
| ODM MongoDB | Motor (async) |
| Cache / Estado | Redis 7 |
| Base de datos relacional | PostgreSQL 16 |
| Base de datos documental | MongoDB 8 |
| Mensajería | RabbitMQ 4 (pika) |
| Autenticación | JWT RS256 (python-jose), bcrypt (passlib) |
| Validación | Pydantic v2 |
| Notificaciones | EmailJS REST API |
| Contenedores | Docker + Docker Compose |

---

## Instrucciones de Instalación

### Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x o Docker Engine + Docker Compose v2.
- Git.

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/JoseLuisAlvarezManica/Ioteur.git
cd Ioteur

# 2. Crear el archivo de variables de entorno
cp .env.example .env        # Linux / macOS
copy .env.example .env      # Windows

# 3. Generar llaves públicas y privadas RSA

# Linux / macOS
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Windows (Git Bash / OpenSSL)
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Mostrar contenido de las llaves
cat private.pem             # Linux / macOS
type private.pem            # Windows

cat public.pem              # Linux / macOS
type public.pem             # Windows

# Copiar el contenido dentro de:
# PRIVATE_KEY=...
# PUBLIC_KEY=...

> ⚠️ **Cuidado** donde generas las llaves, evita que se generen en el repositorio especialmente si se va a publicar.

# 4. Generar llave de Fernet
pip install cryptography

from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())

# Copiar el contenido dentro de:
# UUID_ENCRYPTION_KEY=...

# 5. Configurar EmailJS
# Ioteur envía notificaciones por correo cuando un dispositivo se desconecta.
# Para ello necesitas una cuenta en EmailJS y los siguientes datos:
#   EMAILJS_SERVICE_ID    → ID del servicio de correo que crees en EmailJS
#   EMAILJS_TEMPLATE_ID   → ID de la plantilla de correo que configures
#   EMAILJS_PUBLIC_KEY    → Clave pública de tu cuenta
#   EMAILJS_PRIVATE_KEY   → Clave privada de tu cuenta
#
# Guía oficial para obtener estos valores:
# https://www.emailjs.com/docs/tutorial/overview/
#
# Una vez creada la cuenta y el servicio, puedes encontrar las claves en:
# https://dashboard.emailjs.com/admin/account

# 6. Editar .env con los valores reales
# Ver sección "Variables de entorno" más abajo
```

### Despliegue en Railway

[Railway](https://railway.app/) permite desplegar la plataforma en la nube sin configurar servidores. Cada servicio del stack se despliega como un servicio independiente dentro de un proyecto Railway.

**Pasos generales:**

1. Crea una cuenta en [railway.app](https://railway.app/) y un nuevo proyecto.
2. Para cada microservicio (api-gateway, auth-service, call-service, etc.) crea un nuevo servicio apuntando al repositorio y especifica la ruta del `Dockerfile` correspondiente (p. ej. `services/api-gateway/Dockerfile`).
3. Agrega los servicios de infraestructura desde el marketplace de Railway: **PostgreSQL**, **MongoDB**, **Redis** y **RabbitMQ** (o CloudAMQP como alternativa gestionada).
4. En cada servicio, configura las **variables de entorno** con los valores equivalentes a los del archivo `.env` local. Railway inyecta automáticamente las URLs de conexión de los servicios del marketplace.
5. Asegúrate de que los servicios internos se comunican entre sí usando las URLs de Railway (variables `*_SERVICE_URL`) y que solo el API Gateway tiene un dominio público expuesto.

Consulta la documentación oficial de Railway para más detalles: [https://docs.railway.app/](https://docs.railway.app/)

---

## Instrucciones de Ejecución

### Desarrollo (con puertos expuestos)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Los servicios quedan accesibles en:

| Servicio | URL |
|---|---|
| API Gateway | http://localhost:8000 |
| Auth Service | http://localhost:8001 |
| Call Service | http://localhost:8002 |
| Device Service | http://localhost:8003 |
| Notification Service | http://localhost:8004 |
| Register Service | http://localhost:8005 |
| Telemetry Service | http://localhost:8006 |
| RabbitMQ Management | http://localhost:15672 |

### Producción

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

El API Gateway queda expuesto en el puerto **80**.

### Staging

```bash
docker compose -f docker-compose.yml -f docker-compose.stagging.yml up -d --build
```

El API Gateway queda expuesto en el puerto **8081**.

---

## Variables de Entorno

El archivo `.env.example` contiene todas las variables con valores de ejemplo. Copiar como `.env` y completar antes de levantar los servicios.

| Variable                       | Descripción                                        |
| ------------------------------ | -------------------------------------------------- |
| `LOG_LEVEL`                    | Nivel de logs (`DEBUG`, `INFO`, `WARNING`, etc.)   |
| `POSTGRES_AUTH_USER`           | Usuario de PostgreSQL para auth-service            |
| `POSTGRES_AUTH_PASSWORD`       | Contraseña de PostgreSQL para auth-service         |
| `POSTGRES_AUTH_DB`             | Nombre de la base de datos de auth-service         |
| `POSTGRES_AUTH_DATABASE_URL`   | URL de conexión a PostgreSQL de auth-service       |
| `REDIS_AUTH_URL`               | URL de Redis utilizada por auth-service            |
| `POSTGRES_DEVICE_USER`         | Usuario de PostgreSQL para device-service          |
| `POSTGRES_DEVICE_PASSWORD`     | Contraseña de PostgreSQL para device-service       |
| `POSTGRES_DEVICE_DB`           | Nombre de la base de datos de device-service       |
| `POSTGRES_DEVICE_DATABASE_URL` | URL de conexión a PostgreSQL de device-service     |
| `REDIS_DEVICE_URL`             | URL de Redis utilizada por device-service          |
| `AUTH_SERVICE_URL`             | URL interna de auth-service                        |
| `CALL_SERVICE_URL`             | URL interna de call-service                        |
| `DEVICE_SERVICE_URL`           | URL interna de device-service                      |
| `REGISTER_SERVICE_URL`         | URL interna de register-service                    |
| `TELEMETRY_SERVICE_URL`        | URL interna de telemetry-service                   |
| `API_GATEWAY_URL`              | URL interna del API Gateway                        |
| `PRIVATE_KEY`                  | Clave privada RSA utilizada para firmar JWT        |
| `PUBLIC_KEY`                   | Clave pública RSA utilizada para validar JWT       |
| `UUID_ENCRYPTION_KEY`          | Clave unica para encriptar o desencriptar información sensible       |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | Tiempo de expiración del access token en minutos   |
| `REFRESH_TOKEN_EXPIRE_DAYS`    | Tiempo de expiración del refresh token en días     |
| `INTERNAL_API_KEY`             | Clave compartida entre servicios internos          |
| `RABBITMQ_USER`                | Usuario de RabbitMQ                                |
| `RABBITMQ_PASSWORD`            | Contraseña de RabbitMQ                             |
| `RABBITMQ_PORT`                | Puerto de RabbitMQ                                 |
| `RABBITMQ_URL`                 | URL de conexión a RabbitMQ                         |
| `MONGO_REGISTER_USER`          | Usuario de MongoDB para register-service           |
| `MONGO_REGISTER_PASSWORD`      | Contraseña de MongoDB para register-service        |
| `MONGO_REGISTER_DB`            | Nombre de la base de datos de register-service     |
| `MONGO_REGISTER_URL`           | URL de conexión a MongoDB de register-service      |
| `MONGO_TELEMETRY_USER`         | Usuario de MongoDB para telemetry-service          |
| `MONGO_TELEMETRY_PASSWORD`     | Contraseña de MongoDB para telemetry-service       |
| `MONGO_TELEMETRY_DB`           | Nombre de la base de datos de telemetry-service    |
| `MONGO_TELEMETRY_URL`          | URL de conexión a MongoDB de telemetry-service     |
| `MONGO_NOTIFICATIONS_USER`     | Usuario de MongoDB para notification-service       |
| `MONGO_NOTIFICATIONS_PASSWORD` | Contraseña de MongoDB para notification-service    |
| `MONGO_NOTIFICATIONS_DB`       | Nombre de la base de datos de notification-service |
| `MONGO_NOTIFICATIONS_URL`      | URL de conexión a MongoDB de notification-service  |
| `EMAILJS_URL`                  | Endpoint REST API de EmailJS                       |
| `EMAILJS_SERVICE_ID`           | ID del servicio en EmailJS                         |
| `EMAILJS_TEMPLATE_ID`          | ID de la plantilla de correo en EmailJS            |
| `EMAILJS_PUBLIC_KEY`           | Clave pública de EmailJS                           |
| `EMAILJS_PRIVATE_KEY`          | Clave privada de EmailJS                           |

> ⚠️ **Nunca** subas el archivo `.env` real al repositorio.

---

## Endpoints Principales

Todos los endpoints externos pasan por el **API Gateway** (`http://localhost:8000`).

### Autenticación

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/auth/signup` | Registro de usuario | Público |
| POST | `/auth/login` | Inicio de sesión | Público |
| POST | `/auth/refresh` | Renovar access token | Bearer |
| POST | `/auth/logout` | Cerrar sesión | Bearer |
| GET | `/auth/me` | Datos del usuario actual | Bearer |
| POST | `/auth/admin/register` | Crear usuario admin | Admin |

### Dispositivos

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/devices/register` | Registrar nuevo dispositivo | Bearer |
| PUT | `/devices/update` | Actualizar dispositivo | Bearer |
| GET | `/devices/{user_id}` | Obtener dispositivo de un usuario | Bearer |
| GET | `/devices/` | Listar todos los dispositivos | Admin |

### Registros de telemetría

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/registers/received` | Enviar datos de telemetría | Bearer |
| GET | `/registers/{device_id}` | Obtener registros de un dispositivo | Bearer |
| GET | `/registers/{device_id}/by-date` | Filtrar registros por rango de fechas | Bearer |

### Reportes

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/reports/{device_id}/generate` | Generar reporte diario | Bearer |
| GET | `/reports/{device_id}` | Consultar reportes | Bearer |
| GET | `/reports/{device_id}/by-date` | Filtrar reportes por fecha | Bearer |

Ver documentación detallada en [docs/api.md](docs/api.md).

---

## Eventos Principales (RabbitMQ)

Exchange: `ioteur` (direct, durable)

| Routing Key | Publicado por | Consumido por | Descripción |
|---|---|---|---|
| `device.register` | Call Service | Device Service | Registro de nuevo dispositivo |
| `device.update` | Call Service | Device Service | Actualización de dispositivo |
| `register.received` | Call Service | Register Service | Datos de telemetría recibidos |
| `device.disconnected` | Call Service (scheduler) | Notification Service | Dispositivo sin telemetría superó umbral de inactividad |
| `system.error` | Cualquier servicio | Notification Service | Error interno del sistema |
| `telemetry.report` | Call Service | Telemetry Service | Solicitud de generación de reporte |
| `report.created` | Telemetry Service | — | Confirmación de reporte creado |

Ver documentación completa en [docs/eventos.md](docs/eventos.md).

---

## Evidencias de Pruebas

Las evidencias se encuentran en la carpeta [`evidence/`](evidence/) y están organizadas en tres subcarpetas:

- **[`evidence/logs/`](evidence/logs/)** — Salida capturada de Docker Compose durante las pruebas de fallas simuladas (p. ej. reinicio del Redis de autenticación), útil para verificar el comportamiento de los decoradores y la recuperación automática de los servicios.
- **[`evidence/postman/`](evidence/postman/)** — Colección Postman con 22 requests agrupados en 6 carpetas que cubren los flujos principales: autenticación, dispositivos, telemetría, reportes, notificaciones y errores de sistema. Incluye una nota [`NOTA.md`](evidence/postman/NOTA.md) con instrucciones de uso.
- **[`evidence/screenshots/`](evidence/screenshots/)** — Capturas de pantalla de los escenarios probados: dispositivo activo/inactivo, reinicio de Redis y comportamiento del servicio de dispositivos ante fallos.

**Correo de notificación enviado por EmailJS:**

![EmailJS Evidence](docs/images/Evidence_EmailJS.png)

En [docs/pruebas.md](docs/pruebas.md) se detalla la estrategia completa de pruebas: los cuatro niveles (lint con Ruff, integración con cURL/pytest, E2E y notificación EmailJS), los workflows de GitHub Actions que los ejecutan, y cómo reproducirlos localmente.

---

## Fallas Simuladas

Se documentaron escenarios de falla controlada para verificar la resiliencia del sistema ante caídas de infraestructura:

- **Reinicio del Redis de autenticación** — Se simuló un reinicio prolongado (2 min) del contenedor `redis-auth`. Se verificó que el API Gateway y el Auth Service devuelven errores controlados durante la caída y recuperan la operación normal de forma automática al volver a estar disponible. También se comprobó que los datos persisten en Redis tras un reinicio directo.
- **Caída del Device Service** — Se detuvo el contenedor del servicio de dispositivos para observar cómo el sistema gestiona las peticiones entrantes cuando ese componente no está disponible.

Ver el detalle completo del proceso, comandos utilizados, respuestas obtenidas y capturas en [docs/fallas-simuladas.md](docs/fallas-simuladas.md).

---

## Lecciones Aprendidas

1. **Los contratos entre servicios cambian más de lo esperado:** Al inicio asumimos que los mensajes de RabbitMQ y los endpoints HTTP internos serían estables. En la práctica, cada nueva funcionalidad obligó a revisar y ajustar los esquemas de mensajes. Aprendimos que documentar los contratos desde el principio y versionar los eventos ahorra tiempo de depuración en etapas avanzadas.

2. **Coordinar un equipo en un sistema distribuido requiere más comunicación que en un monolito:** Cada integrante trabajaba en servicios distintos, pero los cambios en uno afectaban a los demás. Hubo momentos en que dos servicios funcionaban correctamente por separado pero fallaban al integrarse porque los supuestos de cada desarrollador no coincidían.

3. **Elegir la tecnología de persistencia correcta no es trivial:** No todos los datos del sistema tienen la misma naturaleza: los usuarios y dispositivos requieren consistencia y relaciones, mientras que los registros de telemetría son semi-estructurados y varían según el tipo de dispositivo. Esa diferencia nos llevó a evaluar qué herramienta se ajustaba mejor a cada caso: PostgreSQL donde importa la integridad relacional, MongoDB donde importa la flexibilidad del esquema. Tomar esa decisión de forma fundamentada, en lugar de usar una sola tecnología por comodidad, fue uno de los aprendizajes más importantes del proyecto.

4. **El diseño inicial rara vez sobrevive al contacto con la implementación:** La arquitectura que planteamos en papel tuvo que modificarse varias veces. El call-service, por ejemplo, comenzó como un simple proxy y terminó siendo el orquestador principal del dominio. Aceptar que el diseño es un punto de partida, no un contrato inamovible, redujo la fricción del equipo al momento de pivotar.

5. **La observabilidad es una necesidad:** Depurar problemas en un sistema con siete servicios comunicándose de forma asíncrona es considerablemente más difícil que depurar un monolito. Tener logs estructurados con niveles configurables desde el inicio ahorró horas de trabajo. Si volviéramos a empezar, también agregaríamos trazas distribuidas desde el día uno.
