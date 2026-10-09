# Consola remota

Le da a Claude acceso a la base de producción durante una sesión de trabajo,
sin pasarle la contraseña del panel. Por qué quedó así:
[decisiones.md, "Consola remota"](decisiones.md).

## Abrir una sesión

1. Panel → **Datos e IA → Consola remota**.
2. "Para qué": una frase (queda en el registro). "Dura": 4 h alcanza casi
   siempre. **Generar token**.
3. Copiar la línea `LABSIM_CONSOLA_TOKEN=lsc_...`, solo la parte `lsc_...`.
4. En una terminal propia (no con `!` dentro de Claude Code, porque así el
   token queda en el chat), desde la carpeta de LabSim:

   ```
   ./scripts/labsim_token.sh lsc_...
   ```

   Lo guarda en `~/.config/labsim/consola.env` (solo lo lee tu usuario) y
   hace un `ping`: si muestra la fecha de vencimiento, quedó bien.
5. Decirle a Claude que ya está.

Un token nuevo reemplaza al anterior en el archivo.

## Cerrar

Cualquiera de estas:

- Claude, al terminar: `python3 scripts/consola.py revocar` (revoca en el
  servidor y borra el archivo).
- Panel → Consola remota → tabla **Tokens** → **Revocar** en la fila
  "Vigente".
- No hacer nada: vence solo a las horas elegidas.

`./scripts/labsim_token.sh --borrar` borra el archivo pero **no** revoca el
token.

## Qué puede hacer Claude

```
python3 scripts/consola.py ping                    vigencia del token, versión PHP/SQLite
python3 scripts/consola.py sql "SELECT ..." [-p '[..]']   una sentencia, con filas
python3 scripts/consola.py script cambios.sql      varias, en una transacción (todas o ninguna)
python3 scripts/consola.py esquema                 CREATE de toda la base
python3 scripts/consola.py backup                  copia en data/backups/ (antes de cambios grandes)
python3 scripts/consola.py archivos [ruta]         listado dentro de data/
python3 scripts/consola.py leer ruta [-o archivo]  un archivo de data/ (.gz descomprimido)
python3 scripts/consola.py revocar                 corta el token
```

- SQL libre: lee, modifica y borra, con los datos sin enmascarar.
- Archivos: solo `data/` (informes, tickets, fotos, backups). Nada fuera de
  ahí, ni `config/`.
- `--json` muestra la respuesta tal cual. `--env archivo` usa otro archivo de
  token.

## Dónde queda registrado

- Cada llamada (SQL, filas, cambios, error, IP): panel → Consola remota →
  **Registro**, tabla `consola_consultas`.
- Crear y revocar tokens también va a **Auditoría**.
- Las fechas de esas tablas están en UTC (3 horas más que Chile en horario
  de verano).

## Si algo no anda

| Mensaje | Qué pasa |
|---|---|
| `Sin token: correr scripts/labsim_token.sh` | No hay archivo: repetir el paso 4. |
| `HTTP 401: Token inválido, vencido o revocado` | Venció o se revocó: generar otro. |
| `HTTP 503: Falta aplicar schema.sql` | Backend recién desplegado: Base de datos → Aplicar schema.sql. |
| `HTTP 422: ...` | El SQL falló; el mensaje es el de SQLite. Un `script` que falla no deja nada a medias. |

## Piezas

- `labsim_backend/public/admin/consola.php`: la página del panel (solo admin
  completo).
- `labsim_backend/public/api/consola.php`: el endpoint (POST JSON,
  `Authorization: Bearer lsc_...`).
- `labsim_backend/src/Consola.php`: tokens (solo se guarda el sha256),
  ejecución y registro.
- `labsim_backend/sql/schema.sql`: tablas `consola_tokens` y
  `consola_consultas`.
- `scripts/consola.py`: el cliente (solo stdlib). `scripts/labsim_token.sh`:
  guarda el token.
