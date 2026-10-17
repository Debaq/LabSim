// Datos para las figuras del cap. 25 (Lo que viene de arriba): corre headless el modelo
// de labyrinthus3d (del autor, Apache-2.0; se lee, no se modifica) y escribe JSON por stdout.
// Lo usa hacer_cap25.py. Las constantes del simulador son órdenes de magnitud docentes,
// no valores normativos: las trazas ilustran el método y la forma de cada hallazgo.
//   LABYRINTHUS3D=<ruta> node hacer_cap25.mjs
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
const f1 = (x) => (x == null ? null : Math.round(x * 100) / 100);

const ASIGNA = Object.assign;
const caso = (...ids) => ASIGNA({}, ...ids.map((i) => CASO[i].canales));
// Floculos a medias (Chiari) y los dos laberintos perdidos (CANVAS)
const FLOCULO_MEDIO = { floculo_izq: 'hipofuncion', floculo_der: 'hipofuncion' };
const CANVAS = ASIGNA({}, FLOCULO_MEDIO, CASO.arreflexia_bilateral.canales);

// Un ojo (el comando conjugado) quieto en la órbita, mirando a `tramos`: [[h, v, segundos], ...],
// con luz (blanco que se mira) o a oscuras (lentes de Frenzel / VNG sin luz). Columnas: t, h, v;
// positivo = derecha y arriba del paciente.
function mirada(canales, { luz = false, tramos = [[0, 0, 8]], dias = 365 } = {}) {
  const f = funciones(canales);
  const fe = efectivas(f);
  const fv = vestibulares(f);
  const comp = compensacion(dias, fe);
  const lenta = faseLentaEspontanea(fe, { compensado: comp, fijacion: luz, frenable: fv });
  const o = new Ojo();
  const dt = 0.004;
  const out = [];
  let t = 0;
  const marcas = [];
  for (const [h, v, dur] of tramos) {
    marcas.push([f1(t), h, v]);
    const fin = t + dur;
    for (; t < fin; t += dt) {
      const op = { f: fe, lenta, ...(luz ? { blanco: direccion([h, v]), vision: 'fija' } : { orbita: direccion([h, v]), vision: 'oscuras' }) };
      o.paso(dt, ID, [0, 0, 0], op);
      const [mh, mv] = miradaDe(o.q);
      if (Math.round(t / dt) % 5 === 0) out.push([f1(t), f1(mh), f1(mv)]);
    }
  }
  return { muestras: out, marcas };
}

// Oculomotor con el examen del simulador, dos ojos, cada 20 ms: t, blanco, der, izq (horizontal).
function oculo(estimulo, canales, opc = {}) {
  const r = X.examina(estimulo, funciones(canales), opc);
  const m = r.muestras;
  const sub = m.filter((_, i) => i % 3 === 0).map((x) => [f1(x[0]), f1(x[1]), f1(x[3]), f1(x[5])]);
  return { sub, saltos: medidasSaltos(m, 0), seg: medidasSeguimiento(m, 0) };
}

const salida = {};
const a = (x) => x; // marca de lectura

// ---- Catálogo de nistagmos centrales (figura 1)
const seq0 = [[0, 0, 6]];
salida.dbn = { sin: mirada(CASO.floculos.canales, { luz: false, tramos: seq0 }), con: mirada(CASO.floculos.canales, { luz: true, tramos: seq0 }) };
salida.ubn = { sin: mirada(CASO.upbeat.canales, { luz: false, tramos: seq0, dias: 0 }), con: mirada(CASO.upbeat.canales, { luz: true, tramos: seq0, dias: 0 }) };
// Mirada excéntrica 25 s a la derecha y vuelta al centro (rebote): cerebelo (flóculos) y fármacos (integrador)
const reb = [[0, 0, 5], [20, 0, 25], [0, 0, 20]];
salida.gen_floculos = mirada(CASO.floculos.canales, { luz: false, tramos: reb });
salida.gen_integrador = mirada(CASO.integrador.canales, { luz: false, tramos: reb });
// Nistagmo periódico alternante: velocidad de la fase lenta cada 5 s, 7 minutos, a oscuras
{
  const f = funciones(CASO.nodulo.canales);
  const r = X.examina({ tipo: 'saltos', amplitud: 0 }, f, { s: 420, ocluido: true, desde: 0 });
  const v = [];
  for (let t = 0; t < 420; t += 5) v.push([t + 2.5, f1(faseLenta(r.muestras, 0, t, t + 5).der)]);
  salida.pan = v;
}
// Pendular de la esclerosis múltiple: 3 s, ojo derecho, horizontal
{
  const r = X.examina({ tipo: 'saltos', amplitud: 0 }, funciones(CASO.em_pendular.canales), { s: 4, ocluido: true, desde: 0 });
  salida.pendular = r.muestras.filter((_, i) => i % 2 === 0).map((x) => [f1(x[0]), f1(x[3]), f1(x[5])]);
}

// ---- Caso 1: CANVAS = flóculos + los dos laberintos perdidos
const sec = [[0, 0, 5], [20, 0, 12], [0, 0, 10], [-20, 0, 12], [0, 0, 8]];
salida.canvas = {
  mirada: mirada(CANVAS, { luz: false, tramos: sec }),
  miradaLuz: mirada(CANVAS, { luz: true, tramos: sec }),
  seguimiento: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, CANVAS, { s: 9 }),
  sacadas: oculo({ tipo: 'saltos', amplitud: 20 }, CANVAS, { s: 8 }),
};
salida.sano = {
  seguimiento: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, {}, { s: 9 }),
  sacadas: oculo({ tipo: 'saltos', amplitud: 20 }, {}, { s: 8 }),
};

// ---- Caso 2: oftalmoplejía internuclear (FLM izquierdo): dos ojos
salida.ino = { sacadas: oculo({ tipo: 'saltos', amplitud: 20 }, CASO.flm.canales, { s: 6 }), okn: oculo({ tipo: 'optocinetico', velocidad: 40 }, CASO.flm.canales, { s: 14 }) };
// ---- Caso 3: Chiari = flóculos a medias; canal vertical y canal horizontal
salida.chiari = {
  primaria: mirada(FLOCULO_MEDIO, { luz: false, tramos: [[0, 0, 6]] }),
  abajo: mirada(FLOCULO_MEDIO, { luz: false, tramos: [[0, -20, 6]] }),
  arriba: mirada(FLOCULO_MEDIO, { luz: false, tramos: [[0, 20, 6]] }),
  lado: mirada(FLOCULO_MEDIO, { luz: false, tramos: [[20, 0, 6]] }),
  fijando: mirada(FLOCULO_MEDIO, { luz: true, tramos: [[0, 0, 6]] }),
  seguimiento: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, FLOCULO_MEDIO, { s: 9 }),
};
// ---- Caso 4: fármacos / alcohol = integrador a medias
salida.farmaco = {
  mirada: mirada(CASO.integrador.canales, { luz: false, tramos: sec }),
  miradaLuz: mirada(CASO.integrador.canales, { luz: true, tramos: sec }),
  seguimiento: oculo({ tipo: 'seno', amplitud: 20, frecuencia: 0.4 }, CASO.integrador.canales, { s: 9 }),
  sacadas: oculo({ tipo: 'saltos', amplitud: 20 }, CASO.integrador.canales, { s: 8 }),
};
console.log(JSON.stringify(salida));
