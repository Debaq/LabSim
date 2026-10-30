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
