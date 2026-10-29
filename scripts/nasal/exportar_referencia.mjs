// Genera tests/data/nasal_referencia.json con el código JS REAL de RinoSim.
//
// Es la verdad contra la que tests/test_nasal_equivalencia.py compara el port
// a Python (src/nasal/). Cada registro trae los argumentos de la llamada y lo
// que devolvió el JS; el test de Python repite la llamada y compara.
//
// Uso (desde la raíz de LabSim):
//   node scripts/nasal/exportar_referencia.mjs tests/data/nasal_referencia.json
// RinoSim se busca en $RINOSIM_DIR o en ~/Escritorio/Proyectos/rinosim.
// Si cambia el modelo de RinoSim (js/*.js), se regenera el JSON y se corrige
// el port hasta que la equivalencia vuelva a pasar.
//
// Para no inflar el archivo, las listas largas de números o textos (más de
// 60 elementos) se guardan de a un elemento cada 4, salvo en los registros
// con `completo: true`. El test aplica la misma regla a lo que calcula.

import { writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const RAIZ = process.env.RINOSIM_DIR || join(homedir(), 'Escritorio', 'Proyectos', 'rinosim');
const imp = (f) => import(pathToFileURL(join(RAIZ, 'js', f)).href);
const azar = await imp('azar.js');
const modelo = await imp('modelo.js');
const rm = await imp('rinomanometria.js');
const ra = await imp('rinometria.js');

const ZANCADA = 4;
const LARGO_MIN = 60;

function reduce(v) {
  if (Array.isArray(v)) {
    if (v.length > LARGO_MIN && v.every((e) => typeof e === 'number' || typeof e === 'string')) {
      return v.filter((_, i) => i % ZANCADA === 0);
    }
    return v.map(reduce);
  }
  if (v && typeof v === 'object') return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, reduce(x)]));
  return v;
}

const edita = (p, cambios = []) => {
  for (const [ruta, valor] of cambios) modelo.escribe(p, ruta, valor);
  return p;
};
const hacer = (r) => edita(modelo.paciente(r.cuadro, r.semilla ?? null), r.edita);

const CUADROS = Object.keys(modelo.CUADROS);
const out = {
  _regenerar: 'node scripts/nasal/exportar_referencia.mjs tests/data/nasal_referencia.json',
  _fuente: 'RinoSim (js/*.js), ejecutado con node ' + process.version,
  _tolerancia: 'relativa 1e-9 (con piso absoluto 1e-12); ver tests/test_nasal_equivalencia.py',
  _regla_listas: `listas de números o textos con más de ${LARGO_MIN} elementos: 1 de cada ${ZANCADA}, salvo completo:true`,
  azar_semilla: [],
  azar_secuencia: [],
  paciente: [],
  normaliza: [],
  congestion: [],
  perfil: [],
  piezas: [],
  rm_coeficientes: [],
  rm_red: [],
  rm_fosa: [],
  rm_puros: {},
  rm_mide: [],
  rm_examen: [],
  ra_equipo: [],
  ra_mide: [],
  ra_puros: {},
};

// ── azar ───────────────────────────────────────────────────────────────────
for (const t of ['', 'a', 'normal/1', 'desviacion_derecha/7', 'rm/1/D/reposo/0', 'ñandú/ü', 'emoji 😀', 42, 0, 1.5, 'x'.repeat(300)]) {
  out.azar_semilla.push({ entrada: t, valor: azar.semilla(t) });
}
for (const s of ['a', 'normal/1', 'ra/1/D/vc/40/2', 12345, 0, 'ñandú']) {
  const g = azar.generador(s);
  const uniforme = Array.from({ length: 25 }, () => g.uniforme());
  const normal = Array.from({ length: 25 }, () => g.normal());
  const normal2 = Array.from({ length: 10 }, () => g.normal(5, 2));
  const entre = Array.from({ length: 10 }, () => g.entre(1, 3));
  out.azar_secuencia.push({ semilla: s, uniforme, normal, normal2, entre });
}
{
  // Una secuencia larga: el estado interno no se desvía con las vueltas.
  const g = azar.generador('larga');
  const lista = Array.from({ length: 5000 }, () => g.uniforme());
  out.azar_secuencia.push({ semilla: 'larga', largo: 5000, ultimos: lista.slice(-5), suma: lista.reduce((a, b) => a + b, 0) });
}

// ── modelo ─────────────────────────────────────────────────────────────────
const SEMILLAS = [null, 1, 7, 'abc'];
for (const cuadro of CUADROS) for (const semilla of SEMILLAS) out.paciente.push({ cuadro, semilla, out: modelo.paciente(cuadro, semilla) });
for (const entrada of [
  { lados: { I: { polipos: 1.2 } } },
  { nombre: 'Mío', cuadro: 'mixta', semilla: 4, lados: { D: { valvula: { area: 0.3, colapso: 0.5 } } }, ciclo: { periodo: 90 }, perforacion: { area: 0.2 } },
  {},
]) out.normaliza.push({ entrada, out: modelo.normaliza(entrada) });

const MINUTOS = [0, 10, 37.5, 75, 150, 200];
for (const cuadro of CUADROS) {
  for (const semilla of [null, 3]) {
    const p = modelo.paciente(cuadro, semilla);
    out.congestion.push({
      cuadro, semilla,
      out: Object.fromEntries(modelo.LADOS.map((l) => [l, {
        reposo: MINUTOS.map((minuto) => modelo.congestion(p, l, { minuto })),
        vc: modelo.congestion(p, l, { vc: true, minuto: 40 }),
        sin_estado: modelo.congestion(p, l),
      }])),
    });
    for (const lado of modelo.LADOS) {
      for (const [estado, colapso] of [[{}, 0], [{ minuto: 40 }, 0.3], [{ vc: true }, 0], [{ minuto: 95 }, 0.6]]) {
        out.perfil.push({ cuadro, semilla, lado, estado, colapso, out: reduce(modelo.perfil(p, lado, estado, colapso)) });
      }
    }
  }
}
for (const cuadro of CUADROS) {
  const p = modelo.paciente(cuadro, 2);
  const xs = [0, 0.5, 1.3, 1.55, 2, 3.2, 4.5, 5.9, 7.1, 9, 12];
  out.piezas.push({ cuadro, semilla: 2, xs, cs: [0.05, 0.4, 0.9],
    out: Object.fromEntries(modelo.LADOS.map((l) => [l, xs.map((x) => [0.05, 0.4, 0.9].map((c) => modelo.piezas(p.lados[l], x, c)))])) });
}
out.modelo_constantes = { REJILLA: modelo.REJILLA.length, ultimo: modelo.REJILLA.at(-1), muestra: [1, 2, 3, 77, 199, 480].map((i) => modelo.REJILLA[i]) };

// ── rinomanometría ─────────────────────────────────────────────────────────
for (const cuadro of CUADROS) {
  const p = modelo.paciente(cuadro, 2);
  for (const lado of modelo.LADOS) {
    const f = rm.fosa(p, lado, { minuto: 20 });
    const Ps = [-300, -75, 0, 20, 75, 150, 400, 900];
    out.rm_fosa.push({
      cuadro, semilla: 2, lado, estado: { minuto: 20 }, Ps,
      out: { flujo: Ps.map((P) => rm.flujoFosa(f, P)), resistencia: [75, 150, 300].map((P) => rm.resistenciaFosa(f, P)), A: reduce(f.A), congestion: f.congestion },
    });
    // Coeficientes de tramos, con la válvula colapsando.
    out.rm_coeficientes.push({
      cuadro, semilla: 2, lado, estado: { vc: true }, cortes: [[0, 320], [0, 50], [50, 320], [0, 160], [160, 320]], Ps: [0, -50, 30, 150, 600],
      out: (() => {
        const g = rm.fosa(p, lado, { vc: true });
        return [0, -50, 30, 150, 600].map((P) => [[0, 320], [0, 50], [50, 320], [0, 160], [160, 320]].map(([a, b]) => g.coef(P, a, b)));
      })(),
    });
  }
}
// La red, con todos los errores y con perforación, en varias presiones.
for (const [cuadro, errores] of [
  ['normal', {}], ['normal', { adaptador: true }], ['normal', { boca: true }], ['normal', { adaptador: true, boca: true }],
  ['perforacion', {}], ['perforacion', { adaptador: true }], ['colapso_valvular', {}], ['mixta', { boca: true }],
]) {
  const p = modelo.paciente(cuadro, 5);
  for (const lado of modelo.LADOS) {
    const otro = lado === 'D' ? 'I' : 'D';
    const Ps = [-420, -150, -20, 0, 2, 40, 150, 300, 420, 900];
    const fm = rm.fosa(p, lado, { minuto: 30 });
    const fo = rm.fosa(p, otro, { minuto: 30 });
    out.rm_red.push({ cuadro, semilla: 5, lado, estado: { minuto: 30 }, errores, Ps, out: Ps.map((P) => rm.resuelveRed(fm, fo, P, p.perforacion, errores)) });
  }
}

out.rm_puros = {
  flujo_presion: [[0.04, 5e-4, 150], [0.2, 2e-3, -80], [0.1, 0, 30], [0.1, 0.01, 0], [1e-3, 1e-3, 1e3]]
    .map(([k1, k2, dP]) => ({ k1, k2, dP, flujo: rm.flujo(k1, k2, dP), presion: rm.presion(k1, k2, rm.flujo(k1, k2, dP)), presion_V: rm.presion(k1, k2, dP) })),
  total: [[0.6, 0.3], [0.375, 0.3], [Infinity, 0.25], [0.25, Infinity], [Infinity, Infinity], [null, 0.3], [0.3, null], [0, 0.5]]
    .map(([a, b]) => ({ a, b, out: rm.resistenciaTotal(a, b) })),
  vasoconstrictor: [[0.6, 0.375], [0.6, 0.45], [0.6, 0.59], [0.3, 0.2], [0.6, 0.8], [0.5, 0.3, 0.2], [null, 0.3], [0.6, null]]
    .map(([a, b, ref]) => ({ a, b, ref: ref ?? null, out: ref === undefined ? rm.lecturaVasoconstrictor(a, b) : rm.lecturaVasoconstrictor(a, b, ref) })),
  constantes: { I_COANA: Math.round(rm.X_COANA / modelo.DX), UMBRAL_SIN_CAMBIO: rm.UMBRAL_SIN_CAMBIO },
  curvas: (() => {
    const c = [[0, 0], [10, 50], [50, 160], [100, 260], [150, 330], [250, 420], [300, 480]];
    return {
      curva: c,
      lee_en: [-1, 0, 5, 10, 75, 149.9, 150, 290, 300, 301].map((P) => ({ P, out: rm.leeEn(c, P) })),
      broms: rm.broms(c), broms_300: rm.broms(c, 300), broms_9999: rm.broms(c, 9999),
    };
  })(),
};

// La medición completa. Cada caso: [cuadro, semillaPaciente, lado, estado, opciones, completo]
const CASOS_RM = [];
for (const cuadro of CUADROS) for (const lado of modelo.LADOS) for (const estado of [{ minuto: 0 }, { vc: true }]) {
  CASOS_RM.push([cuadro, null, lado, estado, { semilla: 1 }, cuadro === 'normal' && lado === 'D']);
}
for (const e of ['mascara', 'adaptador', 'boca', 'irregular']) CASOS_RM.push(['normal', 5, 'D', { minuto: 60 }, { semilla: 4, errores: { [e]: true } }, e === 'irregular']);
CASOS_RM.push(
  ['normal', 5, 'I', { minuto: 60 }, { semilla: 4, forzada: true }, true],
  ['colapso_valvular', null, 'D', {}, { semilla: 1 }, true],
  ['colapso_valvular', null, 'D', {}, { semilla: 1, forzada: true }, false],
  ['colapso_valvular', 3, 'I', { vc: true }, { semilla: 1, forzada: true }, false],
  ['polipos', 7, 'I', { minuto: 30 }, { semilla: 'x', ciclos: 5 }, false],
  ['polipos', 7, 'I', { minuto: 30.5 }, { semilla: 'y', ciclos: 3 }, false],
  ['perforacion', null, 'D', {}, { semilla: 1 }, false],
  ['perforacion', null, 'I', {}, { semilla: 1, errores: { adaptador: true } }, false],
  ['perforacion', 2, 'D', { minuto: 90 }, { semilla: 6, errores: { boca: true, irregular: true } }, false],
  ['desviacion_izquierda', 4, 'I', { minuto: 120 }, { semilla: 9, forzada: true, errores: { irregular: true, mascara: true } }, false],
  ['mixta', 3, 'D', {}, { semilla: 2, errores: { mascara: true, adaptador: true } }, false],
  ['cornetes', null, 'D', { minuto: 45 }, { semilla: 11, ciclos: 5 }, false],
  // Una nariz muy amplia: no llega a 150 Pa (aviso) y una obstruida que llega a más.
  ['normal', null, 'D', {}, { semilla: 1 }, false],
);
const AMPLIA = [['lados.D.valvula.area', 1.2], ['lados.D.cornete.mucosa', 0], ['lados.D.narina', 1.5], ['lados.I.valvula.area', 1.2], ['lados.I.cornete.mucosa', 0], ['lados.I.narina', 1.5]];
const OBSTRUIDA = [['lados.D.valvula.area', 0.2], ['lados.D.polipos', 2.5], ['lados.D.desviacion.area', 0.8]];
for (const [cuadro, semilla, lado, estado, opciones, completo] of CASOS_RM) {
  const p = hacer({ cuadro, semilla });
  out.rm_mide.push({ cuadro, semilla, lado, estado, opciones, completo, out: completo ? rm.mideFosa(p, lado, estado, opciones) : reduce(rm.mideFosa(p, lado, estado, opciones)) });
}
for (const [nombre, cambios, lado] of [['amplia', AMPLIA, 'D'], ['obstruida', OBSTRUIDA, 'D']]) {
  const r = { cuadro: 'normal', semilla: null, edita: cambios };
  const p = hacer(r);
  out.rm_mide.push({ ...r, nombre, lado, estado: {}, opciones: { semilla: 1 }, completo: false, out: reduce(rm.mideFosa(p, lado, {}, { semilla: 1 })) });
}
for (const [cuadro, semilla, estado, opciones] of [['mixta', 3, {}, { semilla: 3 }], ['mixta', 3, { vc: true }, { semilla: 3 }], ['normal', null, { minuto: 15 }, { semilla: 2, errores: { irregular: true } }]]) {
  const p = modelo.paciente(cuadro, semilla);
  out.rm_examen.push({ cuadro, semilla, estado, opciones, out: reduce(rm.examen(p, estado, opciones)) });
}

// ── rinometría ─────────────────────────────────────────────────────────────
for (const cuadro of CUADROS) {
  const p = modelo.paciente(cuadro, 2);
  for (const lado of modelo.LADOS) {
    for (const estado of [{}, { minuto: 70 }, { vc: true }]) {
      out.ra_equipo.push({ cuadro, semilla: 2, lado, estado, errores: {}, out: reduce(ra.curvaDelEquipo(p, lado, estado)) });
    }
  }
}
for (const e of ['aprieta', 'fuga', 'respira']) {
  for (const cuadro of ['normal', 'perforacion']) {
    const p = modelo.paciente(cuadro, 2);
    out.ra_equipo.push({ cuadro, semilla: 2, lado: 'D', estado: { minuto: 20 }, errores: { [e]: true }, out: reduce(ra.curvaDelEquipo(p, 'D', { minuto: 20 }, { [e]: true })) });
  }
}
{
  // Un estrechamiento muy cerrado: lo de atrás se aplana.
  const edits = [['lados.D.valvula.area', 0.15]];
  const p = hacer({ cuadro: 'normal', semilla: null, edita: edits });
  out.ra_equipo.push({ cuadro: 'normal', semilla: null, edita: edits, lado: 'D', estado: {}, errores: {}, out: reduce(ra.curvaDelEquipo(p, 'D', {})) });
}
const CASOS_RA = [];
for (const cuadro of CUADROS) for (const lado of modelo.LADOS) for (const estado of [{}, { vc: true }]) CASOS_RA.push([cuadro, null, lado, estado, { semilla: 1 }, cuadro === 'normal' && lado === 'D' && !estado.vc]);
CASOS_RA.push(
  ['mixta', 3, 'D', { minuto: 55 }, { semilla: 'k', registros: 5 }, false],
  ['normal', 5, 'D', {}, { semilla: 5, errores: { fuga: true } }, true],
  ['normal', 5, 'I', {}, { semilla: 5, errores: { respira: true } }, false],
  ['normal', 5, 'D', {}, { semilla: 1, errores: { aprieta: true } }, false],
  ['normal', 5, 'D', { minuto: 12.5 }, { semilla: 8, registros: 1 }, false],
  ['polipos', 3, 'I', {}, { semilla: 9 }, false],
);
for (const [cuadro, semilla, lado, estado, opciones, completo] of CASOS_RA) {
  const p = modelo.paciente(cuadro, semilla);
  const r = ra.mideFosa(p, lado, estado, opciones);
  out.ra_mide.push({ cuadro, semilla, lado, estado, opciones, completo, out: completo ? r : reduce(r) });
}
{
  // Valvula y cornete movidos: MCA1 y MCA2 siguen a la anatomía.
  for (const pos of [1.0, 1.7]) {
    const edita = [['lados.D.valvula.pos', pos]];
    const p = hacer({ cuadro: 'normal', semilla: null, edita });
    out.ra_mide.push({ cuadro: 'normal', semilla: null, edita, lado: 'D', estado: {}, opciones: { semilla: 1 }, completo: false, out: reduce(ra.mideFosa(p, 'D', {}, { semilla: 1 })) });
  }
}
{
  const x = Array.from({ length: 401 }, (_, i) => i * 0.025);
  const llana = x.map(() => 2);
  const dos = x.map((v) => 2 - 1.4 * Math.exp(-0.5 * ((v - 1.5) / 0.3) ** 2) - Math.exp(-0.5 * ((v - 3.5) / 0.4) ** 2));
  const uno = x.map((v) => 2 - 1.4 * Math.exp(-0.5 * ((v - 1.5) / 0.3) ** 2));
  const creciente = x.map((v) => 0.5 + 0.3 * v);
  out.ra_puros = {
    volumen: [[0, 5], [0, 2], [2, 5], [3.3, 3.31], [-1, 20], [7, 9]].map(([a, b]) => ({ a, b, llana: ra.volumen(x, llana, a, b), dos: ra.volumen(x, dos, a, b) })),
    medidas: { dos: ra.medidas(x, dos), uno: ra.medidas(x, uno), creciente: ra.medidas(x, creciente), llana: ra.medidas(x, llana) },
    constantes: { CRITERIO_REPETICION: ra.CRITERIO_REPETICION, AREA_CRITICA: ra.AREA_CRITICA, X_CURVA: ra.X_CURVA },
  };
}

const texto = JSON.stringify(out, (k, v) => (typeof v === 'number' && !Number.isFinite(v) ? String(v) : v), 0);
const destino = process.argv[2];
if (destino) {
  writeFileSync(destino, texto + '\n');
  console.error(`${destino}: ${(texto.length / 1024).toFixed(0)} KB`);
} else {
  process.stdout.write(texto + '\n');
}
