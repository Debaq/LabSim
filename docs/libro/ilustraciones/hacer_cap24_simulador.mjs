#!/usr/bin/env node
// Figura del cap. 24 hecha con el motor de trainHIT, sin su interfaz:
//
//   cap24-vhit-bilateral.svg  impulsos superpuestos del caso bilateral («C» de los casos a ciegas)
//
// Usa el mismo dibujo y el mismo camino que hacer_h18_simulador.mjs (pulsos sintéticos del caso por
// `procesaCrudo`, como `cargaEjemplos('C')` de la app). trainHIT no se toca. Cifras del modelo, no normas.
//
// Uso:  node docs/libro/ilustraciones/hacer_cap24_simulador.mjs

import { panelesLado, pulsosDe } from './hacer_h18_simulador.mjs';

const r = panelesLado(pulsosDe('C'), 'cap24-vhit-bilateral.svg', 'Los dos canales laterales con ganancia baja', false);
console.log('  der', r.der, 'izq', r.izq, 'asim', r.asim.toFixed(1));
