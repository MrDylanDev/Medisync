# Signals — side effects

Cada acción clave del sistema dispara efectos secundarios automáticos. No hay que llamarlos manualmente.

## Tabla de eventos

| Evento | Signal | Efecto |
|--------|--------|--------|
| Se crea un `Usuario` con `rol=paciente` | `accounts/signals.py` | Crea `Paciente` |
| Se crea un `Usuario` con `rol=medico` | `accounts/signals.py` | Crea `MedicoProfile` (matrícula temporal) |
| Se crea una `Cita` | `notificaciones/signals.py` | Notificación tipo `cita_confirmada` al paciente |
| Se cancela una `Cita` | `notificaciones/signals.py` | Notificación `cita_cancelada` al paciente Y al médico |
| Se crea o cambia estado de una `Cita` | `citas/signals.py` | Auditoría (`AuditoriaCita`) con estado anterior → nuevo |
| Se guarda un `Horario` | `medicos/signals.py` | Validación: rechaza si se superpone con otro del mismo médico |

## Diagrama de flujo

```
Usuario creado ──┬─ rol=paciente → Paciente creado
                 └─ rol=medico   → MedicoProfile + MedicoPractice creados

Cita ──┬─ post_save (create) → Notificacion "confirmada" al paciente
       │                     → AuditoriaCita (null → pendiente)
       └─ post_save (cancel) → Notificacion "cancelada" a paciente + médico
                             → AuditoriaCita (pendiente → cancelada)

Horario ── pre_save → validación de superposición (rechaza con ValidationError)
```

## Archivos fuente

- `accounts/signals.py` — `crear_perfil_usuario`
- `citas/signals.py` — `capturar_estado_anterior` + `crear_auditoria_cita`
- `medicos/signals.py` — `validar_horario_sin_superposicion`
- `notificaciones/signals.py` — `crear_notificacion_cita`
