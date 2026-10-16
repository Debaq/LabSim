// Datos para las figuras de H15: corre headless el modelo de labyrinthus3d
// (del autor, Apache-2.0; se lee, no se modifica) y escribe JSON por stdout.
// Lo usa hacer_h15.py. Las constantes del simulador son órdenes de magnitud
// docentes, no valores normativos: las trazas ilustran el método.
//   LABYRINTHUS3D=<ruta> node hacer_h15.mjs
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { homedir } from 'node:os';

const RAIZ = process.env.LABYRINTHUS3D || join(homedir(), 'Escritorio/Proyectos/labyrinthus3d');
const imp = (r) => import(pathToFileURL(join(RAIZ, r)).href);
const P = await imp('js/patologia.js');
const E = await imp('js/estimulo.js');
const X = await imp('test/examen.mjs');
const { Ojo, funciones, CASO, efectivas, vestibulares, compensacion, faseLentaEspontanea } = P;
const { direccion, miradaDe, medidasSaltos, medidasSeguimiento, faseLenta } = E;
const ID = [0, 0, 0, 1];
const f1 = (x) => Math.round(x * 100) / 100;

// Un ojo quieto en la órbita (cabeza quieta), mirando a `tramos`: [[grados, segundos], ...],
// con luz (blanco que se mira) o a oscuras (lentes de Frenzel / VNG sin luz).
function mirada(caso, { luz = false, tramos = [[0, 8]], dias = 1 } = {}) {
  const c = CASO[caso];
  const f = funciones(c.canales);
  const fe = efectivas(f);
  const fv = vestibulares(f);
  const comp = compensacion(dias, fe);
  const lenta = faseLentaEspontanea(fe, { compensado: comp, fijacion: luz, frenable: fv });
  const o = new Ojo();
  const dt = 0.004;
  const out = [];
  const alturas = [];
  let t = 0;
  const marcas = [];
  for (const [h, dur] of tramos) {
    marcas.push([t, h]);
    const fin = t + dur;
    for (; t < fin; t += dt) {
      const op = { f: fe, lenta, ...(luz ? { blanco: direccion([h, 0]), vision: 'fija' } : { orbita: direccion([h, 0]), vision: 'oscuras' }) };
      o.paso(dt, ID, [0, 0, 0], op);
      const [mh, mv] = miradaDe(o.q);
      // se guarda cada 20 ms
      if (Math.round(t / dt) % 5 === 0) out.push([f1(t), f1(mh), f1(mv)]);
    }
  }
  // Columna 1: grados, positivo hacia la derecha del paciente.
  return { lenta: lenta.map(f1), muestras: out, marcas: marcas.map(([a, b]) => [f1(a), b]) };
}

const salida = {};
salida.frenzel = mirada('neuritis_superior', { luz: false, tramos: [[0, 8]] });
salida.fijando = mirada('neuritis_superior', { luz: true, tramos: [[0, 8]] });
const seq = [[0, 5], [20, 6], [0, 4], [-20, 6], [0, 4]];
salida.alexander = mirada('neuritis_superior', { luz: false, tramos: seq });
salida.evocado = mirada('integrador', { luz: false, tramos: seq });
salida.sano = mirada('sano', { luz: false, tramos: seq });

// Oculomotor: el examen del simulador, dos ojos, cada 20 ms.
function oculo(estimulo, canales, opc = {}) {
  const r = X.examina(estimulo, funciones(canales), opc);
  const m = r.muestras;
  const sub = m.filter((_, i) => i % 5 === 0).map((x) => [f1(x[0]), f1(x[1]), f1(x[3]), f1(x[5])]);
  return { sub, saltos: medidasSaltos(m, 0), seg: medidasSeguimiento(m, 0) };
}
const dec = (o) => o;
salida.sacadas = {
  sano: oculo({ tipo: 'saltos', amplitud: 20 }, {}, { s: 8 }),
  vermis: oculo({ tipo: 'saltos', amplitud: 20 }, CASO.vermis.canales, { s: 8 }),
  fastigio: oculo({ tipo: 'saltos', amplitud: 20 }, CASO.fastigio.canales, { s: 8 }),
  fef: oculo({ tipo: 'saltos', amplitud: 20 }, CASO.fef_coliculo.canales, { s: 8 }),
};
salida.seguimiento = {
  sano: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, {}, { s: 8 }),
  floculos: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, CASO.floculos.canales, { s: 8 }),
};
const okn = X.examina({ tipo: 'optocinetico', velocidad: 40 }, funciones({}), { s: 14 });
salida.optocinetico = okn.muestras.filter((_, i) => i % 5 === 0).map((x) => [f1(x[0]), f1(x[3]), f1(x[7])]);
console.log(JSON.stringify(salida));
