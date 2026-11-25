# Pacientes de práctica de latencia media y tardía (2026-11-25)

Ocho pacientes con la vía central alterada, para el OSCE de Electrofisiología
y la práctica libre. **No son del libro** (aviso en libro-orl,
`pendientes_urgentes.md`). En producción: casos 167-174 (`ids_produccion.json`),
carpeta de práctica "Latencias media y tardía (práctica, fuera del libro)",
carpeta de casos "Práctica · latencias media y tardía".

Cada `lmt_*.json` es el pedido (cuadro, grado, edad, sexo, semilla, escenario
central de `CaseProfile::CENTRAL_SCENARIOS` y anamnesis), en el formato de
`libro-orl/material/casos`. Se armaron con el armador del libro
(`libro-orl/material/figuras/armar_casos.sh`, copiado fuera del libro para no
escribir ahí), que usa el editor real en una copia aislada del backend.

Ajuste a mano después de armar: `lmt_acv_derecho` salió con
`Central.mlr_hemisferio = izquierdo` (el escenario sortea el lado) y se cargó
con `derecho`, que es lo que dice su historia.

Verificado en el ABR: ACV izq. Na-Pa C3 0,28 vs C4 0,59 µV; ACV der. C4 0,49
vs C3 1,16; P1 a ~250 ms (5 años) y ~200 ms (8 años); P300 ~415 y ~445 ms;
MMN −0,6 y −0,9 µV.
