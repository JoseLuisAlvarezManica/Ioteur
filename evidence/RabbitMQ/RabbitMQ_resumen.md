## RabbitMQ — Configuración Ioteur

### Exchange
| Propiedad | Valor |
|-----------|-------|
| Nombre | `ioteur` |
| Tipo | `direct` |
| Durable | `true` |

---

### Queues (7)
| Queue | Estado |
|-------|--------|
| `device.delete.queue` | running |
| `device.register.queue` | running |
| `device.update.queue` | running |
| `notification.device.disconnected` | running |
| `notification.system.error` | running |
| `register.device.register` | running |
| `telemetry.reports.create` | running |

---

### Bindings
| Queue | Routing Key |
|-------|-------------|
| `device.delete.queue` | `device.delete` |
| `device.register.queue` | `device.register` |
| `device.update.queue` | `device.update` |
| `notification.device.disconnected` | `device.disconnected` |
| `notification.system.error` | `system.error` |
| `register.device.register` | `register.received` |
| `telemetry.reports.create` | `telemetry.report` |