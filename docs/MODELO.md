# Recorrido del modelo

```mermaid
erDiagram
    facultad ||--o{ jugador : pertenece
    facultad ||--o{ equipo : representa
    torneo ||--o{ equipo : contiene
    equipo ||--o{ equipo_jugador_torneo : plantel
    jugador ||--o{ equipo_jugador_torneo : inscripcion
    torneo ||--o{ equipo_jugador_torneo : edicion
    jugador o|--o{ equipo : capitan
    complejo ||--o{ cancha : contiene
    cancha ||--o{ partido : sede
    turno ||--o{ partido : horario
    torneo ||--o{ partido : edicion
    equipo ||--o{ partido : local_o_visitante
    partido ||--o{ planilla_partido : participantes
    jugador ||--o{ planilla_partido : participa
    equipo ||--o{ planilla_partido : representa
    planilla_partido ||--o{ gol : registra
    planilla_partido ||--o{ tarjeta : recibe
    equipo_jugador_torneo ||--o{ sancion_jugador : sanciones
```

`login` autentica los dos roles; no identifica a los jugadores ni está ligado a una CI.
El diagrama describe relaciones, no todas las reglas deportivas. Ver `01_esquema.sql` para PK/FK y `REQUISITOS.md` para las reglas todavía pendientes.

## Lectura de un resultado

Partido → planilla → gol. La planilla informa el equipo del jugador. Si autogol es falso, el gol suma a ese equipo; si es verdadero, suma al rival. Las vistas de resultados y actuaciones permiten calcular la tabla de posiciones sin almacenar marcadores duplicados.

## Identidad e historia

La CI identifica una persona. `equipo_jugador_torneo` agrega la edición y el equipo de esa persona, sin crear un jugador nuevo por cada torneo. Los datos del avance mantienen una única facultad/tipo por persona; por ahora se bloquea su modificación cuando existe una inscripción.
