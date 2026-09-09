# Propuesta de rediseño de estilos — LabSim backend web

Fecha: 2026-09-06
Alcance: `labsim_backend/public/{admin,student,lti}` + `src/Layout.php`.

---

## 1. Diagnóstico (qué hay hoy)

Recorrido completo de las páginas admin/student/lti + medición:

| métrica | valor |
|---|---|
| archivos `.css` / `.scss` en el backend | **0** |
| bloques `<style>` inline (en `.php`) | 8 (uno por página que duplica reglas) |
| atributos `style="..."` inline dispersos | **280** repartidos en 17 archivos |
| páginas admin con más estilos inline | `courses.php` (58), `inbox_send.php` (38), `case_create.php` (35), `database.php` (26), `agenda.php` (26) |
| layouts distintos | 2 — `admin/_layout.php` y `student/_layout.php` con ~80% de reglas duplicadas |
| tokens de color (literales hex) únicos | ~25 (`#1a2744`, `#24345c`, `#1a1a1a`, `#f7f7f8`, `#eef0f4`, `#888`, `#555`, `#a33`, `#b00`, `#7a5b00`, `#fff3cd`, `#4a7dbd`…) |
| patrones repetidos verbatim | botón pequeño inline (`margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;`) **aparece 6+ veces**; "campo flex en fila" (`display:flex; gap:0.6rem; align-items:flex-end;`) **8+ veces**; "separador de sección" (`border-top:1px solid #e5e5e5; padding-top:0.6rem; margin-top:0.6rem;`) **15+ veces** |
| `font-size:0.8rem; color:#888` (textos de ayuda/ayuda pequeña) | repetido **40+ veces** |
| `input { width:100% }` global → obliga a usar `style="margin-top:0"` en cada botón de form inline | síntoma de ausencia de sistema de layout |

### Problemas concretos que esto causa

1. **Cambiar el color primario** (hoy `#1a2744`) requiere editar a mano ~30 archivos. Es casi seguro que se va a quedar alguno inconsistente.
2. **Cero responsive en admin** — el alumno abre `mis_pacientes.php` desde el celular (lo dice el comentario en `student/_layout.php`); el admin/docente también va a querer abrir `dashboard.php` desde el tablet del box. No hay `@media`, no hay colapso de tablas, no hay menú hamburguesa. Solo `student/_layout.php` tiene un breakpoint `40rem`.
3. **Cero accesibilidad**: no hay `focus-visible`, no hay contraste verificado, no hay `prefers-reduced-motion`, no hay `aria-*` semánticos en los toggles dropdown del nav (hechos con `:hover` CSS que no funcionan en touch).
4. **Dropdown nav roto en touch/tablet**: `nav-group:hover > .nav-dropdown { display:flex }` no abre en pantallas táctiles. Docentes en iPad no pueden navegar.
5. **Sin dark mode** — los logs de LLM y la página de `chat_detail` (chats largos) queman la vista del docente que los mira de noche.
6. **Tablas no scrolleables** — `agenda.php` tiene 853 líneas y una grilla grande; cualquier tabla ancha revienta el layout en pantallas chicas. `student/_layout.php` sí envuelve en `.table-wrap` con `overflow-x:auto`, pero `admin/_layout.php` no.
7. **Botones con tamaños caóticos** — el mismo botón "Quitar" aparece como `class="danger"` con 3 variantes de tamaño inline diferentes según el formulario.
8. **Mezcla dehelpers `class="error"` con `<p style="color:#b00;">`** — el `_layout` define `.error` y `.success`, pero la mitad de los mensajes de error inline usan hex literal.
9. **Layout duplicado** — `admin/_layout.php` y `student/_layout.php` redefinen `body`, `header`, `main`, `h1`, `table`, `th/td`, `.card`, `.error`. Si se cambia el radio de la card hay que tocar dos archivos.
10. **No hay sistema de formularios** — cada página reinventa `display:flex; gap:0.6rem; align-items:flex-end` para poner label + input + botón en una fila. Mismo patrón copiado en `courses.php`, `inbox_send.php`, `students.php`, `agenda.php`, etc.

---

## 2. Propuesta

#### 2.1 Extraer estilos a archivos `.css` servibles

Crear:
```
labsim_backend/public/admin/styles.css       (admin y lti)
labsim_backend/public/student/styles.css     (student y lti launch público)
labsim_backend/public/shared/tokens.css      (variables CSS, breakpoint helpers)
```

`_layout.php` deja de embebir `<style>` y hace:
```html
<link rel="stylesheet" href="styles.css?v=<?= filemtime(__DIR__.'/styles.css') ?>">
```
El `?v=` con `filemtime` evita cachear el CSS viejo entre deploys.

#### 2.2 Sistema de tokens (custom properties)

Reemplazar todos los literales hex por variables en `:root`:

```css
:root {
  --color-bg: #f7f7f8;
  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --color-muted: #6b7280;
  --color-faint: #9ca3af;
  --color-border: #e5e7eb;
  --color-border-strong: #cbd5e1;

  --color-primary: #1a2744;
  --color-primary-hover: #24345c;
  --color-primary-contrast: #ffffff;

  --color-success-bg: #e8f5e9;
  --color-success-text: #1b5e20;
  --color-danger: #a33;
  --color-danger-hover: #b5443e;
  --color-warn-bg: #fff3cd;
  --color-warn-text: #7a5b00;
  --color-info-border: #4a7dbd;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;

  --font-sans: system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: ui-monospace, "SF Mono", Consolas, monospace;

  --shadow-1: 0 1px 2px rgba(0,0,0,0.06);
  --shadow-2: 0 4px 10px rgba(0,0,0,0.12);
  --shadow-3: 0 8px 24px rgba(0,0,0,0.18);

  --bp-sm: 40rem;
  --bp-md: 56rem;
  --bp-lg: 72rem;
}
```

**Beneficio inmediato**: cambiar el primario en `:root` cambia toda la marca. Agregar dark mode es agregar un `@media (prefers-color-scheme: dark) :root { … }` y nada más.

#### 2.3 Utilidades para los patrones repetidos

Clases chiquitas que reemplazan los `style=""` inline más comunes:

```css
.muted        { color: var(--color-muted); }
.faint        { color: var(--color-faint); }
.help         { font-size: 0.8rem; color: var(--color-muted); margin-top: var(--space-1); }
.section-sep  { border-top: 1px solid var(--color-border); padding-top: var(--space-3); margin-top: var(--space-3); }
.row          { display: flex; gap: var(--space-3); align-items: flex-end; flex-wrap: wrap; }
.row > .grow  { flex: 1 1 12rem; }
.spacer       { flex: 1; }
.mono         { font-family: var(--font-mono); font-size: 0.85rem; word-break: break-all; }
.tag          { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; background: var(--color-border); color: var(--color-text); }
.tag-warn     { background: var(--color-warn-bg); color: var(--color-warn-text); }
.tag-success  { background: var(--color-success-bg); color: var(--color-success-text); }
```

Tarea de barrido: un sed/grep que reemplace los `style="font-size:0.8rem; color:#888; margin-top:0.4rem"` por `class="help"`, etc. Estimado: **~180 de los 280 atributos inline** desaparecen en este pase.

#### 2.4 Sistema de botones con variantes (no más hex inline)

```css
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: 0.4rem; padding: 0.5rem 1.1rem; margin-top: var(--space-4);
  font: inherit; font-weight: 500; line-height: 1.2;
  border: 1px solid transparent; border-radius: var(--radius-sm);
  background: var(--color-primary); color: var(--color-primary-contrast);
  cursor: pointer; transition: background 0.12s, border-color 0.12s;
}
.btn:hover  { background: var(--color-primary-hover); }
.btn:focus-visible { outline: 2px solid var(--color-primary-hover); outline-offset: 2px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn--secondary { background: var(--color-surface); color: var(--color-text); border-color: var(--color-border-strong); }
.btn--secondary:hover { background: var(--color-border); }

.btn--danger { background: var(--color-danger); }
.btn--danger:hover { background: var(--color-danger-hover); }

.btn--ghost { background: transparent; color: var(--color-text); }
.btn--ghost:hover { background: var(--color-border); }

.btn--sm { padding: 0.2rem 0.6rem; font-size: 0.8rem; margin-top: 0; }
.btn--xs { padding: 0.15rem 0.5rem; font-size: 0.72rem; margin-top: 0; }
.btn--block { display: flex; width: 100%; }
```

**Beneficio**: los 6+ botones "Quitar" que tienen `style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"` se vuelven `<button class="btn btn--danger btn--xs">`. Cero inline style.

#### 2.5 Formularios con layout propio (eliminar el `input { width:100% }` global)

```css
.field { display: block; margin-top: var(--space-3); }
.field > label, .field-label { display: block; font-weight: 600; font-size: 0.85rem; margin-bottom: var(--space-1); }
.input, .select, .textarea {
  width: 100%; padding: 0.5rem 0.6rem; font: inherit;
  border: 1px solid var(--color-border-strong); border-radius: var(--radius-sm);
  background: var(--color-surface); color: var(--color-text);
}
.input:focus-visible, .select:focus-visible, .textarea:focus-visible {
  outline: 2px solid var(--color-primary-hover); outline-offset: -1px; border-color: var(--color-primary);
}

.field-inline { display: inline-flex; align-items: center; gap: 0.4rem; margin: 0; font-weight: normal; }
.checkbox-list { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-5); margin-top: var(--space-2); }
.checkbox-list label { font-weight: normal; margin: 0; }
```

**Beneficio**: el botón primario ya no necesita `style="margin-top:0"` porque los forms ahora tienen `margin-top` propio en `.btn`, no heredado.

#### 2.6 Tablas responsivas y cards de datos

```css
.table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.table-wrap > table { min-width: 36rem; }

.table { width: 100%; border-collapse: collapse; background: var(--color-surface); margin: var(--space-4) 0; }
.table th, .table td { text-align: left; padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--color-border); font-size: 0.9rem; }
.table th { background: #eef0f4; font-weight: 600; }
.table tr.clickable { cursor: pointer; }
.table tr.clickable:hover { background: #f3f5fa; }
.table .num { text-align: right; font-variant-numeric: tabular-nums; }
.table .actions { text-align: right; white-space: nowrap; }
```

**Beneficio**: tabla ancha (roster de 200 alumnos en `courses.php`) scrollea horizontalmente sin romper el layout en celular. Hoy desborda.

#### 2.7 Nav admin funcional en touch (reemplazar hover por click)

El nav actual `nav-group:hover .nav-dropdown { display:flex }` no funciona en iPad/celular. Dos opciones, recomiendo la segunda:

1. Mínimo cambio: agregar `<details><summary>…</summary>…</details>` puro HTML. Funciona en touch, sin JS, accesible por teclado. Cada dropdown se vuelve un `<details class="nav-group">`.
2. Más ambicioso: agregar un toggle hamburguesa en `<40rem` que muestre los grupos como accordion vertical.

Recomiendo (1): cero JS nuevo, accesibilidad gratis, replica la estética actual.

#### 2.8 Dark mode

Agregar al final de `tokens.css`:
```css
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #0f172a;
    --color-surface: #1e293b;
    --color-text: #e2e8f0;
    --color-muted: #94a3b8;
    --color-faint: #64748b;
    --color-border: #334155;
    --color-border-strong: #475569;
    --color-primary: #4f7cb8;
    --color-primary-hover: #6b96d3;
    /* …etc */
  }
}
:root[data-theme="dark"] { /* mismo override que arriba, gana sobre light */ }
:root[data-theme="light"] { /* gana sobre system */ }
```

Botón toggle en el header (tres estados: sistema / claro / oscuro), guardado en `localStorage.theme` y aplicado vía `document.documentElement.dataset.theme` antes del primer render (script inline en `<head>` para evitar FOUC).

#### 2.9 Unificar admin + student en un solo sistema

`student/_layout.php` y `admin/_layout.php` redefinen las mismas reglas básicas. Propuesta:

- Mover la base común a `public/shared/base.css` (reset, body, header simple, main, h1, `.card`, `.error`, `.success`, `.mono`).
- `admin/styles.css` extiende la base con nav dropdown, tablas de gestión, badges, etc.
- `student/styles.css` extiende la base con el banner "viendo como", la timeline de `dashboard_report.php`, y los overrides responsive.
- `_layout.php` de cada uno enlaza su CSS específico + el base compartido.

**Beneficio**: un solo cambio de marca, pero cada vista mantiene sus particularidades. Reduce ~60 líneas duplicadas.

#### 2.10 Accesibilidad mínima viable

Sin esto, el rediseño es cosmético:

- `:focus-visible` en todos los interactivos (botones, links, inputs).
- Contraste verificado: `--color-muted` sobre `--color-bg` debe pasar WCAG AA (4.5:1). El `#888` actual sobre `#f7f7f8` está justo en 3.5:1 — falla. Cambiar a `#6b7280` (4.6:1) ✓.
- `<button>` solo cuando es acción, `<a>` solo cuando es navegación — revisar `courses.php` línea ~332 donde un "Quitar" es `<button>` dentro de `<form>` (correcto), pero los "Ver" son `<a>` (correcto). Bien.
- `aria-current="page"` en el link activo del nav (agregar marca del item actual via PHP comparando `basename($_SERVER['PHP_SELF'])`).
- `<label>` siempre asociado al input por `for=` (algunos en `courses.php` envuelven el input dentro del label, que también es válido, pero mezclar es confuso).
- `prefers-reduced-motion: reduce` mata las transitions.

#### 2.11 Componentes nuevos que faltan y se repiten

Identifiqué estos patrones que justifican su propio componente CSS:

- **`.toolbar`** — fila de botones arriba de una tabla/buscardor. Aparece en `courses.php` (búsqueda de roster), `agenda.php` (filtros), `patients.php`, `audit.php`.
- **`.empty-state`** — `Ningún curso creado todavía.`, `Sin docentes asignados todavía.`, `Todos los alumnos activos ya están en este curso.` — texto gris centrado, debería ser `<p class="empty-state">`.
- **`.callout callout--info|warn|danger`** — para los banners (`Vincular curso de Moodle`, `Viendo como … modo docente`).
- **`.timeline`** y `.tl-seg` — solo en `dashboard.php`, vale la pena dejarlo en el CSS de admin si lo usa otra página (sino inline).
- **`.dropdown`** genérico (no nav) — para selects enriquecidos si más adelante se necesita.

#### 2.12 Plan de ejecución por fases

**Fase 1 — cimientos (1 sesión, sin tocar páginas)**
- Crear `public/shared/tokens.css` con todas las variables.
- Crear `public/shared/base.css` con reset, body, header, main, h1-h3, links, `.card`, `.error`, `.success`, `.mono`.
- Crear `public/admin/styles.css` y `public/student/styles.css` que importen la base y extiendan.
- Modificar ambos `_layout.php` para enlazar el CSS en vez de embeber `<style>`.
- Verificar visualmente que admin/login, admin/dashboard, student/mis_pacientes, lti/launch se ven **idénticos** a como estaban. Cero regresión.

**Fase 2 — sistema de botones + forms (2-3 sesiones)**
- Agregar `.btn`, `.btn--*`, `.field`, `.input`, `.select`, `.field-inline`.
- Pasar las páginas más usadas (login, dashboard, courses, patients) a las nuevas clases. Aquí se eliminan ~80 de los 280 inline styles.

**Fase 3 — tablas + responsive (1 sesión)**
- `.table`, `.table-wrap`, breakpoints.
- Envolver las tablas existentes en `.table-wrap`.
- Probar en viewport 360px.

**Fase 4 — utilidades + secciones repetidas (1 sesión)**
- `.help`, `.muted`, `.section-sep`, `.row`, `.tag`. Barrido global con sed/grep + verificación manual.
- Aquí se eliminan otros ~100 inline styles.

**Fase 5 — nav accesible (½ sesión)**
- `<details>` para dropdowns. Probar en iPad/celular.

**Fase 6 — dark mode (½ sesión)**
- Override de tokens + script anti-FOUC en `<head>`.

**Fase 7 — accesibilidad final + auditoría (½ sesión)**
- focus-visible, aria-current, prefers-reduced-motion, contraste verificado con DevTools.

**Total**: ~6-7 sesiones, ataque sin riesgo de regresión si se hace fase por fase con captura visual antes/después.

#### 2.13 Lo que **NO** propongo (para evitar scope creep)

- Reescribir a un framework CSS (Tailwind, Bootstrap). Ya están en el stack PHP plano; meter build step para CSS es desproporcionado.
- Migrar las páginas a un SPA. El backend es servidor-rendered y debe seguir así.
- Cambiar la arquitectura de los `_layout.php` (helpers `admin_header/admin_footer`). Funcionan bien, solo se les quita el `<style>`.
- Tocar los `api/*.php` — esos devuelven JSON, no HTML, no tienen estilos.

#### 2.14 Riesgos y mitigación

| riesgo | mitigación |
|---|---|
| Regresión visual al extraer CSS | Captura con `chromium --screenshot` antes/después de cada fase. Comparar píxel a píxel en login + dashboard. |
| Cache del navegador con CSS viejo | `?v=filemtime()` en el `<link>`. |
| Mezcla temporal de clases nuevas y viejas inline | No prohibirlas: el lint/barrido puede ir por archivo. Cada página puede migrarse cuando se toca. |
| Pérdida del look "funcional/sobrio" actual | Mantener la paleta base (gris/azul oscuro), solo sistematizar. |
| Tiempo de las páginas que aún no se tocan | Las páginas no migradas siguen funcionando con `style=""` inline mientras conviven con las nuevas clases en otras. |

---

## 3. TL;DR

**Hoy**: 0 archivos CSS, 280 atributos `style=""` inline, 25 colores hex literales, dos layouts con 80% duplicado, sin responsive en admin, sin dark mode, sin accesibilidad de foco, nav roto en touch.

**Propuesta**: 3 archivos CSS + tokens en `:root` + clases utilitarias + sistema de botones/forms/tablas + dark mode + nav con `<details>`. Plan por fases sin regresión. Resultado: eliminar ~80% de los estilos inline, hacer la UI mantenible, usable en celular/tablet, y agradable de noche.

**Esfuerzo**: ~6-7 sesiones de ~2-3h cada una. **Impacto**: todo lo que vea un docente o admin en el navegador. Cualquier ajuste futuro de marca pasa de "editar 30 archivos" a "cambiar una variable".