// Datos para la figura del cap. 32 (volver a caminar sin miedo): corre headless el modelo
// postural de labyrinthus3d (del autor, Apache-2.0; se lee, no se modifica) y escribe JSON por stdout.
// Lo usa hacer_cap32.py. Las constantes del simulador son órdenes de magnitud docentes,
// no valores normativos: las trazas ilustran el principio, no a un paciente.
//   LABYRINTHUS3D=<ruta> node hacer_cap32.mjs
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { homedir } from 'node:os';

const RAIZ = process.env.LABYRINTHUS3D || join(homedir(), 'Escritorio/Proyectos/labyrinthus3d');
const imp = (r) => import(pathToFileURL(join(RAIZ, r)).href);
const P = await imp('js/patologia.js');
const Q = await imp('js/postural.js');
const { CASO, funciones } = P;
const { prueba, funcionesPost, vestibularPostural, sesgoVestibular } = Q;

const CONDS = [
  ['firme_abiertos', { ojos: true, superficie: 'firme', entorno: 'fijo' }],
  ['firme_cerrados', { ojos: false, superficie: 'firme', entorno: 'fijo' }],
  ['espuma_abiertos', { ojos: true, superficie: 'espuma', entorno: 'fijo' }],
  ['espuma_cerrados', { ojos: false, superficie: 'espuma', entorno: 'fijo' }],
];
const PERFILES = {
  sano: { vest: 'sano', post: {} },
  neuropatia: { vest: 'sano', post: { propio_izq: 'hipofuncion', propio_der: 'hipofuncion' } },
  vest_neuro: { vest: 'hipofuncion_bilateral', post: { propio_izq: 'hipofuncion', propio_der: 'hipofuncion' } },
  multi: { vest: 'hipofuncion_bilateral', post: { propio_izq: 'hipofuncion', propio_der: 'hipofuncion', vision: 'hipofuncion' } },
};
const r2 = (x) => Math.round(x * 100) / 100;
const semilla = Number(process.env.SEMILLA || 3);
const out = {};
for (const [clave, { vest: v, post }] of Object.entries(PERFILES)) {
  const f = funciones(CASO[v].canales);
  const vest = vestibularPostural(f, 90);
  const sesgo = sesgoVestibular(vest.asimetria);
  const fp = funcionesPost(post);
  out[clave] = {};
  for (const [id, condicion] of CONDS) {
    const r = prueba({ fp, vest, condicion, sesgo, segundos: 20, semilla });
    out[clave][id] = { caidas: r.caidas, cayo: r.cayo ? r.cayo.t : null, rms: r2(r.rms[1]),
      serie: r.serie.filter((_, k) => k % 5 === 0).map((p) => [r2(p[0]), r2(p[2])]) };
  }
}
console.log(JSON.stringify(out));
