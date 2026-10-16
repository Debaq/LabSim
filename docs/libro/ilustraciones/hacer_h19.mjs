// Datos para las figuras de H19: corre headless el modelo de labyrinthus3d
// (del autor, Apache-2.0; se lee, no se modifica) y escribe JSON por stdout.
// Lo usa hacer_h19.py. Las constantes del simulador son órdenes de magnitud
// docentes, no valores normativos: las trazas ilustran el método.
//   LABYRINTHUS3D=<ruta> node hacer_h19.mjs
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { homedir } from 'node:os';

const RAIZ = process.env.LABYRINTHUS3D || join(homedir(), 'Escritorio/Proyectos/labyrinthus3d');
const imp = (r) => import(pathToFileURL(join(RAIZ, r)).href);
const P = await imp('js/patologia.js');
const Q = await imp('js/postural.js');
const { CASO, funciones, compensacion, compensacionDinamica, efectivas, RECUPERA_REFLEJO } = P;
const { prueba, funcionesPost, vestibularPostural, sesgoVestibular } = Q;

const CONDS = [
  ['firme_abiertos', { ojos: true, superficie: 'firme', entorno: 'fijo' }],
  ['firme_cerrados', { ojos: false, superficie: 'firme', entorno: 'fijo' }],
  ['espuma_abiertos', { ojos: true, superficie: 'espuma', entorno: 'fijo' }],
  ['espuma_cerrados', { ojos: false, superficie: 'espuma', entorno: 'fijo' }],
];
const r2 = (x) => Math.round(x * 100) / 100;
function sway(caso, dias, semilla) {
  const f = funciones(CASO[caso].canales);
  const vest = vestibularPostural(f, dias);
  const fp = funcionesPost({});
  const sesgo = sesgoVestibular(vest.asimetria);
  const out = {};
  for (const [id, condicion] of CONDS) {
    const r = prueba({ fp, vest, condicion, sesgo, segundos: 20, semilla });
    out[id] = { caidas: r.caidas, cayo: r.cayo ? r.cayo.t : null, serie: r.serie.filter((_, k) => k % 5 === 0).map((p) => [r2(p[0]), r2(p[2])]) };
  }
  return out;
}
const dias = [];
for (let d = 0.25; d <= 120; d *= 1.08) dias.push(d);
const f = funciones(CASO.perdida_unilateral.canales);
const fe = efectivas(f);
console.log(JSON.stringify({
  sano: sway('sano', 90, 3),
  bilateral: sway('arreflexia_bilateral', 90, 3),
  comp: dias.map((d) => [r2(d), r2(compensacion(d, fe)), r2(compensacionDinamica(d, fe)), r2(compensacionDinamica(d, fe) * RECUPERA_REFLEJO)]),
}));
