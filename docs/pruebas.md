
### CURL para confirmar que la api de node JS funcionaba
curl -X POST https://api.emailjs.com/api/v1.0/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "YOUR_SERVICE_ID",
    "template_id": "YOUR_TEMPLATE_ID",
    "user_id": "YOUR_PUBLIC_KEY",
    "accessToken": "YOUR_PRIVATE_KEY",
    "template_params": {
      "email": "your@email.com",
      "device_id": "test-device-123",
      "severity": "warning",
      "reason": "missed_intervals",
      "status": "unsent",
      "message": "3 consecutive heartbeats missed.",
      "created_at": "2026-05-13T22:00:00"
    }
  }'


### Evidencia de un correo generado con el CURL anterior

![Logo](./images/Evidence_EmailJS.png)