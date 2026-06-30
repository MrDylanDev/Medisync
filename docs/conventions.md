# Convenciones del proyecto

## Estructura de apps

Cada app sigue el mismo patrón:

```
app/
├── models.py             # Solo modelos
├── serializers.py        # DRF serializers (si tiene API)
├── views.py              # API views (DRF @api_view)
├── views_frontend.py     # Frontend views (render templates)
├── views_public.py       # Vistas públicas (si aplica)
├── urls.py               # API endpoints (montados en /api/<app>/)
├── urls_frontend.py      # Frontend endpoints (montados en /<app>/)
├── admin.py              # Django admin config
├── signals.py            # Signals
└── tests.py              # Tests
```

## Vistas frontend

- Funciones con `@login_required` y decoradores de rol custom
- Usan `render()` con templates Bulma
- POST siempre redirige (nunca renderiza directo)

## Vistas API

- `@api_view(["GET", "POST"])` de DRF
- Permisos vía `@permission_classes` o checks manuales
- Devuelven `Response()` con datos serializados

## Naming

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| App | plural o dominio | `citas`, `medicos`, `expedientes` |
| Modelo | singular, Español | `Cita`, `Horario`, `Especialidad` |
| URL name | `app:accion` | `citas:agendar`, `medicos:mis_horarios` |
| Template | `app/accion.html` | `citas/book.html` |
| Serializer | `NombreModelo+Serializer` | `CitaSerializer` |
| Vars template | Español, snake_case | `citas_recientes`, `total_usuarios` |

## Auth dual

- **Frontend**: sesiones Django (login modal POST a `/accounts/login/`)
- **API REST**: JWT via `Authorization: Bearer <token>`
- Ambas comparten el mismo `Usuario` y modelo de permisos
