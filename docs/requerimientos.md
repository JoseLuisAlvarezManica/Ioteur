# Requerimientos del Sistema — Ioteur

---

## Requerimientos Funcionales

### RF-01 Registro y autenticación de usuarios
El sistema debe permitir crear una cuenta con credenciales básicas y autenticar sesiones mediante tokens JWT.
**Enfoque abordado:** Autenticación

### RF-02 Gestión de roles de usuario
El sistema debe diferenciar entre rol Administrador (acceso total, gestión de cuentas) y Usuario regular (gestión de sus propios dispositivos).
**Enfoque abordado:** Autenticación

### RF-03 Registro de dispositivos IoT
El usuario puede dar de alta un dispositivo proporcionando su dirección MAC y un nombre. El sistema genera un UUID y lo persiste en PostgreSQL.
**Enfoque abordado:** Dispositivos

### RF-04 Métodos de conexión
El sistema puede obtener mediciones de dispositivos solamente mediante HTTP.

### RF-05 Recepción de datos desde dispositivos IoT
El sistema debe aceptar payloads JSON desde dispositivos previamente registrados, validar su identidad y encolar el mensaje en RabbitMQ con respuesta 202 Accepted.
**Enfoque abordado:** Datos

### RF-06 Almacenamiento flexible de registros
Los datos recibidos de los dispositivos deben persistirse en MongoDB con los campos que el usuario decida; el registro se guarda como documento dentro de la carpeta del dispositivo.
**Enfoque abordado:** Datos

### RF-07 Monitoreo de estado en tiempo real
El usuario puede consultar el estado operativo de cada dispositivo (activo/inactivo) y su último tiempo visto (`last_seen`), mantenido en Redis.
**Enfoque abordado:** Dispositivos

### RF-08 Detección automática de desconexión
Si un dispositivo supera 2–3 plazos de tiempo, según el dispositivo, sin enviar datos, el sistema debe marcarlo como desconectado (evento `device.disconnected`) y notificar al usuario.
**Enfoque abordado:** Dispositivos

### RF-09 Generación de reportes de telemetría
El usuario puede solicitar un reporte de un dispositivo. El Telemetry Service procesa los registros almacenados y genera análisis agrupados por intervalos de tiempo en su propia instancia MongoDB.
**Enfoque abordado:** Telemetría

### RF-10 Notificaciones por correo electrónico
El sistema debe enviar alertas por email ante eventos relevantes (dispositivo desconectado, umbral superado). Cada intento queda registrado con su resultado (éxito/fallo) y un mecanismo de reintento vía RabbitMQ.
**Enfoque abordado:** Notificaciones

### RF-11 Registro de eventos y errores del sistema
El sistema debe mantener un historial de eventos relevantes clasificados por nivel de severidad (evento `system.error`). El administrador puede consultar este log desde la plataforma.
**Enfoque abordado:** Administración

### RF-12 Gestión de cuentas por el administrador
El administrador puede consultar, suspender o eliminar cuentas de usuarios registrados y monitorear el estado global del sistema desde un panel dedicado.
**Enfoque abordado:** Administración

---

## Requerimientos No Funcionales

### RNF-01 Baja latencia en el camino crítico de recepción
La validación de un dispositivo entrante (consulta a Redis + encolado en RabbitMQ) debe completarse con latencia mínima para no bloquear el flujo de datos. El diseño intencional usa Redis precisamente para evitar roundtrips a la base de datos relacional.
**Enfoque abordado:** Rendimiento

### RNF-02 Seguridad y control de acceso
Todas las peticiones al API Gateway deben validarse mediante token JWT. Los dispositivos sin UUID registrado o marcados como inactivos reciben 403 Forbidden.
**Enfoque abordado:** Seguridad

### RNF-03 Consistencia de datos entre distintos motores de bases
El sistema debe garantizar la sincronización entre PostgreSQL y MongoDB (p.ej. `last_seen`). Ante fallos parciales, debe detectar y resolver desincronizaciones para evitar inconsistencias en el estado reportado de dispositivos.
**Enfoque abordado:** Operaciones

### RNF-04 Escalabilidad horizontal de los microservicios
La arquitectura de microservicios debe permitir escalar horizontalmente el Call Service (principal cuello de botella) y los consumidores de RabbitMQ de forma independiente ante picos de concurrencia.
**Enfoque abordado:** Rendimiento

### RNF-05 Usabilidad para creadores sin experiencia en infraestructura
La interfaz y los flujos de registro, alta de dispositivos y consulta de datos deben ser lo suficientemente simples para que un entusiasta de IoT pueda operar la plataforma sin conocimientos de redes, bases de datos ni protocolos.
**Enfoque abordado:** UX
