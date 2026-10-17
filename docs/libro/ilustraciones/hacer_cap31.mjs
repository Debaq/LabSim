// Datos para las figuras del cap. 31: corre headless el modelo de labyrinthus3d
// (del autor, Apache-2.0; se lee, no se modifica) y escribe JSON por stdout.
// Lo usa hacer_cap31.py. Las constantes del simulador son órdenes de magnitud docentes,
// no valores normativos: las trazas ilustran el principio, no los tiempos de un paciente.
//   LABYRINTHUS3D=<ruta> node hacer_cap31.mjs
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { homedir } from 'node:os';

const RAIZ = process.env.LABYRINTHUS3D || join(homedir(), 'Escritorio/Proyectos/labyrinthus3d');
const imp = (r) => import(pathToFileURL(join(RAIZ, r)).href);
const P = await imp('js/patologia.js');
const Q = await imp('js/postural.js');
const { CASO, funciones } = P;
const { prueba, funcionesPost, vestibularPostural, sesgoVestibular } = Q;

const CONDS = {
  firme_cerrados: { ojos: false, superficie: 'firme', entorno: 'fijo' },
  espuma_cerrados: { ojos: false, superficie: 'espuma', entorno: 'fijo' },
};
const r2 = (x) => Math.round(x * 100) / 100;
const DIAS = [1, 7, 30, 90];
const f = funciones(CASO.perdida_unilateral.canales);
const fp = funcionesPost({});
const out = {};
for (const d of DIAS) {
  const vest = vestibularPostural(f, d);
  const sesgo = sesgoVestibular(vest.asimetria);
  out[d] = { asimetria: r2(vest.asimetria), comp: r2(vest.comp), cd: r2(vest.cd) };
  for (const [id, condicion] of Object.entries(CONDS)) {
    const r = prueba({ fp, vest, condicion, sesgo, segundos: 20, semilla: 3 });
    out[d][id] = { caidas: r.caidas, cayo: r.cayo ? r.cayo.t : null, serie: r.serie.filter((_, k) => k % 5 === 0).map((p) => [r2(p[0]), r2(p[1]), r2(p[2])]) };
  }
}
console.log(JSON.stringify(out));
