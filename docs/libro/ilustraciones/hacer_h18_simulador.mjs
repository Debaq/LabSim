#!/usr/bin/env node
// Figuras de H18 (vHIT) hechas con el motor de trainHIT, sin su interfaz.
//
//   h18-impulsos.svg   impulsos superpuestos del paciente de ejemplo: derecho sano, izquierdo con déficit
//   h18-ganancias.svg  A: ganancia contra velocidad pico; B: los mismos impulsos con área, 60 ms y picos
//   h18-ralp.svg       A: los seis canales; B y C: el plano RALP de una neuritis derecha
//   h18-rechazos.svg   un impulso rechazado por parpadeo en la ventana y otro por lento
//   h18-muestreo.svg   el mismo impulso con sacada encubierta a 200 muestras/s y a 30 cuadros/s (simHit)
//
// trainHIT (~/Escritorio/Proyectos/trainhit) NO se toca: se importan sus módulos de js/ en modo de
// solo lectura y se hace lo mismo que la app al cargar los ejemplos (`cargaEjemplos` de app.js):
// la calibración de ejemplo pasa por `fitParallax`, cada pulso sintético por `procesaCrudo` y el
// resumen por `resumenLado`. El paciente simulado de B y C es el perfil «neuritis-der» de
// js/simulacion.js puesto sobre pulsos sintéticos sanos (como lo hacen los tests de trainHIT), en
// vez de sobre los impulsos de un compañero. Nada se dibuja a mano: las curvas, las sacadas, los
// rechazos y las ganancias son los del motor. Son cifras del modelo, no normas.
//
// h18-muestreo.svg sale del modelo de simHit (~/Escritorio/Proyectos/simHit, tampoco se toca): el
// paciente virtual sin sensor de app/src/lib/simulator.svelte.ts (`tick`): cabeza gaussiana, ojo =
// ganancia × cabeza con 7 ms de retardo y la sacada encubierta como otra gaussiana. Sus constantes
// (IMP_PEAK_OFFSET, IMP_SIGMA, SACCADE_SIGMA, COVERT_OFFSET y la tasa del firmware) se leen del código
// fuente, no se copian; ese modelo no es un módulo importable (Svelte), así que la fórmula se rehace
// aquí sin el ruido aleatorio. Se muestrea igual a 200 Hz (las gafas) y a 30 Hz (una cámara web).
//
// Uso:  node docs/libro/ilustraciones/hacer_h18_simulador.mjs   (TRAINHIT=<ruta> para otra copia)
// cap. 24 importa `panelesLado` y `pulsosDe` para su caso bilateral (hacer_cap24_simulador.mjs).

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const AQUI = dirname(fileURLToPath(import.meta.url));
const JS = resolve(process.env.TRAINHIT ?? `${homedir()}/Escritorio/Proyectos/trainhit`, 'js');
const geom = await import(`${JS}/geom.js`);
const { procesaCrudo } = await import(`${JS}/pipeline.js`);
const A = await import(`${JS}/analysis.js`);
const ej = await import(`${JS}/ejemplo.js`);
const sim = await import(`${JS}/simulacion.js`);

// ── estilo de la casa (el de hacer_h17.py)
const TINTA = '#24101a', TENUE = '#8a8a90', GRILLA = '#e7e5e0', FUERTE = '#cfccc5';
const CABEZA = '#2a6fc2', OJO = '#c0571c', AVISO = '#c62f3a', OK = '#21796c', ENCUBIERTA = '#7b4bb7';
const DER = '#21796c', IZQ = '#b3407a';
const F = `font-family="'Plus Jakarta Sans', sans-serif"`;
const ESCALA = 1.2;
const coma = (x, d = 2) => x.toFixed(d).replace('.', ',');

export class Lienzo {
  constructor(w, h) { this.w = w; this.h = h; this.out = []; }
  t(x, y, s, size = 9, color = TINTA, anchor = 'middle', peso = 400) {
    this.out.push(`<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" ${F} font-size="${(size * ESCALA).toFixed(1)}" fill="${color}" text-anchor="${anchor}" font-weight="${peso}">${s}</text>`);
  }
  l(x1, y1, x2, y2, color = TINTA, w = 1, dash = null) {
    const d = dash ? ` stroke-dasharray="${dash}"` : '';
    this.out.push(`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${color}" stroke-width="${w}"${d}/>`);
  }
  poli(pts, color, w = 2, op = 1, dash = null) {
    const d = dash ? ` stroke-dasharray="${dash}"` : '';
    this.out.push(`<polyline points="${pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="${w}" stroke-opacity="${op}" stroke-linejoin="round" stroke-linecap="round"${d}/>`);
  }
  rect(x, y, w, h, fill = 'none', stroke = 'none', sw = 1, dash = null, op = 1, rx = 0) {
    const d = dash ? ` stroke-dasharray="${dash}"` : '';
    this.out.push(`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" rx="${rx}" fill="${fill}" fill-opacity="${op}" stroke="${stroke}" stroke-width="${sw}"${d}/>`);
  }
  punto(x, y, color, r = 3.6, hueco = false) {
    this.out.push(hueco
      ? `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="#fff" stroke="${color}" stroke-width="1.4"/>`
      : `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="${color}"/>`);
  }
  triangulo(x, y, color, s = 5) { // apunta hacia abajo, con la punta en (x, y)
    this.out.push(`<polygon points="${(x - s).toFixed(1)},${(y - 1.6 * s).toFixed(1)} ${(x + s).toFixed(1)},${(y - 1.6 * s).toFixed(1)} ${x.toFixed(1)},${y.toFixed(1)}" fill="${color}"/>`);
  }
  crudo(s) { this.out.push(s); }
  guardar(nombre) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${this.w} ${this.h}" width="${this.w}" height="${this.h}"><rect width="${this.w}" height="${this.h}" fill="#fff"/>${this.out.join('')}</svg>`;
    writeFileSync(resolve(AQUI, nombre), svg, 'utf8');
    console.log(nombre);
  }
}

export class Ejes {
  constructor(c, px, py, w, h, x0, x1, y0, y1) { Object.assign(this, { c, px, py, w, h, x0, x1, y0, y1 }); }
  X(x) { return this.px + ((x - this.x0) / (this.x1 - this.x0)) * this.w; }
  Y(y) { return this.py + this.h - ((y - this.y0) / (this.y1 - this.y0)) * this.h; }
  marco(xt, yt, xlab, ylab = null, fmt = (v) => `${v}`) {
    const c = this.c;
    for (const y of yt) {
      c.l(this.px, this.Y(y), this.px + this.w, this.Y(y), GRILLA, 1);
      c.t(this.px - 5, this.Y(y) + 3, fmt(y), 7.5, TENUE, 'end');
    }
    for (const x of xt) {
      c.l(this.X(x), this.py + this.h, this.X(x), this.py + this.h + 3, TENUE, 1);
      c.t(this.X(x), this.py + this.h + 13, `${x}`, 7.5, TENUE);
    }
    c.l(this.px, this.py + this.h, this.px + this.w, this.py + this.h, FUERTE, 1);
    c.l(this.px, this.py, this.px, this.py + this.h, FUERTE, 1);
    if (xlab) c.t(this.px + this.w / 2, this.py + this.h + 26, xlab, 8, TENUE);
    if (ylab) c.t(this.px - 30, this.py - 8, ylab, 8, TENUE, 'start');
  }
  dentro(x) { return x >= this.x0 && x <= this.x1; }
}

// ── el motor de trainHIT
const DERIV = { windowMs: 50, degree: 2 }; // las perillas de fábrica (index.html)

export function modeloEjemplo() {
  const m = new geom.EyeModel();
  const fit = geom.fitParallax(ej.calibracionDeEjemplo(), m.radiusMm);
  m.kParallax = fit?.acceptable ? fit.kParallax : ej.K_EJEMPLO;
  m.calibrated = true;
  return m;
}

/** Los pulsos de un caso, como `cargaEjemplos(caso)` de app.js (semillas 1… o 100…). */
export function pulsosDe(caso = null) {
  const m = modeloEjemplo();
  const s0 = caso ? 100 : 1;
  return ej.pulsosDe(caso).map((p, i) => {
    const { crudo, tTrigger } = ej.crudoDeEjemplo(p, s0 + i);
    return procesaCrudo(crudo, tTrigger, m, DERIV, A.CONFIG);
  }).filter(Boolean);
}

/** Pulsos sintéticos sanos con un perfil del paciente simulado encima, en un plano. */
function pulsosSimulados(perfil, plano, n = 4) {
  const m = modeloEjemplo();
  const s0 = { lateral: 0, ralp: 20, larp: 40 }[plano] ?? 60;
  const out = [];
  const picos = [175, 205, 165, 190, 215, 180];
  for (let i = 0; i < 2 * n; i++) {
    const lado = i % 2 ? 'izquierda' : 'derecha';
    const { crudo, tTrigger } = ej.crudoDeEjemplo({ lado, pico: picos[i % picos.length], ganancia: 0.98 }, 300 + s0 + i);
    const params = sim.parametrosPulso(perfil, lado, 500 + s0 + i, plano);
    const t = procesaCrudo(sim.simulaCrudo(crudo, tTrigger, params, m), tTrigger, m, DERIV, A.CONFIG);
    if (t) out.push(t);
  }
  return out;
}

/** Cabeza y ojo invertido, con el signo del lado: la cabeza va hacia arriba (como `curvas` de figure1_datos.mjs). */
function curvas(t) {
  const s = A.sideSign(t.side);
  return t.samples.map((m) => ({ t: m.tMs - t.tOnsetMs, cabeza: m.headVel * s, ojo: (m.headVel - m.gazeVel) * s, blink: m.blink }));
}

function trazaPulso(c, e, t, { op = 0.8, w = 1.4, colCab = CABEZA, colOjo = OJO, marcas = true } = {}) {
  const cv = curvas(t).filter((p) => e.dentro(p.t));
  c.poli(cv.map((p) => [e.X(p.t), e.Y(p.cabeza)]), colCab, w, op);
  c.poli(cv.map((p) => [e.X(p.t), e.Y(p.ojo)]), colOjo, w, op);
  if (!marcas) return;
  for (const s of t.sacadas ?? []) {
    const x = s.tPicoMs - t.tOnsetMs;
    if (!e.dentro(x)) continue;
    const yOjo = Math.max(...cv.filter((p) => Math.abs(p.t - x) < 20).map((p) => p.ojo));
    c.triangulo(e.X(x), e.Y(yOjo) - 4, s.tipo === 'encubierta' ? ENCUBIERTA : AVISO, 4.2);
  }
}

/** Un panel de impulsos superpuestos de un lado (o de un canal), con su ganancia debajo. */
export function panelLado(c, px, py, w, h, trials, lado, titulo, { corte = A.CONFIG.gainNormalMin, ylab = true, x1 = 500, angosto = false } = {}) {
  const e = new Ejes(c, px, py, w, h, -100, x1, -40, 300);
  c.t(px, py - 18, titulo, 9.5, TINTA, 'start', 700);
  e.marco([0, 100, 200, 300, 400, 500].filter((x) => x <= x1), [0, 100, 200, 300], 'tiempo desde el inicio del impulso (ms)', ylab ? '°/s' : null);
  c.l(e.X(-100), e.Y(0), e.X(x1), e.Y(0), FUERTE, 1);
  const del = trials.filter((t) => t.side === lado && !t.rejected);
  for (const t of del) trazaPulso(c, e, t);
  const r = A.resumenLado(trials, lado);
  const rech = trials.filter((t) => t.side === lado && t.rejected).length;
  const col = r.media >= corte ? OK : AVISO;
  c.t(px, py + h + 50, `ganancia ${coma(r.media)} ± ${coma(r.de)}`, 11, col, 'start', 700);
  const n = `${r.n} aceptados${rech ? ` · ${rech} rechazados` : ''}`;
  if (angosto) c.t(px, py + h + 64, n, 8, TENUE, 'start');
  else c.t(px + w, py + h + 50, n, 8, TENUE, 'end');
  return { e, r };
}

function leyenda(c, x, y, conEncubierta = true) {
  c.l(x, y - 3, x + 22, y - 3, CABEZA, 2.4); c.t(x + 28, y, 'cabeza', 8.5, TINTA, 'start');
  c.l(x + 88, y - 3, x + 110, y - 3, OJO, 2.4); c.t(x + 116, y, 'ojo (invertido)', 8.5, TINTA, 'start');
  let k = x + 220;
  if (conEncubierta) { c.triangulo(k + 5, y + 1, ENCUBIERTA, 4.2); c.t(k + 15, y, 'sacada encubierta', 8.5, TINTA, 'start'); k += 135; }
  c.triangulo(k + 5, y + 1, AVISO, 4.2); c.t(k + 15, y, 'sacada manifiesta', 8.5, TINTA, 'start');
}

/** Los dos lados del plano lateral, uno junto al otro. */
export function panelesLado(trials, nombre, titulo, conEncubierta = true) {
  const c = new Lienzo(720, 340);
  c.t(14, 18, titulo, 10, TINTA, 'start', 700);
  const ri = panelLado(c, 52, 66, 300, 180, trials, 'derecha', 'Impulsos hacia la derecha');
  const rd = panelLado(c, 404, 66, 300, 180, trials, 'izquierda', 'Impulsos hacia la izquierda', { ylab: false });
  const asim = A.asimetria(ri.r.media, rd.r.media);
  c.t(704, 18, `asimetría ${Math.abs(asim).toFixed(0)} %`, 9, TINTA, 'end', 700);
  leyenda(c, 52, 332, conEncubierta);
  c.guardar(nombre);
  return { der: ri.r, izq: rd.r, asim };
}

// ── figuras
function impulsos() {
  const tr = pulsosDe(null);
  const r = panelesLado(tr, 'h18-impulsos.svg', 'Canal lateral derecho sano, izquierdo con déficit');
  console.log('  der', r.der, 'izq', r.izq, 'asim', r.asim.toFixed(1));
  return tr;
}

function ganancias(tr) {
  const c = new Lienzo(720, 300);
  c.t(14, 18, 'Los mismos impulsos, tres maneras de calcular la ganancia', 10, TINTA, 'start', 700);
  // A: ganancia de área contra velocidad pico
  const e = new Ejes(c, 52, 66, 260, 170, 50, 300, 0, 1.4);
  c.t(52, 48, 'A · Ganancia (área) y velocidad de la cabeza', 9.5, TINTA, 'start', 700);
  e.marco([50, 100, 150, 200, 250, 300], [0, 0.4, 0.8, 1.2], 'velocidad pico de la cabeza (°/s)', 'ganancia', (v) => coma(v, 1));
  c.rect(e.X(A.CONFIG.accept.peakMinDegS), e.py, e.X(300) - e.X(A.CONFIG.accept.peakMinDegS), e.h, OK, 'none', 0, null, 0.06);
  c.l(e.X(50), e.Y(A.CONFIG.gainNormalMin), e.X(300), e.Y(A.CONFIG.gainNormalMin), TENUE, 1.2, '5 3');
  c.t(e.X(300) - 2, e.Y(A.CONFIG.gainNormalMin) - 4, 'corte 0,80', 7.5, TENUE, 'end');
  c.t(e.X(A.CONFIG.accept.peakMinDegS) + 3, e.py + 10, 'velocidad suficiente', 7.5, OK, 'start');
  for (const t of tr) {
    if (t.gain === null) continue;
    c.punto(e.X(t.peakHeadDegS), e.Y(t.gain), t.side === 'derecha' ? DER : IZQ, 4, Boolean(t.rejected));
  }
  c.punto(60, 272, DER, 4); c.t(68, 275, 'derecha', 8.5, TINTA, 'start');
  c.punto(130, 272, IZQ, 4); c.t(138, 275, 'izquierda', 8.5, TINTA, 'start');
  c.punto(205, 272, TENUE, 4, true); c.t(213, 275, 'rechazado', 8.5, TINTA, 'start');
  // B: área, 60 ms y picos sobre los mismos impulsos
  const metodos = [['área', (t) => t.gains.area], ['60 ms', (t) => t.gains.instant60ms], ['picos', (t) => t.gains.peak]];
  const b = new Ejes(c, 440, 66, 250, 170, 0, 1.2, 0, 3);
  c.t(370, 48, 'B · Media de cada lado según el método', 9.5, TINTA, 'start', 700);
  for (const g of [0, 0.4, 0.8, 1.2]) {
    c.l(b.X(g), b.py, b.X(g), b.py + b.h, GRILLA, 1);
    c.t(b.X(g), b.py + b.h + 13, coma(g, 1), 7.5, TENUE);
  }
  c.l(b.px, b.py + b.h, b.px + b.w, b.py + b.h, FUERTE, 1);
  c.t(b.px + b.w / 2, b.py + b.h + 26, 'ganancia media', 8, TENUE);
  c.l(b.X(0.8), b.py, b.X(0.8), b.py + b.h, TENUE, 1.2, '5 3');
  const filas = {};
  metodos.forEach(([nom, f], k) => {
    const y = b.py + 30 + k * 55;
    c.t(b.px - 12, y + 4, nom, 9.5, TINTA, 'end', 700);
    const rd = A.resumenLado(tr, 'derecha', f), ri = A.resumenLado(tr, 'izquierda', f);
    filas[nom] = [rd.media, ri.media];
    c.l(b.X(Math.min(rd.media, ri.media)), y, b.X(Math.max(rd.media, ri.media)), y, FUERTE, 2);
    c.punto(b.X(rd.media), y, DER, 5);
    c.punto(b.X(ri.media), y, IZQ, 5);
    c.t(b.X(rd.media), y - 9, coma(rd.media), 8, DER, 'middle', 700);
    c.t(b.X(ri.media), y + 18, coma(ri.media), 8, IZQ, 'middle', 700);
  });
  c.guardar('h18-ganancias.svg');
  console.log('  ', filas);
}

function ralp() {
  const perfil = 'neuritis-der';
  const lat = pulsosSimulados(perfil, 'lateral');
  const ra = pulsosSimulados(perfil, 'ralp');
  const la = pulsosSimulados(perfil, 'larp');
  const g = (trs, lado) => A.resumenLado(trs, lado);
  const canales = {
    'anterior izq.': [g(la, 'izquierda'), 'v'], 'anterior der.': [g(ra, 'derecha'), 'v'],
    'lateral izq.': [g(lat, 'izquierda'), 'l'], 'lateral der.': [g(lat, 'derecha'), 'l'],
    'posterior izq.': [g(ra, 'izquierda'), 'v'], 'posterior der.': [g(la, 'derecha'), 'v'],
  };
  const c = new Lienzo(720, 330);
  c.t(14, 18, 'Neuritis derecha (rama superior): los seis canales y el plano RALP', 10, TINTA, 'start', 700);
  // A: la cabeza vista desde arriba
  c.t(14, 48, 'A · Los seis canales', 9.5, TINTA, 'start', 700);
  const cx = 120, cy = 178;
  c.crudo(`<ellipse cx="${cx}" cy="${cy}" rx="34" ry="42" fill="#fff" stroke="${TINTA}" stroke-width="1.4"/>`);
  c.crudo(`<polyline points="${cx - 8},${cy - 40} ${cx},${cy - 54} ${cx + 8},${cy - 40}" fill="#fff" stroke="${TINTA}" stroke-width="1.4"/>`);
  c.crudo(`<ellipse cx="${cx - 36}" cy="${cy}" rx="5" ry="10" fill="#fff" stroke="${TINTA}" stroke-width="1.2"/>`);
  c.crudo(`<ellipse cx="${cx + 36}" cy="${cy}" rx="5" ry="10" fill="#fff" stroke="${TINTA}" stroke-width="1.2"/>`);
  c.t(cx - 14, cy + 4, 'I', 9, TINTA, 'middle', 700);
  c.t(cx + 14, cy + 4, 'D', 9, TINTA, 'middle', 700);
  c.t(cx, cy - 60, 'nariz', 7.5, TENUE);
  // el plano RALP: anterior derecho adelante a la derecha, posterior izquierdo atrás a la izquierda
  c.l(cx - 52, cy + 62, cx + 52, cy - 62, CABEZA, 2.6);
  c.t(cx + 56, cy - 62, 'RALP', 8, CABEZA, 'start', 700);
  const caja = (x, y, nombre) => {
    const [r, tipo] = canales[nombre];
    const corte = tipo === 'l' ? A.CONFIG.gainNormalMin : A.CONFIG.gainNormalMinVertical;
    const col = r.media >= corte ? OK : AVISO;
    c.rect(x, y, 78, 36, '#fff', col, 1.4, null, 1, 4);
    c.t(x + 39, y + 13, nombre, 7.5, TINTA);
    c.t(x + 39, y + 29, coma(r.media), 10, col, 'middle', 700);
  };
  caja(14, 84, 'anterior izq.'); caja(148, 84, 'anterior der.');
  caja(4, 160, 'lateral izq.'); caja(158, 160, 'lateral der.');
  caja(14, 236, 'posterior izq.'); caja(148, 236, 'posterior der.');
  c.t(14, 300, 'Corte dibujado: 0,80 en el lateral y 0,70', 7.5, TENUE, 'start');
  c.t(14, 312, 'en los verticales.', 7.5, TENUE, 'start');
  // B y C: el plano RALP
  const b = panelLado(c, 300, 92, 180, 140, ra, 'derecha', 'B · Anterior der. (nariz abajo)', { corte: A.CONFIG.gainNormalMinVertical, x1: 450, angosto: true });
  const d = panelLado(c, 530, 92, 180, 140, ra, 'izquierda', 'C · Posterior izq. (nariz arriba)', { corte: A.CONFIG.gainNormalMinVertical, ylab: false, x1: 450, angosto: true });
  c.t(300, 48, 'B y C · Plano RALP: cabeza girada 45° a la izquierda, mirada en el blanco', 8.5, TENUE, 'start');
  c.l(300, 322, 322, 322, CABEZA, 2.4); c.t(328, 325, 'cabeza', 8.5, TINTA, 'start');
  c.l(388, 322, 410, 322, OJO, 2.4); c.t(416, 325, 'ojo (invertido)', 8.5, TINTA, 'start');
  c.triangulo(525, 326, AVISO, 4.2); c.t(535, 325, 'sacada manifiesta', 8.5, TINTA, 'start');
  c.guardar('h18-ralp.svg');
  console.log('  ', Object.fromEntries(Object.entries(canales).map(([k, [r]]) => [k, r.media?.toFixed(2)])), 'B', b.r.media.toFixed(2), 'C', d.r.media.toFixed(2));
}

function rechazos(tr) {
  const der = tr.filter((t) => t.side === 'derecha');
  const buenos = der.filter((t) => !t.rejected);
  const parpadeo = der.find((t) => t.rejected === 'parpadeo');
  const lento = der.find((t) => t.rejected === 'lento');
  const c = new Lienzo(720, 300);
  c.t(14, 18, 'Dos impulsos que el motor no cuenta (en gris, los aceptados del mismo lado)', 10, TINTA, 'start', 700);
  const panel = (px, t, titulo, nota) => {
    const e = new Ejes(c, px, 66, 290, 170, -100, 400, -40, 300);
    c.t(px, 48, titulo, 9.5, TINTA, 'start', 700);
    e.marco([0, 100, 200, 300, 400], [0, 100, 200, 300], 'tiempo desde el inicio del impulso (ms)', '°/s');
    for (const b of buenos) trazaPulso(c, e, b, { op: 0.5, w: 1.1, colCab: '#b9b7b2', colOjo: '#d6d3cc', marcas: false });
    trazaPulso(c, e, t, { w: 2 });
    c.t(px, 280, nota, 8, TINTA, 'start');
    return e;
  };
  const e1 = panel(52, parpadeo, 'A · Rechazado: parpadeo en la ventana', 'El párpado tapó la pupila dentro de la ventana del impulso.');
  const x0 = e1.X(parpadeo.tOnsetMs - parpadeo.tOnsetMs), x1 = e1.X(parpadeo.tOffsetMs - parpadeo.tOnsetMs);
  c.rect(x0, e1.py + 4, x1 - x0, e1.h - 4, 'none', AVISO, 1.4, '4 3');
  c.t(x0 + 2, e1.py + 16, 'ventana del impulso', 7.5, AVISO, 'start', 700);
  for (const p of curvas(parpadeo)) if (p.blink && e1.dentro(p.t)) c.punto(e1.X(p.t), e1.Y(-22), AVISO, 2.6);
  c.t(x1 + 4, e1.Y(-22) + 3, 'cuadros con el ojo cerrado', 7.5, AVISO, 'start');
  const e2 = panel(404, lento, 'B · Rechazado: muy lento', `Pico de ${lento.peakHeadDegS.toFixed(0)} °/s: por debajo del mínimo de ${A.CONFIG.accept.peakMinDegS} °/s.`);
  c.l(e2.X(-100), e2.Y(A.CONFIG.accept.peakMinDegS), e2.X(400), e2.Y(A.CONFIG.accept.peakMinDegS), AVISO, 1.2, '5 3');
  c.t(e2.X(400) - 2, e2.Y(A.CONFIG.accept.peakMinDegS) - 4, 'velocidad mínima', 7.5, AVISO, 'end', 700);
  c.guardar('h18-rechazos.svg');
}

function muestreo() {
  const SIMHIT = resolve(process.env.SIMHIT ?? `${homedir()}/Escritorio/Proyectos/simHit`, 'app/src/lib');
  const fuente = readFileSync(`${SIMHIT}/simulator.svelte.ts`, 'utf8');
  const cte = (n) => Number(fuente.match(new RegExp(`const ${n} = ([0-9.]+)`))[1]);
  const FS = Number(readFileSync(`${SIMHIT}/firmware-constants.ts`, 'utf8').match(/FIRMWARE_SAMPLE_RATE_HZ = (\d+)/)[1]);
  const PICO_T = cte('IMP_PEAK_OFFSET'), SIG = cte('IMP_SIGMA'), SIG_S = cte('SACCADE_SIGMA'), COV = cte('COVERT_OFFSET');
  const RETARDO = Number(fuente.match(/now - (\d+) - center/)[1]);
  const PICO = 200, G = 0.5;
  // t en ms desde el arranque del impulso, como `tick`: cabeza y ojo invertido (positivos).
  const cab = (t) => PICO * Math.exp(-((t - PICO_T) ** 2) / (2 * SIG ** 2));
  const ojo = (t) => G * PICO * Math.exp(-((t - RETARDO - PICO_T) ** 2) / (2 * SIG ** 2))
    + PICO * (1 - G) * 1.2 * Math.exp(-((t - COV) ** 2) / (2 * SIG_S ** 2));
  const c = new Lienzo(720, 320);
  c.t(14, 18, 'Un mismo impulso con sacada encubierta, registrado a dos velocidades de muestreo', 10, TINTA, 'start', 700);
  const panel = (px, fs, fase, titulo, nota) => {
    const e = new Ejes(c, px, 66, 290, 170, 0, 300, 0, 300);
    c.t(px, 48, titulo, 9.5, TINTA, 'start', 700);
    e.marco([0, 100, 200, 300], [0, 100, 200, 300], 'tiempo desde el arranque del impulso (ms)', '°/s');
    const dt = 1000 / fs;
    const ts = [];
    for (let t = fase; t <= 300; t += dt) ts.push(t);
    for (const [f, col] of [[cab, CABEZA], [ojo, OJO]]) {
      c.poli(ts.map((t) => [e.X(t), e.Y(f(t))]), col, 1.8);
      if (fs < 100) for (const t of ts) c.punto(e.X(t), e.Y(f(t)), col, 3);
    }
    c.t(px, 280, nota, 8, TINTA, 'start');
    return e;
  };
  const e1 = panel(52, FS, 0, `A · ${FS} muestras por segundo`, `Una muestra cada ${1000 / FS} ms.`);
  const t0 = COV;
  c.triangulo(e1.X(t0), e1.Y(ojo(t0)) - 4, ENCUBIERTA, 4.2);
  const e2 = panel(404, 30, 12, 'B · 30 cuadros por segundo (cámara web)', 'Un cuadro cada 33 ms.');
  c.l(52, 304, 74, 304, CABEZA, 2.4); c.t(80, 307, 'cabeza', 8.5, TINTA, 'start');
  c.l(140, 304, 162, 304, OJO, 2.4); c.t(168, 307, 'ojo (invertido)', 8.5, TINTA, 'start');
  c.triangulo(275, 308, ENCUBIERTA, 4.2); c.t(285, 307, 'sacada encubierta', 8.5, TINTA, 'start');
  c.guardar('h18-muestreo.svg');
  console.log('  simHit', { FS, PICO_T, SIG, SIG_S, COV, RETARDO });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const tr = impulsos();
  ganancias(tr);
  ralp();
  rechazos(tr);
  muestreo();
}
