// Datos de cap27-sot-sano-pppd.svg (cap. 27, mareo que no se va): corre sin pantalla el modelo
// postural de labyrinthus3d (se lee, no se modifica) y escribe JSON por stdout. Lo usa
// hacer_cap27_simulador.py. Hace lo mismo que la posturografía rápida del simulador (las seis
// condiciones, tres intentos cada una, el promedio), con semilla fija para que salga igual siempre.
// Las constantes del modelo son órdenes de magnitud docentes, no valores normativos.
//   LABYRINTHUS3D=<ruta> node hacer_cap27_simulador.mjs
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { homedir } from 'node:os';

const RAIZ = process.env.LABYRINTHUS3D || join(homedir(), 'Escritorio/Proyectos/labyrinthus3d');
const imp = (r) => import(pathToFileURL(join(RAIZ, r)).href);
const { CASO, funciones } = await imp('js/patologia.js');
const Q = await imp('js/postural.js');

const semilla = Number(process.env.SEMILLA || 271);
const out = { normal: Q.SOT_NORMAL, analisis_normal: Q.ANALISIS_NORMAL };
for (const id of ['sano', 'pppd']) {
  const caso = Q.CASO_POST[id];
  const f = funciones(CASO[caso.vestibular].canales);
  const vest = Q.vestibularPostural(f, 90);
  const sesgo = Q.sesgoVestibular(vest.asimetria);
  const fp = Q.funcionesPost(caso.post);
  const hechos = [0, 1, 2].map((k) => Q.posturografia({ fp, vest, sesgo, semilla: semilla + 101 * k }));
  const puntajes = Q.SOT.map((_, i) => Math.round(hechos.reduce((a, x) => a + x.puntajes[i], 0) / hechos.length));
  const caidas = Q.SOT.map((_, i) => hechos.every((x) => x.intentos[i].caidas > 0));
  out[id] = { puntajes, caidas, analisis: Q.analisisSensorial(puntajes), compuesto: Q.compuesto(puntajes) };
}
console.log(JSON.stringify(out));
