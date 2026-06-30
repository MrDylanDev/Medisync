# API — ejemplos de uso

Todos los endpoints protegidos requieren `Authorization: Bearer <jwt>`.

```bash
# 1. Obtener JWT
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"correo":"medico@ejemplo.com","password":"MiPass123!"}'
# → { "access": "<jwt>", "refresh": "<jwt>" }

TOKEN="<jwt>"

# 2. Listar especialidades
curl http://localhost:8000/api/especialidades/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Ver disponibilidad de un médico en una fecha
curl "http://localhost:8000/api/medicos/1/disponibilidad/?fecha=2026-07-15" \
  -H "Authorization: Bearer $TOKEN"

# 4. Reservar un turno
curl -X POST http://localhost:8000/api/citas/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "medico": 1,
    "horario": 42,
    "motivo": "Consulta de rutina"
  }'

# 5. Cancelar turno
curl -X POST http://localhost:8000/api/citas/1/cancelar/ \
  -H "Authorization: Bearer $TOKEN"

# 6. Obtener comprobante PDF
curl http://localhost:8000/api/citas/1/comprobante/ \
  -H "Authorization: Bearer $TOKEN" \
  -o comprobante.pdf
```

> Documentación interactiva: `/api/schema/swagger-ui/`
