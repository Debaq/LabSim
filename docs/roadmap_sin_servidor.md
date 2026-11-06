# Roadmap: el práctico cuando el hosting se cae

Plan futuro, sin fecha. Nace de la caída de HostArmada del 2026-10-30: no
respondían sus servidores de nombres (ns1/ns2.dalult3.hostarmada.net), el
dominio tmeduca.org daba SERVFAIL en todo el mundo y el panel de control
tampoco abría. Con eso no hay práctico.

## Qué falla hoy sin servidor

- **Iniciar sesión**: necesita el backend; nadie entra, ni alumnos ni
  docente. Es a propósito.
- **Agenda, abrir y cerrar la atención, chat con el paciente, secretaria**:
  todo pasa por el backend. El chat va por `api/llm_chat.php`, así que aunque
  haya internet, sin nuestro servidor no hay LLM.
- **Kiosko**: si el backend no contesta, la lista de versiones se pide a
  GitHub (`core/actualizacion_kiosko.py`). No probado con una caída real.

## Qué sobrevive

- Una atención ya abierta sigue si se corta la red: los informes quedan
  respaldados en el equipo (`core/respaldo_informes.py`) y suben cuando
  vuelve. El cierre de la atención sí necesita red.
- El modo invitado (sin cuenta): catálogo y otoscopías, cero API. Sirve para
  practicar, pero no queda registro ni hay chat.

## Opciones, de menor a mayor esfuerzo

1. **DNS fuera de HostArmada** (Cloudflare, gratis). Lo hace él en el
   registrador. Cubre la caída de los servidores de nombres solos; la del
   2026-10-30 no, porque cayó todo el proveedor.
2. **Plan B docente, sin código**: si el hosting cae en pleno práctico, se
   trabaja en modo invitado con los pacientes del libro. Se pierde el
   registro y la nota del día. Va escrito para los docentes.
3. **Práctico sin servidor** (lo que de verdad resuelve el caso):
   - Antes del práctico, cada PC del laboratorio baja los casos y la agenda
     del día (en parte ya lo hace la sincronización).
   - Entrada sin red con una **llave del práctico** que genera el docente,
     en vez del login de cada alumno (en el kiosko los PC son compartidos).
   - Se atiende normal, todo queda en el equipo y sube solo cuando vuelve el
     servidor.
   - Sin chat (necesita el LLM): en su lugar, la anamnesis escrita del caso,
     como en el modo invitado.
   Varios días de trabajo; toca login, agenda y cierre de atención.
4. **Servidor en el laboratorio**: un PC del lab corre el backend como espejo
   y la app lo usa si el hosting no responde. Lo más robusto, pero obliga a
   reconciliar dos bases SQLite. Alto riesgo; no recomendado.

Recomendación: 1 cuando se pueda, 2 como protocolo escrito, 3 diseñado con
calma (comparte piezas con `docs/roadmap_practica_libro.md`: casos del libro
sin red y anamnesis en vez de chat).

## Servidor lento o intermitente (2026-11-06)

Distinto de la caída del 30-10: el 06-11, en pleno práctico, el servidor
contestaba pero mal. Medido desde fuera del laboratorio, 12:30-12:40 UTC:
50-83 % de paquetes perdidos hacia 216.183.246.223, conexión TCP de 1-7 s
(normal 0,24), handshake TLS de 3-17 s, y la mitad de los pedidos con
timeout o conexión cortada. El traceroute llegaba limpio hasta
dalult3.hostarmada.net: la pérdida es del servidor. PHP respondía en 0 ms.
Los alumnos veían "problema de red"; algunos entraban y otros no.

### Por qué la app no lo aguanta

- **Un solo intento por pedido.** `backend/client.py` no reintenta nada: un
  paquete perdido en el handshake = error para el alumno.
- **Timeout de 10 s para todo** (`DEFAULT_TIMEOUT`), y con handshakes de
  hasta 17 s muchos pedidos mueren antes de empezar.
- **Abrir la atención encadena tres pedidos**, y tienen que salir los tres:
  bajada completa del estado (`estado_completo`), casos, y la escritura de
  la agenda para marcar "atendiendo". Si cada pedido sale la mitad de las
  veces, la atención abre ~1 de cada 8 intentos. Además corre en el hilo de
  la ventana: se congela mientras espera.
- **La bajada completa pesa** (hasta ~1,4 MB con el admin) y con pérdida de
  paquetes es lo primero que se corta, aunque la sincronización de cada
  60 s ya tenga casi todo en el equipo.
- **El cierre y el chat** fallan al primer error, sin reintentar solos.

### Plan, de más barato a más caro

1. **Reintentos en el cliente** — HECHO 2026-11-06, distinto de lo
   planeado tras medir: lo caro era abrir la conexión (5-10 s), no el
   pedido (0,2 s por una conexión abierta), y el servidor la cierra entre
   10 y 30 s sin uso. Quedó así en `backend/client.py`: una sola Session
   para toda la app (antes una por módulo), un latido HEAD a
   `/css/base.css` cada 8 s que la mantiene abierta, conexión 15 s +
   lectura 30 s, y se insiste por tiempo (45 s), no por intentos. Sin
   internet del todo (DNS, red inalcanzable) falla al tiro. Los tickets
   manuales llevan una prueba de red del equipo (`core/prueba_red.py`).
   En la ventana de ingreso (usuario y contraseña) está "Probar conexión":
   le dice al docente qué revisar y deja mandar un reporte sin haber
   entrado (ticket.php lo acepta sin sesión, marcado "[Sin sesión]"). El
   reporte que no sale queda en el equipo (`core/tickets_pendientes.py`)
   y se envía solo al arrancar o al iniciar sesión.
   Lo que sigue es lo que se había planeado:
   - `HTTPAdapter` con `urllib3.Retry` en `_SesionHttp`: hasta 4
     reintentos con espera creciente (0,5-1-2-4 s) en errores de conexión,
     502/503/504 y timeouts de conexión. Los GET se reintentan siempre; los
     POST solo cuando el pedido no alcanzó a salir (falla al conectar), así
     no se duplica nada.
   - Timeout separado: `(conectar 20 s, leer 30 s)` en lugar de 10 s para
     todo. El chat y el cierre mantienen su lectura larga.
   - La conexión se mantiene abierta entre pedidos (la `Session` ya lo hace
     si el servidor deja); se paga el handshake una vez, no por pedido.
   - Con esto, un 50 % de pérdida pasa de 1 en 8 atenciones a casi todas.
2. **Abrir la atención con lo que ya está en el equipo** — HECHO
   2026-11-06 junto con la 3: `helpers.estado_en_memoria()` (lo que bajó
   Shedule() y mantiene el sync) en vez de bajar todo, y "atendiendo" a la
   cola `core/acciones_pendientes.py`. Sin estado en memoria (la app recién
   abierta sin red) todavía no se puede. Lo planeado era:
   - El caso y la cita salen de la caché que deja la sincronización; si la
     caché es reciente (< 5 min) no se baja el estado completo.
   - Marcar "atendiendo" va a una cola local (como `log_queue`) que sube
     en segundo plano con reintentos; la atención abre al tiro.
   - Si no hay caché del caso, recién ahí se baja, y en segundo plano con
     "Cargando el paciente…" en vez de congelar la ventana.
   - Cuidado: el choque "ya lo está atendiendo otro" se resuelve en el
     servidor al subir; si choca, avisar sin perder lo hecho.
3. **Cierre de atención en cola** — HECHO 2026-11-06. Si lo que falla es
   la red (no un rechazo del servidor), la atención se cierra en el equipo
   y "atendido" va a la cola, que primero sube los informes de esa cita
   (con la atención cerrada el servidor ya no los acepta). La agenda
   muestra lo encolado (`helpers.con_pendientes`) y no deja reabrir una
   cerrada sin red. Cada acción guarda el token de quien la hizo: si otro
   alumno entra antes de que vuelva la red, lo del anterior sale con su
   token (cabecera X-LabSim-Ajeno: su 401 no cierra la sesión del que
   está). Limitación: hora_real la pone el servidor al recibirla. Además,
   al entrar con red, la práctica libre vigente se guarda en el equipo y
   "Practicar sin cuenta" la usa (`invitado.descargar_catalogo`), más
   nueva que el catálogo que viene con la versión. Lo planeado era: Los informes ya se respaldan en el
   equipo; el cierre también queda encolado y sube solo cuando hay red, con
   "Cerrada, se está enviando" en vez de "No se pudo cerrar". El alumno
   puede pasar al siguiente paciente.
4. **Chat que reintenta.** Si el mensaje no llega, se reintenta solo 2 veces
   y el paciente "se queda pensando"; si sigue sin red, se deja el mensaje en
   la caja con un botón Reenviar, sin perderlo.
5. **Indicador de conexión en vez de modales.** Un punto en la barra de
   estado (verde / amarillo lento / rojo sin red) con lo que mide
   `core/tiempos.py`; los avisos modales solo cuando algo de verdad se
   perdió. Así el docente ve de un vistazo qué PC está sufriendo.
6. **Menos bytes por pedido** (lado servidor). Gzip en las respuestas
   JSON grandes y que la app use el delta de `sync.php` también al abrir.
   Con pérdida de paquetes, menos bytes = menos cortes.

Fuera de la app: ticket a HostArmada (06-11; contestaron que su servidor
estaba bien y que era el proveedor de internet) y, si se repite,
evaluar cambiar de hosting; eso lo decide él.

Recomendación: 1 ya (resuelve la mayor parte del 06-11), 2 y 3 juntos
(comparten la cola), 4 y 5 después, 6 cuando se mida cuánto pesa cada
pedido en terreno.
